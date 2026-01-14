from __future__ import annotations

import asyncio
import threading
from _thread import lock
from asyncio import AbstractEventLoop, Event, Lock, Queue, Task
from collections import defaultdict
from typing import final

from pydantic import ValidationError

from .exceptions import AlConfigurationError, AlLoggerError, AlQueueManagerError
from .handlers.base import Handler, Sink
from .models.framework import BackpressurePolicy, QueueConfig
from .record import LogRecord
from .types import JsonConfig, JsonValue


@final
class QueueManager:
    """
    Queue manager for async log dispatching.
    Handles enqueueing from sync contexts (`structlog`) and async worker dispatch.
    """

    _async_lock: Lock = asyncio.Lock()
    _lock: lock = threading.Lock()

    __slots__ = (
        "_config",
        "_queue",
        "_handler_groups",
        "_worker_task",
        "_shutdown_event",
        "_loop",
        "_dropped_count",
    )

    def __init__(self, config: QueueConfig) -> None:
        self._config: QueueConfig = config
        self._queue: Queue[LogRecord | None] | None = None
        self._handler_groups: dict[str, list[Handler]] = defaultdict(list)
        self._worker_task: Task[None] | None = None
        self._shutdown_event: Event | None = None
        self._loop: AbstractEventLoop | None = None
        self._dropped_count: int = 0

    @classmethod
    def from_json(cls, config: JsonConfig | JsonValue) -> QueueManager:
        """
        Creates an instance of this manager from config data native to JSON.

        Raises:
            * `AlConfigurationError`: The provided config is invalid for factory.
        """
        try:
            v_cfg: QueueConfig = QueueConfig.model_validate(obj=config)
            return cls(config=v_cfg)
        except ValidationError as exc:
            raise AlConfigurationError(
                "Could not create queueing manager instance",
                service=cls.__name__,
            ) from exc

    # ---------------------------------------------------------------------------------
    #   Special methods
    # ---------------------------------------------------------------------------------

    def add_sink(self, logger_name: str, sink: Sink) -> None:
        handlers: list[Handler] = self._handler_groups[logger_name]
        for hdlr in handlers:
            hdlr.sink = sink

    def remove_sink(self, logger_name: str) -> None:
        handlers: list[Handler] = self._handler_groups[logger_name]
        for hdlr in handlers:
            hdlr.sink = None

    # ---------------------------------------------------------------------------------
    #   Initialization and exit
    # ---------------------------------------------------------------------------------

    async def start(self) -> None:
        """Initialize queue and start worker."""

        if self._worker_task is not None:
            return

        self._loop = asyncio.get_running_loop()
        self._queue = Queue[LogRecord | None](maxsize=self._config.max_queue_size)
        self._shutdown_event = asyncio.Event()
        self._worker_task = asyncio.create_task(coro=self._worker())

    async def flush(self) -> None:
        if self._queue:
            await self._queue.join()

    async def shutdown(self) -> None:
        """Graceful shutdown with queue drain."""

        if (self._worker_task is None) or (self._queue is None):
            return

        # Finish all unfinished tasks
        await self.flush()

        # Enforce no outside calls can execute `_enqueue_async()`
        assert self._shutdown_event is not None
        self._shutdown_event.set()

        # Signal `_worker()` to stop
        await self._queue.put(item=None)

        try:
            await asyncio.wait_for(
                fut=self._worker_task, timeout=self._config.drain_timeout
            )
        except asyncio.CancelledError:
            pass
        except asyncio.TimeoutError:
            _ = self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass

        # Close all handlers across all loggers
        all_handlers: list[Handler] = [
            handler
            for handlers in self._handler_groups.values()
            for handler in handlers
        ]
        _ = await asyncio.gather(
            *(handler.close() for handler in all_handlers),
            return_exceptions=True,
        )

        self._loop = None
        self._handler_groups.clear()
        self._worker_task = None

    def is_running(self) -> bool:
        if (self._worker_task is None) or (self._queue is None):
            return False
        return True

    # ---------------------------------------------------------------------------------
    #   Handler handling :)
    # ---------------------------------------------------------------------------------

    def register_handler(self, logger_name: str, handler: Handler) -> None:
        """Register handler for specific logger."""

        self._handler_groups[logger_name].append(handler)

    def unregister_handler(self, logger_name: str, handler: Handler) -> None:
        """Unregister handler from logger's group."""

        if logger_name in self._handler_groups:
            try:
                self._handler_groups[logger_name].remove(handler)
            except ValueError:
                pass

    # ---------------------------------------------------------------------------------
    #   Sync pushing onto destination
    # ---------------------------------------------------------------------------------

    def push_sync(self, record: LogRecord) -> None:
        """
        Synchronously emit `LogRecord` to handlers matching logger name.
        Supports hierarchical logger names (e.g., `src.ko-log.manager`).

        Raises:
            * `AlQueueManagerError`:
              Error occured whilst trying to emit log to specified handlers.
        """

        # Ensure `QueueManager` is running
        if self._queue is None or (
            self._shutdown_event and self._shutdown_event.is_set()
        ):
            return

        handlers: list[Handler] = self._handler_groups.get(record.logger_name, [])
        if not handlers:
            handlers = self._find_parent_handlers(logger_name=record.logger_name)
        if not handlers:
            return

        with self._lock:
            try:
                for hdlr in handlers:
                    hdlr.emit_sync(record.event_dict)
            except AlLoggerError as exc:
                raise AlQueueManagerError(
                    "Failed to synchronously emit log message"
                    + f" of logger `{record.logger_name}`"
                    + f" to handlers `[{', '.join([h.__repr__() for h in handlers])}]`",
                    service=self.__class__.__name__,
                ) from exc

    # ---------------------------------------------------------------------------------
    #   Async pushing onto queue
    # ---------------------------------------------------------------------------------

    async def enqueue(self, record: LogRecord) -> None:
        """Internal async enqueue with backpressure handling."""

        if self._queue is None or (
            self._shutdown_event and self._shutdown_event.is_set()
        ):
            return
        try:
            if self._config.backpressure_policy == BackpressurePolicy.DROP:
                self._queue.put_nowait(item=record)
            elif self._config.backpressure_policy == BackpressurePolicy.BLOCK:
                await self._queue.put(item=record)
            elif self._config.backpressure_policy == BackpressurePolicy.DROP_OLDEST:
                try:
                    self._queue.put_nowait(item=record)
                except asyncio.QueueFull:
                    try:
                        _ = self._queue.get_nowait()
                        self._dropped_count += 1
                    except asyncio.QueueEmpty:
                        pass
                    self._queue.put_nowait(item=record)
        except asyncio.QueueFull:
            pass

    async def _worker(self) -> None:
        """
        Background worker consuming queue and dispatching to handlers.
        Runs until sentinel value received.
        """
        # Is existing anyways at runtime and when asserts are disabled
        assert self._queue is not None

        while True:
            record: LogRecord | None = await self._queue.get()
            if record is None:  # Sentinel for shutdown
                self._queue.task_done()
                break

            # Fan-out to all handlers
            try:
                await self._dispatch(record)
            finally:
                self._queue.task_done()

    async def _dispatch(self, record: LogRecord) -> None:
        """
        Asynchronously dispatches (emit) `LogRecord` to handlers matching logger name.
        Supports hierarchical logger names (e.g., `src.ko-log.manager`).

        Raises:
            * `AlQueueManagerError`:
              Error occured whilst trying to emit log to specified handlers.
        """

        # Get handlers of the specific logger
        handlers: list[Handler] = self._handler_groups.get(record.logger_name, [])

        # Support hierarchical loggers
        if not handlers:
            handlers = self._find_parent_handlers(logger_name=record.logger_name)
        if not handlers:
            return

        # Dispatch to matched handlers
        assert isinstance(record.event_dict, dict)
        try:
            _ = await asyncio.gather(
                *(handler.emit_async(record.event_dict.copy()) for handler in handlers),
                return_exceptions=True,
            )
        except AlLoggerError as exc:
            raise AlQueueManagerError(
                "Failed to asynchronously emit log message"
                + f" of logger `{record.logger_name}`"
                + f" to handlers `[{', '.join([h.__repr__() for h in handlers])}]`",
                service=self.__class__.__name__,
            ) from exc

    def _find_parent_handlers(self, logger_name: str) -> list[Handler]:
        """
        Find handlers from parent loggers.
        Example: "src.ko-log.manager" searches "src.ko-log", then "src"
        """

        parts: list[str] = logger_name.split(sep=".")
        # Try each parent level
        for i in range(len(parts) - 1, 0, -1):
            parent_name: str = ".".join(parts[:i])
            if parent_name in self._handler_groups:
                return self._handler_groups[parent_name]

        # Check root logger
        return self._handler_groups.get("root", [])

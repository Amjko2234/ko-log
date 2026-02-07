from __future__ import annotations

import asyncio
import inspect
import os
import sys
import time
from collections.abc import AsyncGenerator, AsyncIterator, Generator, Iterator
from contextlib import asynccontextmanager, contextmanager
from datetime import datetime, timezone
from inspect import Traceback
from pathlib import Path
from types import FrameType, ModuleType
from typing import Self, final, override

from .exceptions import AlLoggerError, AlProcessorError
from .levels import LogLevel
from .manager import QueueManager
from .record import LogRecord
from .types import (
    Context,
    EventDict,
    ExcInfo,
    LogContext,
    Processor,
    WrappedLogger,
)
from .utils import pop_value

# =====================================================================================
#   Base logger
# =====================================================================================


@final
class QueueLoggerWrapper:
    """
    Internal logger that actually logs.
    It is wrapped by `BoundLoggerBase` to serve as the interface for logging.
    """

    name: str

    def __init__(self, name: str, queue_manager: QueueManager):
        self.name = name
        self._queue: QueueManager = queue_manager

    def log(self, event_dict: EventDict) -> None:
        """Internal log method that creates the `LogRecord`."""

        event_dict["name"] = self.name
        event_dict["timestamp"] = datetime.now(tz=timezone.utc)
        record: LogRecord = LogRecord.create(event_dict)
        self._queue.push_sync(record)

    async def async_log(self, event_dict: EventDict) -> None:
        """Internal async log method that creates the `LogRecord`."""

        event_dict["name"] = self.name
        event_dict["timestamp"] = datetime.now(tz=timezone.utc)
        record: LogRecord = LogRecord.create(event_dict)
        await self._queue.enqueue(record)


# =====================================================================================
#   Base bridge
# =====================================================================================


class BoundLoggerBase:
    """Immutable context carrier. This doesn't do any actual logging."""

    _logger: WrappedLogger

    def __init__(
        self,
        logger: WrappedLogger,
        processors: list[Processor],
        context: LogContext,
    ) -> None:
        self._logger = logger
        self._processors: list[Processor] = processors
        self._context: LogContext = context

    @override
    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__}"
            f" (context={self._context!r},"
            f" processors={self._processors!r})>"
        )

    @override
    def __eq__(self, other: object) -> bool:
        if isinstance(other, BoundLoggerBase):
            try:
                return self._context == other._context
            except AttributeError:
                return False
        return False

    @override
    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)

    # ---------------------------------------------------------------------------------
    #   Logging methods
    # ---------------------------------------------------------------------------------

    def debug(self, event: str, /, **context: Context) -> None:
        self._sync_log(event, level=LogLevel.DEBUG, frame_count=2, **context)

    async def adebug(self, event: str, /, **context: Context) -> None:
        await self._async_log(event, level=LogLevel.DEBUG, frame_count=2, **context)

    @contextmanager
    def debug_scope(self, event: str, /, **context: Context) -> Generator[Self]:
        with self._sync_scope(event, level=LogLevel.DEBUG, **context) as logger:
            yield logger

    @asynccontextmanager
    async def adebug_scope(
        self, event: str, /, **context: Context
    ) -> AsyncGenerator[Self]:
        async with self._async_scope(event, level=LogLevel.DEBUG, **context) as logger:
            yield logger

    @contextmanager
    def debug_life(self, scope: str, /, **context: Context) -> Generator[Self]:
        with self._sync_life(scope, level=LogLevel.DEBUG, **context) as logger:
            yield logger

    @asynccontextmanager
    async def adebug_life(
        self, scope: str, /, **context: Context
    ) -> AsyncGenerator[Self]:
        async with self._async_life(scope, level=LogLevel.DEBUG, **context) as logger:
            yield logger

    # ---------------------------------------------------------------------------------

    def info(self, event: str, /, **context: Context) -> None:
        self._sync_log(event, level=LogLevel.INFO, frame_count=2, **context)

    async def ainfo(self, event: str, /, **context: Context) -> None:
        await self._async_log(event, level=LogLevel.INFO, frame_count=2, **context)

    @contextmanager
    def info_scope(self, event: str, /, **context: Context) -> Generator[Self]:
        with self._sync_scope(event, level=LogLevel.INFO, **context) as logger:
            yield logger

    @asynccontextmanager
    async def ainfo_scope(
        self, event: str, /, **context: Context
    ) -> AsyncGenerator[Self]:
        async with self._async_scope(event, level=LogLevel.INFO, **context) as logger:
            yield logger

    @contextmanager
    def info_life(self, scope: str, /, **context: Context) -> Generator[Self]:
        with self._sync_life(scope, level=LogLevel.INFO, **context) as logger:
            yield logger

    @asynccontextmanager
    async def ainfo_life(
        self, scope: str, /, **context: Context
    ) -> AsyncGenerator[Self]:
        async with self._async_life(scope, level=LogLevel.INFO, **context) as logger:
            yield logger

    # ---------------------------------------------------------------------------------

    def warning(self, event: str, /, **context: Context) -> None:
        self._sync_log(event, level=LogLevel.WARNING, frame_count=2, **context)

    async def awarning(self, event: str, /, **context: Context) -> None:
        await self._async_log(event, level=LogLevel.WARNING, frame_count=2, **context)

    @contextmanager
    def warning_scope(self, event: str, /, **context: Context) -> Generator[Self]:
        with self._sync_scope(event, level=LogLevel.WARNING, **context) as logger:
            yield logger

    @asynccontextmanager
    async def awarning_scope(
        self, event: str, /, **context: Context
    ) -> AsyncGenerator[Self]:
        async with self._async_scope(
            event, level=LogLevel.WARNING, **context
        ) as logger:
            yield logger

    @contextmanager
    def warning_life(self, scope: str, /, **context: Context) -> Generator[Self]:
        with self._sync_life(scope, level=LogLevel.WARNING, **context) as logger:
            yield logger

    @asynccontextmanager
    async def awarning_life(
        self, scope: str, /, **context: Context
    ) -> AsyncGenerator[Self]:
        async with self._async_life(scope, level=LogLevel.WARNING, **context) as logger:
            yield logger

    # ---------------------------------------------------------------------------------

    # fmt: off
    warn = warning  # pyright: ignore[reportUnannotatedClassAttribute]
    awarn = awarning  # pyright: ignore[reportUnannotatedClassAttribute]
    warn_scope = warning_scope  # pyright: ignore[reportUnannotatedClassAttribute]
    awarn_scope = awarning_scope  # pyright: ignore[reportUnannotatedClassAttribute]
    warn_life = warning_life  # pyright: ignore[reportUnannotatedClassAttribute]
    awarn_life = awarning_life  # pyright: ignore[reportUnannotatedClassAttribute]
    # fmt: on

    # ---------------------------------------------------------------------------------

    def error(self, event: str, /, **context: Context) -> None:
        self._sync_log(event, level=LogLevel.ERROR, frame_count=2, **context)

    async def aerror(self, event: str, /, **context: Context) -> None:
        await self._async_log(event, level=LogLevel.ERROR, frame_count=2, **context)

    @contextmanager
    def error_scope(self, event: str, /, **context: Context) -> Generator[Self]:
        with self._sync_scope(event, level=LogLevel.ERROR, **context) as logger:
            yield logger

    @asynccontextmanager
    async def aerror_scope(
        self, event: str, /, **context: Context
    ) -> AsyncGenerator[Self]:
        async with self._async_scope(event, level=LogLevel.ERROR, **context) as logger:
            yield logger

    @contextmanager
    def error_life(self, scope: str, /, **context: Context) -> Generator[Self]:
        with self._sync_life(scope, level=LogLevel.ERROR, **context) as logger:
            yield logger

    @asynccontextmanager
    async def aerror_life(
        self, scope: str, /, **context: Context
    ) -> AsyncGenerator[Self]:
        async with self._async_life(scope, level=LogLevel.ERROR, **context) as logger:
            yield logger

    # ---------------------------------------------------------------------------------

    def critical(self, event: str, /, **context: Context) -> None:
        self._sync_log(event, level=LogLevel.CRITICAL, frame_count=2, **context)

    async def acritical(self, event: str, /, **context: Context) -> None:
        await self._async_log(event, level=LogLevel.CRITICAL, frame_count=2, **context)

    @contextmanager
    def critical_scope(self, event: str, /, **context: Context) -> Generator[Self]:
        with self._sync_scope(event, level=LogLevel.CRITICAL, **context) as logger:
            yield logger

    @asynccontextmanager
    async def acritical_scope(
        self, event: str, /, **context: Context
    ) -> AsyncGenerator[Self]:
        async with self._async_scope(
            event, level=LogLevel.CRITICAL, **context
        ) as logger:
            yield logger

    @contextmanager
    def critical_life(self, scope: str, /, **context: Context) -> Generator[Self]:
        with self._sync_life(scope, level=LogLevel.CRITICAL, **context) as logger:
            yield logger

    @asynccontextmanager
    async def acritical_life(
        self, scope: str, /, **context: Context
    ) -> AsyncGenerator[Self]:
        async with self._async_life(
            scope, level=LogLevel.CRITICAL, **context
        ) as logger:
            yield logger

    # ---------------------------------------------------------------------------------

    # fmt: off
    fatal = critical  # pyright: ignore[reportUnannotatedClassAttribute]
    afatal = acritical  # pyright: ignore[reportUnannotatedClassAttribute]
    fatal_scope = critical_scope  # pyright: ignore[reportUnannotatedClassAttribute]
    afatal_scope = acritical_scope  # pyright: ignore[reportUnannotatedClassAttribute]
    fatal_life = critical_life  # pyright: ignore[reportUnannotatedClassAttribute]
    afatal_life = acritical_life  # pyright: ignore[reportUnannotatedClassAttribute]
    # fmt: on

    # ---------------------------------------------------------------------------------
    #   Internal logger helpers
    # ---------------------------------------------------------------------------------

    @contextmanager
    def _sync_scope(self, event: str, level: str, **ctx: Context) -> Iterator[Self]:
        """
        Logs for synchronous scopes.

        Yields:
            `BoundLoggerBase`: The current logger instance.
        """

        self._sync_log(event, level, frame_count=5, **ctx)
        try:
            yield self
        except BaseException as exc:
            ctx["exc_info"] = exc
            self._sync_log(event="Error in a scope", level=level, frame_count=5, **ctx)
            raise

    @asynccontextmanager
    async def _async_scope(
        self, event: str, level: str, **ctx: Context
    ) -> AsyncIterator[Self]:
        """
        Logs for asynchronous scopes.

        Yields:
            `BoundLoggerBase`: The current logger instance.
        """

        await self._async_log(event, level, frame_count=5, **ctx)
        try:
            yield self
        except BaseException as exc:
            ctx["exc_info"] = exc
            await self._async_log(
                event="Error in a scope", level=level, frame_count=5, **ctx
            )
            raise

    @contextmanager
    def _sync_life(
        self, scope: str, level: str, **ctx: Context
    ) -> Generator[Self, None, None]:
        """
        Logs lifecycle entry and exit for synchronous scopes.

        Yields:
            `BoundLoggerBase`: The current logger instance.
        """

        _log_exc: bool = pop_value(ctx, "log_exc", expected_type=bool)

        self._sync_log(event=f"Begin: {scope}", level=level, frame_count=5, **ctx)
        start: float = time.perf_counter()
        try:
            yield self
        except BaseException as exc:
            if _log_exc:
                ctx["exc_info"] = exc
                self._sync_log(
                    event=f"Error in {scope}", level=level, frame_count=5, **ctx
                )
            raise
        finally:
            duration: float = time.perf_counter() - start
            self._sync_log(
                event=f"End ({duration:.2f}): {scope}",
                level=level,
                frame_count=5,
                **ctx,
            )

    @asynccontextmanager
    async def _async_life(
        self, scope: str, level: str, **ctx: Context
    ) -> AsyncGenerator[Self, None]:
        """
        Logs lifecycle entry and exit for asynchronous scopes.

        Yields:
            `BoundLoggerBase`: The current logger instance.
        """

        _log_exc: bool = pop_value(ctx, "log_exc", expected_type=bool)

        await self._async_log(
            event=f"Begin: {scope}", level=level, frame_count=5, **ctx
        )
        start: float = time.perf_counter()
        try:
            yield self
        except BaseException as exc:
            if _log_exc:
                ctx["exc_info"] = exc
                await self._async_log(
                    event=f"Error in {scope}", level=level, frame_count=5, **ctx
                )
            raise
        finally:
            duration: float = time.perf_counter() - start
            await self._async_log(
                event=f"End ({duration:.2f}): {scope}",
                level=level,
                frame_count=5,
                **ctx,
            )

    # ---------------------------------------------------------------------------------
    #   Binding methods
    # ---------------------------------------------------------------------------------

    def bind(self, **new_values: Context) -> Self:
        """Return a new logger with `new_values` added to context."""

        return self.__class__(
            self._logger,
            self._processors,
            self._context.__class__(**self._context, **new_values),
        )

    def unbind(self, *keys: str) -> Self:
        """
        Return a new logger with *keys* removed from context.

        Raises:
            * `KeyError`: If the key is not part of the context.
        """

        bound_logger = self.bind()
        for key in keys:
            del bound_logger._context[key]
        return bound_logger

    def try_unbind(self, *keys: str) -> Self:
        """Like `unbind`, but best effort: missing keys are ignored."""

        bound_logger = self.bind()
        for key in keys:
            _ = bound_logger._context.pop(key, None)
        return bound_logger

    def new(self, **new_values: Context) -> Self:
        """
        Clear context and binds `new_values` using `bind`.

        Only necessary with dict implementations that keep global state like those
        wrapped by `structlog.threadlocal.wrap_dict` when threads are reused.
        """

        self._context.clear()
        return self.bind(**new_values)

    # ---------------------------------------------------------------------------------
    #   Helper methods
    # ---------------------------------------------------------------------------------

    def _sync_log(
        self,
        event: str,
        level: str,
        frame_count: int = 2,
        **ctx: Context,
    ) -> None:
        frame: FrameType = sys._getframe(  # pyright: ignore[reportPrivateUsage]
            frame_count
        )
        event_dict: EventDict = {
            "name": self._logger.name,
            "event": event,
            "level": level,
            "exc_info": self._is_exception(level, **ctx),
            **self._extract_caller_info(frame),
            "context": {**self._context.copy(), **ctx},
        }
        event_dict = self._process_events(event, event_dict=event_dict.copy())
        self._logger.log(event_dict)

    async def _async_log(
        self,
        event: str,
        level: str,
        frame_count: int = 2,
        **ctx: Context,
    ) -> None:
        frame: FrameType = sys._getframe(  # pyright: ignore[reportPrivateUsage]
            frame_count
        )
        caller_info: dict[str, str] = await asyncio.to_thread(
            lambda: self._extract_caller_info(frame)
        )
        event_dict: EventDict = {
            "name": self._logger.name,
            "event": event,
            "level": level,
            "exc_info": self._is_exception(level, **ctx),
            **caller_info,
            "context": {**self._context.copy(), **ctx},
        }
        event_dict = self._process_events(event, event_dict=event_dict.copy())
        await self._logger.async_log(event_dict)

    def _extract_caller_info(self, frame: FrameType) -> dict[str, str]:
        frame_info: Traceback = inspect.getframeinfo(frame)
        module: ModuleType | None = inspect.getmodule(object=frame)

        return {
            "pathname": os.path.abspath(path=frame_info.filename),
            "filename": Path(frame_info.filename).name,
            "lineno": str(frame_info.lineno),
            "funcName": frame_info.function,
            "module": module.__name__ if module else "unknown",
        }

    def _process_events(self, event: str, event_dict: EventDict) -> EventDict:
        event_dict["event"] = event
        for processor in self._processors:
            try:
                event_dict = processor(event_dict)
            except AlProcessorError as exc:
                raise AlLoggerError(
                    "Failed to finish processing the message through top-level processors",
                    service=self.__class__.__name__,
                ) from exc
        return event_dict

    def _is_exception(self, level: str, **kwargs: Context) -> ExcInfo | None:
        if level in ("ERROR", "CRITICAL"):
            return sys.exc_info()
        elif ("exc_info" in kwargs) and (sys.exc_info()[0] is not None):
            return sys.exc_info()
        else:
            return None

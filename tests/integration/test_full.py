# pyright: reportPrivateUsage=false

import asyncio
import tempfile
import threading
import time
from collections.abc import AsyncGenerator
from pathlib import Path
from threading import Thread
from types import CoroutineType
from typing import TypeAlias

import pytest
import pytest_asyncio

from ko_log import BoundLoggerBase, LoggerFactory, LogLevel, QueueManager, Sink
from ko_log.models import (
    BackpressurePolicy,
    HandlerConfig,
    HandlerType,
    LoggerConfig,
    LoggingSystemConfig,
    NullHandlerConfig,
    PlainFileRendererConfig,
    QueueConfig,
    RendererConfig,
    RendererType,
)

_LoggerSinkManagerFactory: TypeAlias = tuple[
    BoundLoggerBase, Sink, QueueManager, LoggerFactory
]


class TestFullSystemIntegration:
    """Integration tests for the complete logging system."""

    @pytest_asyncio.fixture
    async def full_system_with_sink(
        self,
    ) -> AsyncGenerator[_LoggerSinkManagerFactory, None]:
        """Create a complete logging system with a sink."""

        # Setup QueueManager
        queue_config: QueueConfig = QueueConfig(
            max_queue_size=100,
            backpressure_policy=BackpressurePolicy.BLOCK,
            drain_timeout=2.0,
        )
        queue_manager: QueueManager = QueueManager(config=queue_config)
        await queue_manager.start()

        # Create temp file for internal logging
        with tempfile.NamedTemporaryFile(suffix=".log", delete=False) as f:
            temp_path: Path = Path(f.name)

        # Create system config with a logger
        system_config: LoggingSystemConfig = LoggingSystemConfig(
            loggers=[
                LoggerConfig(
                    name="app",
                    level=LogLevel.DEBUG,
                    processors=[],
                    handlers=[
                        HandlerConfig(
                            type=HandlerType.NULL,
                            renderer=RendererConfig(
                                type=RendererType.FILE_PLAIN,
                                params=PlainFileRendererConfig(
                                    fmt="%(event)s",
                                    datefmt="foobar",
                                ),
                            ),
                            processors=[],
                            params=NullHandlerConfig(),
                        ),
                    ],
                    propagate=False,
                    context={"app": "test_app", "env": "testing"},
                )
            ],
            default_level=LogLevel.INFO,
        )

        # Get the logger with `Sink` for testing
        factory: LoggerFactory = LoggerFactory(
            config=system_config, queue_manager=queue_manager, log_path=temp_path
        )
        logger: BoundLoggerBase = factory.get_logger(name="app")
        sink: Sink = Sink()
        queue_manager.add_sink(logger_name="app", sink=sink)

        yield logger, sink, queue_manager, factory

        # Cleanup
        await queue_manager.shutdown()
        if temp_path.exists():
            temp_path.unlink()

    @pytest.mark.asyncio
    async def test_complete_async_logging_flow(
        self, full_system_with_sink: _LoggerSinkManagerFactory
    ) -> None:
        """Test complete async logging flow from logger to sink."""

        logger, sink, _, _ = full_system_with_sink

        # Log asynchronously
        await logger.ainfo("Async test message", user="test_user", action="login")
        await asyncio.sleep(0.1)

        # Check sink captured the output
        assert len(sink.events) > 0

        # The exact format depends on the handler, but we should see the message
        event: str = sink.events[0]
        assert "Async test message" in event or "test_user" in event

    def test_concurrent_sync_logging(
        self, full_system_with_sink: _LoggerSinkManagerFactory
    ) -> None:
        """Test concurrent synchronous logging from multiple threads."""

        logger, _, _, _ = full_system_with_sink

        # Counter for thread safety check
        log_count: list[int] = [0]

        def log_from_thread(thread_id: int) -> None:
            logger.info(f"Thread {thread_id} message", thread_id=thread_id)
            log_count[0] += 1

        # Create and start multiple threads
        threads: list[Thread] = []
        for i in range(10):
            thread: Thread = threading.Thread(target=log_from_thread, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        time.sleep(0.2)

        # All logs should have been processed
        assert log_count[0] == 10

        # Sink should have received events (exact count depends on handler implementation)
        # At minimum, we know no exceptions were raised

    @pytest.mark.asyncio
    async def test_concurrent_async_logging(
        self, full_system_with_sink: _LoggerSinkManagerFactory
    ) -> None:
        """Test concurrent asynchronous logging from multiple tasks."""

        logger, sink, _, _ = full_system_with_sink

        # Create multiple async logging tasks
        tasks: list[CoroutineType[object, object, None]] = []
        for i in range(5):
            task: CoroutineType[object, object, None] = logger.ainfo(
                f"Async task {i} message", task_id=i
            )
            tasks.append(task)

        # Run all concurrently
        _ = await asyncio.gather(*tasks)

        # Wait for queue processing
        await asyncio.sleep(0.2)

        # Sink should have received events
        assert len(sink.events) > 0

    def test_error_logging_with_exception(
        self, full_system_with_sink: _LoggerSinkManagerFactory
    ) -> None:
        """Test logging errors with exception information."""

        logger, sink, _, _ = full_system_with_sink

        try:
            raise ValueError("Test exception for logging")
        except ValueError:
            # Log with exception
            logger.error("Operation failed", additional_info="test")

        # Wait for processing
        time.sleep(0.1)

        # TODO: Should have captured the error log
        # The exact content depends on the handler and processors, but we set no
        # `CallsiteParameter` processor, therefore no errors are passed through the
        # final `stdout` output. See in `tests/functional/test_processors.py` for the
        # error capture with `CallsiteParameter`
        assert len(sink.events) > 0
        event: str = sink.events[0]
        assert "Operation failed" in event

    def test_logger_rebinding_in_chain(
        self, full_system_with_sink: _LoggerSinkManagerFactory
    ) -> None:
        """Test chaining multiple bind operations."""

        logger, _, _, _ = full_system_with_sink

        # Chain multiple binds
        chained_logger: BoundLoggerBase = (
            logger.bind(service="auth").bind(user_id=123).bind(action="authenticate")
        )

        # All context should be present
        assert chained_logger._context["service"] == "auth"
        assert chained_logger._context["user_id"] == 123
        assert chained_logger._context["action"] == "authenticate"
        # Original context should also be there
        assert chained_logger._context["app"] == "test_app"

    @pytest.mark.asyncio
    async def test_mixed_sync_async_logging(
        self, full_system_with_sink: _LoggerSinkManagerFactory
    ) -> None:
        """Test mixing sync and async logging operations."""

        logger, sink, _, _ = full_system_with_sink

        # Mix sync and async logs
        logger.info("Sync message 1")
        await logger.ainfo("Async message 1")
        logger.warning("Sync message 2")
        await logger.awarning("Async message 2")
        await asyncio.sleep(0.2)

        # All messages should have been processed
        # (exact assertion depends on handler implementation)
        assert len(sink.events) > 0

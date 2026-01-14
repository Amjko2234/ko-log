# pyright: reportPrivateUsage=false

import asyncio
import time
from collections.abc import AsyncGenerator
from typing import TypeAlias
from unittest.mock import AsyncMock, Mock

import pytest
import pytest_asyncio

from ko_log import BoundLoggerBase, QueueManager
from ko_log.models import BackpressurePolicy, QueueConfig

_LoggerWithManager: TypeAlias = tuple[BoundLoggerBase, Mock, QueueManager]


class TestBoundLoggerIntegration:
    """Integration tests for `BoundLoggerBase` with real `QueueManager`."""

    @pytest_asyncio.fixture
    async def bound_logger_with_sink(self) -> AsyncGenerator[_LoggerWithManager, None]:
        """
        Create a `BoundLogger` with a "sink" (mock object) for capturing output.
        """

        # Setup QueueManager
        queue_config: QueueConfig = QueueConfig(
            max_queue_size=100,
            backpressure_policy=BackpressurePolicy.BLOCK,
            drain_timeout=2.0,
        )
        queue_manager: QueueManager = QueueManager(config=queue_config)
        await queue_manager.start()

        # Create a mock wrapped logger
        wrapped_logger: Mock = Mock()
        wrapped_logger.name = "test_integration_logger"
        wrapped_logger.log = Mock()
        wrapped_logger.async_log = AsyncMock()

        # Create BoundLogger with empty processors and context
        logger: BoundLoggerBase = BoundLoggerBase(
            logger=wrapped_logger, processors=[], context={}
        )

        yield logger, wrapped_logger, queue_manager

        await queue_manager.shutdown()

    def test_sync_log_methods(self, bound_logger_with_sink: _LoggerWithManager) -> None:
        """Test synchronous logging methods."""

        logger, wrapped_logger, _ = bound_logger_with_sink

        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
        logger.critical("Critical message")

        # Verify log was called for each
        assert wrapped_logger.log.call_count == 5  # pyright: ignore[reportAny]

        # Check the event dicts
        calls = wrapped_logger.log.call_args_list  # pyright: ignore[reportAny]
        assert calls[0][0][0]["event"] == "Debug message"
        assert calls[0][0][0]["level"] == "DEBUG"

        assert calls[1][0][0]["event"] == "Info message"
        assert calls[1][0][0]["level"] == "INFO"

        assert calls[4][0][0]["event"] == "Critical message"
        assert calls[4][0][0]["level"] == "CRITICAL"

    @pytest.mark.asyncio
    async def test_async_log_methods(
        self, bound_logger_with_sink: _LoggerWithManager
    ) -> None:
        """Test asynchronous logging methods."""

        logger, wrapped_logger, _ = bound_logger_with_sink

        await logger.adebug("Async debug")
        await logger.ainfo("Async info")
        await logger.awarning("Async warning")
        await logger.aerror("Async error")
        await logger.acritical("Async critical")

        # Verify async_log was called for each
        assert wrapped_logger.async_log.call_count == 5  # pyright: ignore[reportAny]

        # Check the event dicts
        calls = wrapped_logger.async_log.call_args_list  # pyright: ignore[reportAny]
        assert calls[0][0][0]["event"] == "Async debug"
        assert calls[0][0][0]["level"] == "DEBUG"

    def test_logger_binding_new_context(
        self, bound_logger_with_sink: _LoggerWithManager
    ) -> None:
        """Test binding new context values to logger."""

        logger, _, _ = bound_logger_with_sink

        new_logger: BoundLoggerBase = logger.bind(user_id=123, action="login")

        # Verify new logger has the context
        assert new_logger._context["user_id"] == 123
        assert new_logger._context["action"] == "login"

        # Original logger should not be affected
        assert "user_id" not in logger._context

    def test_logger_unbinding_context(
        self, bound_logger_with_sink: _LoggerWithManager
    ) -> None:
        """Test unbinding context values from logger."""

        logger, _, _ = bound_logger_with_sink

        bound_logger: BoundLoggerBase = logger.bind(a=1, b=2, c=3)

        # Unbind one key
        unbound_logger: BoundLoggerBase = bound_logger.unbind("b")

        # Verify b was removed
        assert "b" not in unbound_logger._context
        assert unbound_logger._context["a"] == 1
        assert unbound_logger._context["c"] == 3

    def test_logger_try_unbind_ignores_missing_keys(
        self, bound_logger_with_sink: _LoggerWithManager
    ) -> None:
        """Test `try_unbind` doesn't raise for missing keys."""

        logger, _, _ = bound_logger_with_sink

        bound_logger: BoundLoggerBase = logger.bind(x=10, y=20)

        # Try to unbind existing and non-existing keys
        unbound_logger: BoundLoggerBase = bound_logger.try_unbind("x", "z", "y")

        # All keys should be gone (x, y) and z ignored
        assert "x" not in unbound_logger._context
        assert "y" not in unbound_logger._context

    def test_logger_new_clears_context(
        self, bound_logger_with_sink: _LoggerWithManager
    ) -> None:
        """Test `new()` method clears context and binds new values."""

        logger, _, _ = bound_logger_with_sink

        bound_logger: BoundLoggerBase = logger.bind(old_key="old_value")

        new_logger: BoundLoggerBase = bound_logger.new(app="new_app", env="test")

        # Verify old context is gone
        assert "old_key" not in new_logger._context

        # Verify new context is present
        assert new_logger._context["app"] == "new_app"
        assert new_logger._context["env"] == "test"

    def test_logger_context_merging_in_log_calls(
        self, bound_logger_with_sink: _LoggerWithManager
    ) -> None:
        """Test that log calls merge logger context with call-specific context."""

        logger, wrapped_logger, _ = bound_logger_with_sink

        bound_logger: BoundLoggerBase = logger.bind(app="myapp", version="1.0")

        bound_logger.info("User action", user_id=456, action="click")

        # Verify the merged context
        call_args = wrapped_logger.log.call_args[0][0]  # pyright: ignore[reportAny]
        context = call_args["context"]  # pyright: ignore[reportAny]

        assert context["app"] == "myapp"
        assert context["version"] == "1.0"
        assert context["user_id"] == 456
        assert context["action"] == "click"

    def test_sync_scope_context_manager(
        self, bound_logger_with_sink: _LoggerWithManager
    ) -> None:
        """Test synchronous scope context manager."""

        logger, wrapped_logger, _ = bound_logger_with_sink

        # Use debug_scope
        with logger.debug_scope("Processing data", batch_id=123) as scoped_logger:
            # Should be the same logger instance
            assert scoped_logger is logger

            # Log inside scope
            scoped_logger.info("Inside scope")

        # Should have logged twice: scope entry and inside scope
        assert wrapped_logger.log.call_count == 2  # pyright: ignore[reportAny]

        # First call should be the scope entry
        assert wrapped_logger.log.call_args_list[0][0][0]["event"] == "Processing data"  # pyright: ignore[reportAny]
        assert wrapped_logger.log.call_args_list[0][0][0]["context"]["batch_id"] == 123  # pyright: ignore[reportAny]

    @pytest.mark.asyncio
    async def test_async_scope_context_manager(
        self, bound_logger_with_sink: _LoggerWithManager
    ) -> None:
        """Test asynchronous scope context manager."""

        logger, wrapped_logger, _ = bound_logger_with_sink

        # Use async scope
        async with logger.ainfo_scope("Async operation", task_id=789) as scoped_logger:
            assert scoped_logger is logger
            await scoped_logger.ainfo("Inside async scope")

        # Should have logged twice
        assert wrapped_logger.async_log.call_count == 2  # pyright: ignore[reportAny]

        # First call should be scope entry
        assert (
            wrapped_logger.async_log.call_args_list[0][0][0]["event"]  # pyright: ignore[reportAny]
            == "Async operation"
        )
        assert (
            wrapped_logger.async_log.call_args_list[0][0][0]["context"]["task_id"]  # pyright: ignore[reportAny]
            == 789
        )

    def test_sync_lifecycle_context_manager(
        self, bound_logger_with_sink: _LoggerWithManager
    ) -> None:
        """Test synchronous lifecycle context manager."""

        logger, wrapped_logger, _ = bound_logger_with_sink

        # Use lifecycle context manager
        with logger.info_life("Data processing", dataset="test.csv") as life_logger:
            assert life_logger is logger
            # Simulate some work
            time.sleep(0.01)

        # Should have logged: begin, end (with duration)
        assert wrapped_logger.log.call_count == 2  # pyright: ignore[reportAny]

        # First call should be "Begin: ..."
        first_call = wrapped_logger.log.call_args_list[0][0][0]  # pyright: ignore[reportAny]
        assert first_call["event"].startswith("Begin: Data processing")  # pyright: ignore[reportAny]

        # Second call should be "End (...): ..."
        second_call = wrapped_logger.log.call_args_list[1][0][0]  # pyright: ignore[reportAny]
        assert second_call["event"].startswith("End (")  # pyright: ignore[reportAny]
        assert "Data processing" in second_call["event"]

    def test_sync_lifecycle_with_exception(
        self, bound_logger_with_sink: _LoggerWithManager
    ) -> None:
        """Test lifecycle context manager logs exception."""

        logger, wrapped_logger, _ = bound_logger_with_sink

        try:
            with logger.error_life("Failing operation"):
                raise ValueError("Simulated error")
        except ValueError:
            pass

        # Should have logged: begin, error, end
        assert wrapped_logger.log.call_count == 3  # pyright: ignore[reportAny]

        # Second call should be the error
        error_call = wrapped_logger.log.call_args_list[1][0][0]  # pyright: ignore[reportAny]
        assert "Error in Failing operation" in error_call["event"]
        assert "exc_info" in error_call

    @pytest.mark.asyncio
    async def test_async_lifecycle_context_manager(
        self, bound_logger_with_sink: _LoggerWithManager
    ) -> None:
        """Test asynchronous lifecycle context manager."""

        logger, wrapped_logger, _ = bound_logger_with_sink

        async with logger.awarning_life("Async processing") as life_logger:
            assert life_logger is logger
            await asyncio.sleep(0.01)

        # Should have logged begin and end
        assert wrapped_logger.async_log.call_count == 2  # pyright: ignore[reportAny]

        # End should include duration
        end_call = wrapped_logger.async_log.call_args_list[1][0][0]  # pyright: ignore[reportAny]
        assert "End (" in end_call["event"]

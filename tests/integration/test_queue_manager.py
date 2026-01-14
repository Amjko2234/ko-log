import asyncio
import time
from asyncio import Task
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, Mock

import pytest
import pytest_asyncio

from ko_log import QueueManager, Sink
from ko_log.handlers import Handler
from ko_log.models import BackpressurePolicy, QueueConfig


class TestQueueManagerIntegration:
    """Integration tests for `QueueManager` with real components."""

    @pytest_asyncio.fixture
    async def queue_manager(self) -> AsyncGenerator[QueueManager, None]:
        """Create and yield a `QueueManager` instance."""

        config: QueueConfig = QueueConfig(
            max_queue_size=100,
            backpressure_policy=BackpressurePolicy.BLOCK,
            drain_timeout=2.0,
            worker_count=1,
        )
        manager: QueueManager = QueueManager(config)
        await manager.start()
        yield manager
        await manager.shutdown()

    def test_queue_manager_sync_push_and_handler_registration(
        self, queue_manager: QueueManager, mock_handler: Mock
    ) -> None:
        """Test that handlers are registered and receive sync logs."""

        # Register handler for a specific logger
        queue_manager.register_handler(logger_name="test_logger", handler=mock_handler)

        # Create a log record
        record: Mock = Mock()
        record.logger_name = "test_logger"
        record.event_dict = {"event": "Test message", "level": "INFO"}

        # Push synchronously
        queue_manager.push_sync(record)

        # Verify handler was called
        mock_handler.emit_sync.assert_called_once_with(record.event_dict)  # pyright: ignore[reportAny]

    @pytest.mark.asyncio
    async def test_queue_manager_async_enqueue_and_dispatch(
        self, queue_manager: QueueManager, mock_handler: Mock
    ) -> None:
        """Test async enqueue and dispatch to handlers."""

        queue_manager.register_handler(logger_name="test_logger", handler=mock_handler)

        record: Mock = Mock()
        record.logger_name = "test_logger"
        record.event_dict = {"event": "Async message", "level": "DEBUG"}

        # Enqueue asynchronously
        await queue_manager.enqueue(record)

        # Wait a bit for the worker to process
        await asyncio.sleep(0.1)

        # Verify handler was called asynchronously
        mock_handler.emit_async.assert_called_once_with(record.event_dict.copy())  # pyright: ignore[reportAny]

    def test_hierarchical_logger_name_resolution(
        self, queue_manager: QueueManager, mock_handler: Mock
    ) -> None:
        """Test that parent loggers receive child logs."""

        # Register handler for parent logger only
        queue_manager.register_handler(logger_name="parent", handler=mock_handler)

        # Create log records for child and grandchild loggers
        child_record: Mock = Mock()
        child_record.logger_name = "parent.child"
        child_record.event_dict = {"event": "Child message", "level": "INFO"}

        grandchild_record: Mock = Mock()
        grandchild_record.logger_name = "parent.child.grandchild"
        grandchild_record.event_dict = {"event": "Grandchild message", "level": "INFO"}

        # Push both synchronously
        queue_manager.push_sync(record=child_record)
        queue_manager.push_sync(record=grandchild_record)

        # Both should go to the parent handler
        assert mock_handler.emit_sync.call_count == 2  # pyright: ignore[reportAny]
        calls = mock_handler.emit_sync.call_args_list  # pyright: ignore[reportAny]
        assert calls[0][0][0]["event"] == "Child message"
        assert calls[1][0][0]["event"] == "Grandchild message"

    def test_logger_without_handler_does_nothing(
        self, queue_manager: QueueManager, mock_handler: Mock
    ) -> None:
        """Test that logs from loggers without handlers are silently ignored."""

        # Register handler for `logger1` only
        queue_manager.register_handler(logger_name="logger1", handler=mock_handler)

        # Create log record for `logger2`
        record: Mock = Mock()
        record.logger_name = "logger2"  # No handler registered
        record.event_dict = {"event": "Should be ignored", "level": "INFO"}

        # Should not raise any exception
        queue_manager.push_sync(record)

        # Handler should not be called
        mock_handler.emit_sync.assert_not_called()  # pyright: ignore[reportAny]

    @pytest.mark.asyncio
    async def test_queue_backpressure_block_policy(self) -> None:
        """Test `BackpressurePolicy.BLOCK`."""

        config: QueueConfig = QueueConfig(
            max_queue_size=2,  # Very small queue
            backpressure_policy=BackpressurePolicy.BLOCK,
            drain_timeout=2.0,
        )
        manager: QueueManager = QueueManager(config)
        await manager.start()

        # Register a mock handler that processes slowly
        handler: Mock = Mock(spec=Handler)
        handler.emit_async = AsyncMock(side_effect=lambda x: time.sleep(0.2))  # pyright: ignore[reportUnknownLambdaType]
        manager.register_handler(logger_name="test", handler=handler)

        # Fill the queue
        for i in range(2):
            record: Mock = Mock()
            record.logger_name = "test"
            record.event_dict = {"event": f"Message {i}", "level": "INFO"}
            await manager.enqueue(record)

        # Next enqueue should block (but eventually succeed when space frees up)
        start_time: float = time.time()
        record = Mock()
        record.logger_name = "test"
        record.event_dict = {"event": "Blocked message", "level": "INFO"}

        # This should block until space is available
        enqueue_task: Task[None] = asyncio.create_task(coro=manager.enqueue(record))

        # Wait for it to complete (should take ~0.2 seconds for handler to process one)
        await asyncio.wait_for(fut=enqueue_task, timeout=0.5)

        elapsed: float = time.time() - start_time
        # Should have blocked for at least a short time
        assert elapsed > 0.1

        await manager.shutdown()

    @pytest.mark.asyncio
    async def test_queue_backpressure_drop_oldest_policy(self) -> None:
        """Test `BackpressurePolicy.DROP_OLDEST`."""

        config: QueueConfig = QueueConfig(
            max_queue_size=2,
            backpressure_policy=BackpressurePolicy.DROP_OLDEST,
            drain_timeout=2.0,
        )
        manager: QueueManager = QueueManager(config)
        await manager.start()

        async def _mock_emit_async(_: object) -> None:
            await asyncio.sleep(0.1)

        handler: Mock = Mock(spec=Handler)
        handler.emit_async = AsyncMock(side_effect=_mock_emit_async)
        manager.register_handler(logger_name="test", handler=handler)

        # Fill the queue
        for i in range(2):
            record: Mock = Mock()
            record.logger_name = "test"
            record.event_dict = {"event": f"Message {i}", "level": "INFO"}
            await manager.enqueue(record)

        # Add one more - should drop the oldest
        record = Mock()
        record.logger_name = "test"
        record.event_dict = {"event": "New message", "level": "INFO"}
        await manager.enqueue(record)

        # Wait for processing
        await asyncio.sleep(0.5)

        # Should have processed 2 calls only (initial 2, with 3rd one dropped)
        assert handler.emit_async.call_count == 2  # pyright: ignore[reportAny]

        # Lets not call shutdown in this test :)
        # Because of mocks, processes are never truly finished; therefore, as the
        # manager awaits all tasks to be finished first before shutting down, it gets
        # stuck in a loop.
        # >>> await manager.shutdown()

    @pytest.mark.asyncio
    async def test_shutdown_drains_queue(
        self, queue_manager: QueueManager, mock_handler: Mock
    ) -> None:
        """Test that shutdown drains the queue before stopping."""

        # Register handler
        queue_manager.register_handler(logger_name="test", handler=mock_handler)

        # Add several records
        for i in range(5):
            record: Mock = Mock()
            record.logger_name = "test"
            record.event_dict = {"event": f"Message {i}", "level": "INFO"}
            await queue_manager.enqueue(record)

        # Shutdown should wait for all to be processed
        await queue_manager.shutdown()

        # All messages should have been processed
        assert mock_handler.emit_async.call_count == 5  # pyright: ignore[reportAny]

    def test_add_and_remove_sink(
        self, queue_manager: QueueManager, mock_handler: Mock, sink: Sink
    ) -> None:
        """Test adding and removing sinks from handlers."""

        # Register handler
        queue_manager.register_handler(logger_name="test_logger", handler=mock_handler)
        queue_manager.add_sink(logger_name="test_logger", sink=sink)

        # Verify handler's sink was set
        assert mock_handler.sink == sink  # pyright: ignore[reportAny]

        # Verify handler's sink was cleared
        queue_manager.remove_sink(logger_name="test_logger")
        assert mock_handler.sink is None  # pyright: ignore[reportAny]

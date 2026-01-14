# pyright: reportPrivateUsage=false

import asyncio
import sys
import threading
from threading import Thread
from types import CoroutineType
from typing import TextIO
from unittest.mock import AsyncMock, Mock, patch

import pytest

from ko_log import Sink
from ko_log.handlers import AsyncStreamHandler, Handler

from .._helpers import create_test_messages


def test_init(stream_handler: Handler) -> None:
    """Test attributes are set based from configuration, upon initialization."""

    assert isinstance(stream_handler, AsyncStreamHandler)
    assert stream_handler._use_stderr is False


def test_init_with_stderr(stream_handler_to_stderr: Handler) -> None:
    """Test initialization with `use_stderr` parameter."""

    assert isinstance(stream_handler_to_stderr, AsyncStreamHandler)
    stream_handler: AsyncStreamHandler = stream_handler_to_stderr
    assert stream_handler._use_stderr is True


def test_locks_init(stream_handler: AsyncStreamHandler) -> None:
    """Test that both async and sync locks are initialized."""

    assert hasattr(stream_handler, "_lock_async")
    assert hasattr(stream_handler, "_lock_sync")
    assert isinstance(stream_handler._lock_async, asyncio.Lock)
    assert isinstance(stream_handler._lock_sync, threading.Lock)


def test_write_sync_to_sink(stream_handler_to_sink: Handler) -> None:
    """Test synchronous write with `Sink` attached."""

    assert isinstance(stream_handler_to_sink, AsyncStreamHandler)
    stream_handler: AsyncStreamHandler = stream_handler_to_sink
    test_message: str = "Test sync message to sink"

    original_sink: Sink | None = stream_handler.sink
    assert original_sink

    stream_handler._write_sync(test_message)

    # Verify message was written to `Sink`
    assert len(original_sink.events) == 1
    assert original_sink.events[0] == test_message


def test_write_sync(stream_handler: AsyncStreamHandler) -> None:
    """Test synchronous write to `sys.stdout`."""

    test_message: str = "Test sync message to stdout"

    with (
        patch.object(sys.stdout, "write") as mock_write,
        patch.object(sys.stdout, "flush") as mock_flush,
    ):
        stream_handler._write_sync(test_message)

        mock_write.assert_called_once_with(test_message)
        mock_flush.assert_called_once


def test_write_sync_to_stderr(stream_handler_to_stderr: AsyncStreamHandler) -> None:
    """Test synchronous write to `sys.stderr`."""

    stream_handler: AsyncStreamHandler = stream_handler_to_stderr
    test_message: str = "Test sync message to stderr"

    with (
        patch.object(sys.stderr, "write") as mock_write,
        patch.object(sys.stderr, "flush") as mock_flush,
    ):
        stream_handler._write_sync(test_message)

        mock_write.assert_called_once_with(test_message)
        mock_flush.assert_called_once


@pytest.mark.asyncio
async def test_write_async_to_sink(stream_handler_to_sink: AsyncStreamHandler) -> None:
    """Test asynchronous write with `Sink` attached."""

    stream_handler: AsyncStreamHandler = stream_handler_to_sink
    test_message: str = "Test async message to sink"

    original_sink: Sink | None = stream_handler.sink
    assert original_sink

    await stream_handler._write_async(test_message)

    # Verify message was written to `Sink`
    assert len(original_sink.events) == 1
    assert original_sink.events[0] == test_message


@pytest.mark.asyncio
async def test_write_async(stream_handler: AsyncStreamHandler) -> None:
    """Test asynchronous write to `sys.stdout`."""

    test_message: str = "Test sync message to stdout"

    with patch("asyncio.to_thread", new_callable=AsyncMock) as mock_to_thread:
        await stream_handler._write_async(test_message)

        # Verify `asyncio.to_thread` was called
        mock_to_thread.assert_called_once()

        args: list[object] = mock_to_thread.call_args[0]  # pyright: ignore[reportAny]
        assert args[0] == stream_handler._write_flush
        assert args[1] == sys.stdout
        assert args[2] == test_message


@pytest.mark.asyncio
async def test_write_async_to_stderr(
    stream_handler_to_stderr: AsyncStreamHandler,
) -> None:
    """Test asynchronous write to `sys.stderr`."""

    stream_handler: AsyncStreamHandler = stream_handler_to_stderr
    test_message: str = "Test sync message to stderr"

    with patch("asyncio.to_thread", new_callable=AsyncMock) as mock_to_thread:
        await stream_handler._write_async(test_message)

        # Verify `asyncio.to_thread` was called with `stderr`
        mock_to_thread.assert_called_once()

        args: list[object] = mock_to_thread.call_args[0]  # pyright: ignore[reportAny]
        assert args[0] == stream_handler._write_flush
        assert args[1] == sys.stderr
        assert args[2] == test_message


def test_write_flush_method(stream_handler: AsyncStreamHandler) -> None:
    """Test the `_write_flush()` helper method."""

    test_message: str = "Test write flush"
    mock_stream: Mock = Mock(spec=TextIO)

    stream_handler._write_flush(stream=mock_stream, msg=test_message)

    # Verify write and flush were called
    mock_stream.write.assert_called_once_with(test_message)  # pyright: ignore[reportAny]
    mock_stream.flush.assert_called_once()  # pyright: ignore[reportAny]


def test_write_flush_with_sink(stream_handler: AsyncStreamHandler) -> None:
    """Test `_write_flush()` with a `Sink` object."""

    test_message: str = "Test write flush with sink"
    sink: Sink = Sink()

    stream_handler._write_flush(stream=sink, msg=test_message)

    # Verify message was added to `Sink.events`
    assert len(sink.events) == 1
    assert sink.events[0] == test_message


@pytest.mark.asyncio
async def test_flush_method(stream_handler: AsyncStreamHandler) -> None:
    """Test that flush method does nothing (no-op)."""

    await stream_handler.flush()

    # Verify it's no-op by calling it multiple times
    _ = await asyncio.gather(
        stream_handler.flush(),
        stream_handler.flush(),
        stream_handler.flush(),
    )


@pytest.mark.asyncio
async def test_close_method(stream_handler: AsyncStreamHandler) -> None:
    """Test that close method does nothing (no-op)."""

    await stream_handler.close()

    # Verify it's no-op by calling it multiple times
    _ = await asyncio.gather(
        stream_handler.close(),
        stream_handler.close(),
        stream_handler.close(),
    )


def test_concurrent_sync_writes(stream_handler: AsyncStreamHandler) -> None:
    """Test that synchronous writes are thread-safe."""

    test_messages: list[str] = create_test_messages(count=10, msg_length=10)
    write_count: list[int] = [0]

    def mock_write(msg: str) -> None:
        write_count[0] += 1

        with (
            patch.object(sys.stdout, "write", side_effect=mock_write),
            patch.object(sys.stdout, "flush"),
        ):
            threads: list[Thread] = []
            for msg in test_messages:
                thread: Thread = threading.Thread(
                    target=stream_handler._write_sync, args=(msg,)
                )
                threads.append(thread)
                thread.start()

            # Wait for all threads
            for thread in threads:
                thread.join()

            # Verify all messages were written
            assert write_count[0] == len(test_messages)


@pytest.mark.asyncio
async def test_concurrent_async_writes(
    stream_handler_to_sink: AsyncStreamHandler,
) -> None:
    """Test that asynchronous writes are properly serialized with lock."""

    stream_handler: AsyncStreamHandler = stream_handler_to_sink
    test_messages: list[str] = create_test_messages(count=10, msg_length=10)

    sink: Sink | None = stream_handler.sink
    assert sink

    # Create async tasks
    tasks: list[CoroutineType[object, object, None]] = [
        stream_handler._write_async(msg) for msg in test_messages
    ]

    _ = await asyncio.gather(*tasks)

    # Verify all messages were written in order
    assert len(sink.events) == len(test_messages)
    for i, msg in enumerate[str](test_messages):
        assert sink.events[i] == msg

# pyright: reportPrivateUsage=false
import asyncio
import threading
from pathlib import Path
from threading import Thread
from types import CoroutineType
from unittest.mock import Mock, patch

import pytest

from ko_log import Sink
from ko_log import file_handler as _file_handler
from ko_log.exceptions import AlHandlerError
from ko_log.handlers import AsyncFileHandler, Handler
from ko_log.models import HandlerConfig
from ko_log.types import Processor, Renderer

from .._helpers import (
    convert_to_byte,
    create_test_messages,
    read_file_content,
)


def test_init(simple_log_file: Path, file_handler: Handler) -> None:
    """Test attributes are set based from configuration, upon initialization."""

    assert isinstance(file_handler, AsyncFileHandler)
    assert file_handler._filepath == simple_log_file
    assert file_handler._file_async is None
    assert file_handler._file_sync is None
    assert file_handler._encoding == "utf-8"
    assert file_handler._mode == "wb"
    assert file_handler._override is True


def test_init_without_override(
    simple_log_file: Path, file_handler_without_override: Handler
) -> None:
    """Test initialization with `override_existing` parameter."""

    assert isinstance(file_handler_without_override, AsyncFileHandler)
    file_handler: AsyncFileHandler = file_handler_without_override
    assert file_handler._filepath == simple_log_file
    assert file_handler._file_async is None
    assert file_handler._file_sync is None
    assert file_handler._encoding == "utf-8"
    assert file_handler._mode == "wb"
    assert file_handler._override is False


def test_locks_init(file_handler: AsyncFileHandler) -> None:
    """Test that both async and sync locks are initialized."""

    assert hasattr(file_handler, "_lock_async")
    assert hasattr(file_handler, "_lock_sync")
    assert isinstance(file_handler._lock_async, asyncio.Lock)
    assert isinstance(file_handler._lock_sync, threading.Lock)


def test_write_adds_newline(file_handler: AsyncFileHandler) -> None:
    """Test asynchronous or synchronous write adds a newline."""

    test_message: str = "Test message"

    mock_file: Mock = Mock()
    mock_file.write = Mock()
    mock_file.flush = Mock()

    with patch.object(file_handler, "_file_sync", mock_file):
        file_handler._write_sync(test_message)

        # A newline is added during write
        byte_message: bytes = convert_to_byte(test_message + "\n")
        mock_file.write.assert_called_once_with(byte_message)  # pyright: ignore[reportAny]
        mock_file.flush.assert_called_once()  # pyright: ignore[reportAny]


def test_write_sync_with_sink(file_handler_with_sink: Handler) -> None:
    """Test synchronous write with `Sink` attached."""

    test_message: str = "Test sync message with `Sink`"

    assert isinstance(file_handler_with_sink, AsyncFileHandler)
    file_handler: AsyncFileHandler = file_handler_with_sink

    sink: Sink | None = file_handler.sink
    assert sink

    file_handler._write_sync(test_message)

    assert len(sink.events) == 1
    # Message is not encoded into bytes if sink is used
    assert sink.events[0] == test_message + "\n"

    # File shouldn't be open if the sink is used
    assert file_handler._file_async is None
    assert file_handler._file_sync is None


def test_write_opens_lazily(file_handler: AsyncFileHandler) -> None:
    """Test that file is opened on first write."""

    assert file_handler._file_sync is None
    assert file_handler.sink is None
    test_message: str = "Test sync write"

    def _mock_file_handler() -> None:
        mock_file_handler: Mock = Mock()
        mock_file_handler.write = Mock()
        mock_file_handler.flush = Mock()
        setattr(file_handler, "_file_sync", mock_file_handler)

    with patch.object(
        file_handler, "_open_sync", side_effect=_mock_file_handler
    ) as mock_open_sync:
        file_handler._write_sync(test_message)

        # Verify the file was opened
        mock_open_sync.assert_called_once()


def test_write_sync(file_handler: AsyncFileHandler) -> None:
    """Test synchronous write into a temporary log file."""

    test_message: str = "Test log message"

    file_handler._write_sync(test_message)
    assert file_handler._file_async is None
    assert file_handler._file_sync is not None
    file_handler.close_sync()

    assert file_handler._filepath.exists()
    content: str = read_file_content(file_handler._filepath)
    assert test_message + "\n" == content


@pytest.mark.asyncio
async def test_write_async_with_sink(file_handler_with_sink: AsyncFileHandler) -> None:
    """Test asynchronous write with `Sink` attached."""

    file_handler: AsyncFileHandler = file_handler_with_sink
    test_message: str = "Test async message with `Sink`"

    sink: Sink | None = file_handler.sink
    assert sink

    await file_handler._write_async(test_message)

    assert len(sink.events) == 1
    # Message is not encoded into bytes if sink is used
    assert sink.events[0] == test_message + "\n"

    # File shouldn't be open if the sink is used
    assert file_handler._file_async is None
    assert file_handler._file_sync is None


@pytest.mark.asyncio
async def test_write_async(file_handler: AsyncFileHandler) -> None:
    """Test asynchronous write into a temporary log file."""

    test_message: str = "Test log message"

    await file_handler._write_async(test_message)
    assert file_handler._file_async is not None
    assert file_handler._file_sync is None
    await file_handler.close()

    assert file_handler._filepath.exists()
    content: str = read_file_content(file_handler._filepath)
    assert test_message + "\n" == content


@pytest.mark.asyncio
async def test_open_overrides_existing(
    file_handler_with_existing_file: AsyncFileHandler,
) -> None:
    """Test opening a file creates a new file if there is an existing one."""

    file_handler: AsyncFileHandler = file_handler_with_existing_file
    test_message: str = "Test log message"

    existing_file: Path = file_handler._filepath
    assert existing_file.exists()

    file_handler._write_sync(test_message)
    file_handler.close_sync()

    # A new file was created
    assert file_handler._filepath != existing_file
    assert file_handler._filepath.name == "temporary.log.0001"
    content: str = read_file_content(file_handler._filepath)
    assert test_message + "\n" == content


@pytest.mark.asyncio
async def test_open_overrides_2_existing(
    temp_log_dir: Path,
    file_handler_with_existing_file: AsyncFileHandler,
) -> None:
    """Test opening a file recursively creates a new file if there are existing ones."""

    file_handler: AsyncFileHandler = file_handler_with_existing_file
    test_message: str = "Test log message"

    existing_file1: Path = file_handler._filepath
    assert existing_file1.exists()

    # Should walk up to `temporary.log.0002` because .0001 exists already
    existing_file2: Path = temp_log_dir / "temporary.log.0001"
    existing_file2.touch()
    assert existing_file2.exists()

    file_handler._write_sync(test_message)
    file_handler.close_sync()

    # A new file was created
    assert file_handler._filepath != existing_file2
    assert file_handler._filepath.name == "temporary.log.0002"
    content: str = read_file_content(file_handler._filepath)
    assert test_message + "\n" == content


@pytest.mark.asyncio
async def test_flush_without_file(file_handler: AsyncFileHandler) -> None:
    """Test flush method when no file is open."""

    assert file_handler._file_async is None
    assert file_handler._file_sync is None

    # Shouldn't raise
    await file_handler.flush()


@pytest.mark.asyncio
async def test_close_without_file(file_handler: AsyncFileHandler) -> None:
    """Test close method when no file is open."""

    assert file_handler._file_async is None
    assert file_handler._file_sync is None

    # Shouldn't raise
    file_handler.close_sync()
    await file_handler.close()


@pytest.mark.asyncio
async def test_close_method(file_handler: AsyncFileHandler) -> None:
    """Test close method works."""

    test_message: str = "Test log message"

    assert file_handler._file_async is None
    assert not file_handler._filepath.exists()

    await file_handler._write_async(test_message)
    assert file_handler._filepath.exists()

    assert file_handler._file_async is not None
    assert file_handler._filepath.exists()

    # Close method should close file
    await file_handler.close()
    assert file_handler._file_async is None
    assert file_handler._filepath.exists()


def test_concurrent_sync_writes(file_handler_with_sink: AsyncFileHandler) -> None:
    """Test that synchronous writes are thread-safe."""

    test_messages: list[str] = create_test_messages(count=10, msg_length=10)
    write_count: list[int] = [0]
    file_handler: AsyncFileHandler = file_handler_with_sink

    def mock_sink_write(msg: str) -> None:
        _ = msg
        write_count[0] += 1

    # Mock `Sink.write`
    assert file_handler.sink
    file_handler.sink.write = mock_sink_write

    # Create threads to write concurrently
    threads: list[Thread] = []
    for msg in test_messages:
        thread: Thread = threading.Thread(target=file_handler._write_sync, args=(msg,))
        threads.append(thread)
        thread.start()

    # Wait for all threads
    for thread in threads:
        thread.join()

    # Verify all messages were written
    assert write_count[0] == len(test_messages)


@pytest.mark.asyncio
async def test_concurrent_async_writes(
    file_handler_with_sink: AsyncFileHandler,
) -> None:
    """Test that asynchronous writes are properly serialized."""

    test_messages: list[str] = create_test_messages(count=10, msg_length=10)

    file_handler: AsyncFileHandler = file_handler_with_sink
    sink: Sink | None = file_handler.sink
    assert sink

    initial_count: int = len(sink.events)

    # Create async tasks
    tasks: list[CoroutineType[object, object, None]] = [
        file_handler._write_async(msg) for msg in test_messages
    ]

    # Run concurrently
    _ = await asyncio.gather(*tasks)

    # Verify all messages were written in order
    assert len(sink.events) == initial_count + len(test_messages)
    for i, msg in enumerate[str](test_messages):
        assert sink.events[initial_count + i] == msg + "\n"


def test_sync_error_when_passed_a_directory(
    default_file_handler_config: HandlerConfig,
    temp_log_dir: Path,
    mock_renderer: Renderer,
) -> None:
    """
    Test error is raised when synchronous write lazily tries to open the file, but the
    path is a directory path only.
    """

    config: HandlerConfig = default_file_handler_config
    # Just a directory path, not a file path
    config.params.filename = str(temp_log_dir)  # pyright: ignore[reportAttributeAccessIssue]
    renderer: Renderer = mock_renderer
    processors: list[Processor] = []

    test_message: str = "Test sync message"
    file_handler: AsyncFileHandler = _file_handler(config, renderer, processors)

    with pytest.raises(AlHandlerError, match="Failed to open"):
        file_handler._write_sync(test_message)


def test_sync_error_when_disk_full(file_handler: AsyncFileHandler) -> None:
    """
    Test error is raised when synchronous write lazily tries to open the file, but the
    disk is full.
    """

    test_message: str = "Test sync message"
    with patch.object(file_handler, "_open_sync", side_effect=IOError("Disk full")):
        with pytest.raises(AlHandlerError, match="Failed to open"):
            file_handler._write_sync(test_message)


@pytest.mark.asyncio
async def test_async_error_when_passed_a_directory(
    default_file_handler_config: HandlerConfig,
    temp_log_dir: Path,
    mock_renderer: Renderer,
) -> None:
    """
    Test error is raised when asynchronous write lazily tries to open the file, but the
    path is a directory path only.
    """

    config: HandlerConfig = default_file_handler_config
    # Just a directory path, not a file path
    config.params.filename = str(temp_log_dir)  # pyright: ignore[reportAttributeAccessIssue]
    renderer: Renderer = mock_renderer
    processors: list[Processor] = []

    test_message: str = "Test sync message"
    file_handler: AsyncFileHandler = _file_handler(config, renderer, processors)

    with pytest.raises(AlHandlerError, match=r"Failed to \(await\) open"):
        await file_handler._write_async(test_message)


@pytest.mark.asyncio
async def test_async_error_when_disk_full(file_handler: AsyncFileHandler) -> None:
    """
    Test error is raised when asynchronous write lazily tries to open the file, but the
    disk is full.
    """

    test_message: str = "Test sync message"
    with patch.object(file_handler, "_open", side_effect=IOError("Disk full")):
        with pytest.raises(AlHandlerError, match=r"Failed to \(await\) open"):
            await file_handler._write_async(test_message)

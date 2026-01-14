# pyright: reportPrivateUsage=false

from pathlib import Path

import pytest

from ko_log import AsyncRotatingFileHandler, Handler

from .._helpers import create_test_messages, read_file_content


class TestAsyncRotatingFileHandlerBasics:
    """Test suite for `AsyncRotatingFileHandler` basic usage."""

    @pytest.mark.asyncio
    async def test_init(
        self,
        rotating_file_handler: Handler,
        simple_log_file: Path,
    ) -> None:
        """Test attributes are set based from configuration, upon initialization."""

        assert isinstance(rotating_file_handler, AsyncRotatingFileHandler)
        assert rotating_file_handler._filepath == simple_log_file
        assert rotating_file_handler._file_async is None
        assert rotating_file_handler._file_sync is None
        assert rotating_file_handler._encoding == "utf-8"
        assert rotating_file_handler._mode == "ab"
        assert rotating_file_handler._max_bytes == 100
        assert rotating_file_handler._backup_count == 10
        assert rotating_file_handler._rotation_interval == 0

    @pytest.mark.asyncio
    async def test_write_single_message(
        self, rotating_file_handler_no_rotation: AsyncRotatingFileHandler
    ) -> None:
        handler: AsyncRotatingFileHandler = rotating_file_handler_no_rotation

        test_message: str = "Test log message"

        await handler._write_async(test_message)
        await handler.close()

        assert handler._filepath.exists()
        content: str = read_file_content(handler._filepath)
        assert test_message + "\n" == content

    @pytest.mark.asyncio
    async def test_write_many_messages(
        self, rotating_file_handler_no_rotation: AsyncRotatingFileHandler
    ) -> None:
        handler: AsyncRotatingFileHandler = rotating_file_handler_no_rotation

        messages: list[str] = ["Test message 1", "Test message 2", "Test message 3"]

        for msg in messages:
            await handler._write_async(msg)
        await handler.close()

        content: str = read_file_content(handler._filepath)
        expected: str = "\n".join(messages) + "\n"
        assert expected == content

    @pytest.mark.asyncio
    async def test_flush_method(
        self, rotating_file_handler_no_rotation: AsyncRotatingFileHandler
    ) -> None:
        handler: AsyncRotatingFileHandler = rotating_file_handler_no_rotation

        test_message: str = "Test flush"

        await handler._write_async(test_message)
        await handler.flush()

        assert handler._filepath.exists()
        content: str = read_file_content(handler._filepath)
        assert test_message + "\n" == content

        await handler.close()

    @pytest.mark.asyncio
    async def test_close_method(
        self, rotating_file_handler_no_rotation: AsyncRotatingFileHandler
    ) -> None:
        handler: AsyncRotatingFileHandler = rotating_file_handler_no_rotation

        await handler._write_async("Test message")
        assert handler._file_async is not None

        handler._write_sync("Test message")
        assert handler._file_sync is not None

        await handler.close()
        assert handler._file_async is None
        assert handler._file_sync is None


class TestSizeBasedRotation:
    """Test suite for `AsyncRotatingFileHandler` rotation system."""

    @pytest.mark.asyncio
    async def test_rotation_by_size_single_trigger(
        self,
        rotating_file_handler: AsyncRotatingFileHandler,
        temp_log_dir: Path,
    ) -> None:
        handler: AsyncRotatingFileHandler = rotating_file_handler
        log_dir: Path = temp_log_dir

        # 10 messages should trigger rotation as that should approx. be <100 bytes
        messages: list[str] = create_test_messages(count=10, msg_length=20)

        for msg in messages:
            await handler._write_async(msg)
        await handler.close()

        # Check files created
        log_files: list[Path] = list[Path](log_dir.glob(pattern="*.log*"))
        assert len(log_files) == 2

        backup_file: Path = log_dir / "temporary.log.0001"
        assert backup_file.exists()

        current_log_content: str = read_file_content(handler._filepath)
        assert len(current_log_content) > 0

        backup_log_content: str = read_file_content(backup_file)
        assert len(backup_log_content) > 0

    @pytest.mark.asyncio
    async def test_multiple_rotations(
        self,
        rotating_file_handler: AsyncRotatingFileHandler,
        temp_log_dir: Path,
    ) -> None:
        handler: AsyncRotatingFileHandler = rotating_file_handler
        log_dir: Path = temp_log_dir

        messages: list[str] = create_test_messages(count=50, msg_length=10)

        for msg in messages:
            await handler._write_async(msg)
        await handler.close()

        # Check files created
        log_files: list[Path] = sorted(log_dir.glob(pattern="*.log*"))
        assert len(log_files) > 3

        expected_files: list[str] = [
            "temporary.log",
            "temporary.log.0001",
            "temporary.log.0002",
            "temporary.log.0003",
            "temporary.log.0004",
        ]
        actual_files: list[str] = [file.name for file in log_files]
        assert sorted(actual_files) == sorted(expected_files)

    @pytest.mark.asyncio
    async def test_backup_count_respected(
        self,
        rotating_file_handler: AsyncRotatingFileHandler,
        temp_log_dir: Path,
    ) -> None:
        handler: AsyncRotatingFileHandler = rotating_file_handler
        log_dir: Path = temp_log_dir

        messages: list[str] = create_test_messages(count=100, msg_length=15)

        for msg in messages:
            await handler._write_async(msg)
        await handler.close()

        # Check files created
        log_files: list[Path] = sorted(log_dir.glob(pattern="*.log*"))
        assert len(log_files) == 11

        oldest_backup: Path = temp_log_dir / "temporary.log.0011"
        assert not oldest_backup.exists()

    @pytest.mark.asyncio
    async def test_rotation_with_existing_files(
        self,
        rotating_file_handler: AsyncRotatingFileHandler,
        temp_log_dir: Path,
    ) -> None:
        handler: AsyncRotatingFileHandler = rotating_file_handler
        log_dir: Path = temp_log_dir

        # Create existing files
        for i in range(1, 4):
            log_file: Path = log_dir / f"temporary.log.000{i}"
            _ = log_file.write_text(data=f"Old content {i}\n")

        # Write enough to rotate until 3rd backup because even if it doesn't go beyond
        # 3 backups, the existing ones should be removed
        messages: list[str] = create_test_messages(count=10, msg_length=10)

        for msg in messages:
            await handler._write_async(msg)
        await handler.close()

        # Check files created
        log_files: list[Path] = sorted(log_dir.glob(pattern="*.log*"))
        assert len(log_files) == 4

        # Check oldest existing file was removed
        oldest: Path = log_dir / "temporary.log.0004"
        assert not oldest.exists()

import asyncio
import os
import threading
import time
from _io import FileIO
from _thread import lock
from asyncio import Lock
from collections.abc import Callable
from pathlib import Path
from typing import override

import aiofiles
from aiofiles.threadpool import binary

from ..exceptions import AlHandlerError
from ..types import FileTextMode, Processor, Renderer
from ..utils import validate_file_path
from .base import Handler

# =====================================================================================
#   Basic File Handler
# =====================================================================================


class AsyncFileHandler(Handler):
    def __init__(
        self,
        renderer: Renderer,
        processors: list[Processor],
        *,
        filename: str | Path,
        mode: FileTextMode,
        encoding: str,
        override_existing: bool,
    ) -> None:
        super().__init__(renderer, processors)

        self._filepath: Path = validate_file_path(
            path=filename, create_missing_dir=True
        )
        self._file_async: binary.AsyncFileIO | None = None
        self._file_sync: FileIO | None = None
        self._mode: FileTextMode = mode
        self._encoding: str = encoding

        self._override: bool = override_existing

        self._lock_async: Lock = asyncio.Lock()
        self._lock_sync: lock = threading.Lock()

    @override
    def _write_sync(self, msg: str, /) -> None:
        line: str = msg + "\n"

        if self.sink:
            with self._lock_sync:
                self.sink.write(line)
            return

        if self._file_sync is None:
            try:
                self._open_sync()
            except (IsADirectoryError, IOError) as exc:
                raise AlHandlerError(
                    f"Failed to open the file at path `{self._filepath!s}`",
                    service=self.__class__.__name__,
                ) from exc
        assert self._file_sync is not None

        with self._lock_sync:
            _ = self._file_sync.write(line.encode(encoding=self._encoding))
            self._file_sync.flush()

    @override
    async def _write_async(self, msg: str, /) -> None:
        line: str = msg + "\n"

        if self.sink:
            async with self._lock_async:
                self.sink.write(line)
            return

        if self._file_async is None:
            try:
                await self._open()
            except (IsADirectoryError, IOError) as exc:
                raise AlHandlerError(
                    f"Failed to (await) open the file at path `{self._filepath!s}`",
                    service=self.__class__.__name__,
                ) from exc
        assert self._file_async is not None

        async with self._lock_async:
            _ = await self._file_async.write(line.encode(encoding=self._encoding))
            await self._file_async.flush()

    @override
    async def flush(self) -> None:
        """
        Flush both async and sync files to their destinations.

        WARNING:
            There is no `flush_sync` method unlike `close` and `close_sync`, as writing
            into this handler automatically performs a flush. It is highly unnecessary
            and only in rare cases you are in need to manually call this method.
        """

        if self._file_async:
            async with self._lock_async:
                await self._file_async.flush()

        if self._file_sync:
            with self._lock_sync:
                self._file_sync.flush()

    @override
    async def close(self) -> None:
        """Flush and close both async and sync file handle."""

        if self._file_async is not None:
            async with self._lock_async:
                await self._file_async.close()
                self._file_async = None

        if self._file_sync is not None:
            with self._lock_sync:
                self._file_sync.close()
                self._file_sync = None

    def close_sync(self) -> None:
        """Flush and close sync-only file handle."""

        if self._file_sync is not None:
            with self._lock_sync:
                self._file_sync.close()
                self._file_sync = None

    # ---------------------------------------------------------------------------------
    #   Helper methods
    # ---------------------------------------------------------------------------------

    def _open_sync(self) -> None:
        if self._override is False:
            self._avoid_override()

        self._file_sync = self._filepath.open(
            self._mode,
            buffering=0,
        )

    async def _open(self) -> None:
        if self._override is False:
            await asyncio.to_thread(self._avoid_override)

        self._file_async = await aiofiles.open(
            file=self._filepath,
            mode=self._mode,
            buffering=0,
        )

    def _avoid_override(self) -> None:
        retry: int = 1
        org_filepath: Path = self._filepath
        while True:
            if self._filepath.exists():
                self._filepath = Path(f"{org_filepath}.{retry:04d}")
                retry += 1
                continue
            break


# =====================================================================================
#   Rotating File Handler
# =====================================================================================


class AsyncRotatingFileHandler(Handler):
    def __init__(
        self,
        renderer: Renderer,
        processors: list[Processor],
        *,
        filename: str | Path,
        mode: FileTextMode,
        encoding: str,
        max_bytes: int | None,
        backup_count: int | None,
        rotation_interval: int | None,
        # Only for the developer to modify, not exposed publicly
        namer: Callable[[str, int], str] | None = None,
        rotator: Callable[[str, str], None] | None = None,
    ) -> None:
        super().__init__(renderer, processors)

        self._filepath: Path = validate_file_path(
            path=filename, create_missing_dir=True
        )
        self._file_async: binary.AsyncFileIO | None = None
        self._file_sync: FileIO | None = None
        self._mode: FileTextMode = mode
        self._encoding: str = encoding

        # Rotation parameters
        self._max_bytes: int = max_bytes or 0
        self._backup_count: int = backup_count or 0
        self._rotation_interval: int = rotation_interval or 0
        self._namer: Callable[[str, int], str] | None = namer
        self._rotator: Callable[[str, str], None] | None = rotator

        # State tracking
        self._current_size: int = 0
        self._last_rotation_time: float = 0
        self._base_filename: str = str(self._filepath)

        self._lock_async: Lock = asyncio.Lock()
        self._lock_sync: lock = threading.Lock()

    def _rotate_files_sync(self) -> None:
        """Rotate files synchronously."""

        if self._backup_count <= 0:
            return

        # Close current file
        if self._file_sync:
            self._file_sync.close()
            self._file_sync = None

        self._remove_if_reached_max_backup()
        self._rotate_existing_files()
        self._rename_current_to_first()

        # Reopen
        self._open_sync()

    def _should_rotate_sync(self, msg_length: int) -> bool:
        """Check if we should rotate based on size or time."""

        should_rotate: bool = False

        # Check size-based rotation
        if self._max_bytes > 0:
            self._current_size += msg_length
            if self._current_size >= self._max_bytes:
                should_rotate = True
                self._current_size = 0

        # Check time-based rotation
        if self._rotation_interval > 0:
            current_time = time.time()
            if current_time - self._last_rotation_time >= self._rotation_interval:
                should_rotate = True
                self._last_rotation_time = current_time

        return should_rotate

    async def _rotate_files(self) -> None:
        """Rotate files asynchronously."""

        if self._backup_count <= 0:
            return

        # Close current file
        if self._file_async:
            await self._file_async.close()
            self._file_async = None

        await asyncio.to_thread(self._remove_if_reached_max_backup)
        await asyncio.to_thread(self._rotate_existing_files)
        await asyncio.to_thread(self._rename_current_to_first)

        # Reopen
        await self._open()

    async def _should_rotate(self, msg_length: int) -> bool:
        """Asynchronous wrapper for rotation check."""

        # This is essentially the same logic, but I might want to make it truly async
        # if I add async file stats checking
        return self._should_rotate_sync(msg_length)

    @override
    def _write_sync(self, msg: str, /) -> None:
        line: str = msg + "\n"
        line_bytes: int = len(line.encode(encoding=self._encoding))

        if self.sink:
            with self._lock_sync:
                self.sink.write(line)
            return

        # Check if we need to rotate before writing
        if self._should_rotate_sync(msg_length=line_bytes):
            self._rotate_files_sync()

        if self._file_sync is None:
            try:
                self._open_sync()
            except (IsADirectoryError, IOError) as exc:
                raise AlHandlerError(
                    f"Failed to open the file at path `{self._filepath!s}`",
                    service=self.__class__.__name__,
                ) from exc
            self._set_initial_file_size()
        assert self._file_sync is not None

        with self._lock_sync:
            _ = self._file_sync.write(line.encode(encoding=self._encoding))
            self._file_sync.flush()

    @override
    async def _write_async(self, msg: str, /) -> None:
        line: str = msg + "\n"
        line_bytes: int = len(line.encode(encoding=self._encoding))

        if self.sink:
            async with self._lock_async:
                self.sink.write(line)
            return

        # Check if we need to rotate before writing
        if await self._should_rotate(msg_length=line_bytes):
            await self._rotate_files()

        if self._file_async is None:
            try:
                await self._open()
            except (IsADirectoryError, IOError) as exc:
                raise AlHandlerError(
                    f"Failed to (await) open the file at path `{self._filepath!s}`",
                    service=self.__class__.__name__,
                ) from exc
            await asyncio.to_thread(self._set_initial_file_size)
        assert self._file_async is not None

        async with self._lock_async:
            _ = await self._file_async.write(line.encode(encoding=self._encoding))
            await self._file_async.flush()

    @override
    async def flush(self) -> None:
        """
        Flush both async and sync files to their destinations.

        WARNING:
            There is no `flush_sync` method unlike `close` and `close_sync`, as writing
            into this handler automatically performs a flush. It is highly unnecessary
            and only in rare cases you are in need to manually call this method.
        """

        if self._file_async:
            async with self._lock_async:
                await self._file_async.flush()

        if self._file_sync:
            with self._lock_sync:
                self._file_sync.flush()

    @override
    async def close(self) -> None:
        """Flush and close both async and sync file handle."""

        if self._file_async is not None:
            async with self._lock_async:
                await self._file_async.close()
                self._file_async = None

        if self._file_sync is not None:
            with self._lock_sync:
                self._file_sync.close()
                self._file_sync = None

    def close_sync(self) -> None:
        """Flush and close sync-only file handle."""

        if self._file_sync is not None:
            with self._lock_sync:
                self._file_sync.close()
                self._file_sync = None

    # ---------------------------------------------------------------------------------
    #   Helper methods
    # ---------------------------------------------------------------------------------

    def _set_initial_file_size(self) -> None:
        if self._max_bytes > 0:
            self._current_size = os.path.getsize(filename=self._filepath)

    def _rename_current_to_first(self) -> None:
        if os.path.exists(path=self._base_filename):
            os.rename(src=self._base_filename, dst=self._get_rotated_filename(index=1))

    def _rotate_existing_files(self) -> None:
        for i in range(self._backup_count - 1, 0, -1):
            src: str = self._get_rotated_filename(index=i)
            dst: str = self._get_rotated_filename(index=i + 1)
            if os.path.exists(path=src):
                os.rename(src, dst)

    def _remove_if_reached_max_backup(self) -> None:
        if self._backup_count > 0:
            oldest_file: str = self._get_rotated_filename(index=self._backup_count)
            if os.path.exists(path=oldest_file):
                os.remove(path=oldest_file)

    def _get_rotated_filename(self, index: int) -> str:
        """Generate rotated filename based on naming convention."""

        if self._namer:
            return self._namer(self._base_filename, index)

        # Default naming: <filename>, <filename>.0001, <filename>.0002, etc.
        if index == 0:
            return self._base_filename
        return f"{self._base_filename}.{index:04d}"

    def _open_sync(self) -> None:
        self._file_sync = self._filepath.open(
            self._mode,
            buffering=0,
        )

    async def _open(self) -> None:
        self._file_async = await aiofiles.open(
            file=self._filepath,
            mode=self._mode,
            buffering=0,
        )

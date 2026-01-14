import asyncio
import sys
import threading
from _thread import lock
from asyncio import Lock
from typing import TextIO, override

from ..types import Processor, Renderer
from .base import Handler, Sink

# =====================================================================================
#   Stream handler
# =====================================================================================


class AsyncStreamHandler(Handler):
    def __init__(
        self,
        renderer: Renderer,
        processors: list[Processor] | None = None,
        *,
        use_stderr: bool = False,
    ) -> None:
        super().__init__(renderer, processors)
        self._use_stderr: bool = use_stderr

        self._lock_async: Lock = asyncio.Lock()
        self._lock_sync: lock = threading.Lock()

    @override
    def _write_sync(self, msg: str, /) -> None:
        if self.sink is not None:
            with self._lock_sync:
                self.sink.write(msg)
                return

        stream: TextIO = sys.stderr if self._use_stderr else sys.stdout
        with self._lock_sync:
            self._write_flush(stream, msg)

    @override
    async def _write_async(self, msg: str, /) -> None:
        if self.sink is not None:
            async with self._lock_async:
                self.sink.write(msg)
                return

        stream: TextIO = sys.stderr if self._use_stderr else sys.stdout
        async with self._lock_async:
            await asyncio.to_thread(self._write_flush, stream, msg)

    def _write_flush(self, stream: TextIO | Sink, msg: str) -> None:
        """For sync and async writes."""

        _ = stream.write(msg)
        stream.flush()

    @override
    async def flush(self) -> None:
        """No-op for console flushing."""
        pass

    @override
    async def close(self) -> None:
        """No-op for console closing."""
        pass

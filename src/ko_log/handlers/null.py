import asyncio
import threading
from _thread import lock
from asyncio import Lock
from typing import override

from ..types import Renderer
from .base import Handler

# =====================================================================================
#   Basic File Handler
# =====================================================================================


class AsyncNullHandler(Handler):
    """
    Discard all logs, except when there is a `Sink` attached.

    Used as a default handler or for test purposes.
    """

    def __init__(self, renderer: Renderer) -> None:
        super().__init__(renderer=renderer, processors=[])

        self._lock_async: Lock = asyncio.Lock()
        self._lock_sync: lock = threading.Lock()

    @override
    def _write_sync(self, msg: str, /) -> None:
        if self.sink is not None:
            with self._lock_sync:
                self.sink.write(msg)
                return

    @override
    async def _write_async(self, msg: str, /) -> None:
        if self.sink is not None:
            async with self._lock_async:
                self.sink.write(msg)
                return

    @override
    async def flush(self) -> None:
        pass

    @override
    async def close(self) -> None:
        pass

    async def _open(self) -> None:
        pass

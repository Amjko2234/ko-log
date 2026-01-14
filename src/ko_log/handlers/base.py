from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import TypeAlias, override

from ..exceptions import AlLoggerError, AlProcessorError
from ..models.handlers import HandlerConfig
from ..processors import DropLog
from ..types import EventDict, Processor, Renderer

FuncHandler: TypeAlias = Callable[[HandlerConfig, Renderer, list[Processor]], "Handler"]

# =====================================================================================
#   Sink
# =====================================================================================


class Sink:
    """
    Sink to properly and safey catch outputs of `SenaHandler` or its subclasses.

    Used for special cases, such as testing, and for redirecting stream logs that
    cannot be preconfigured to be directed towards the final destination.
    """

    def __init__(self) -> None:
        self.events: list[str] = []

    def write(self, msg: str, /) -> None:
        self.events.append(msg)

    def flush(self) -> None:
        """No-op for sink (non-stdout; non-stderr) flushing."""
        pass


# =====================================================================================
#   Mixins
# =====================================================================================


class _HasSinkMixin:
    def __init__(self) -> None:
        self._sink: Sink | None = None

    @property
    def sink(self) -> Sink | None:
        return self._sink

    @sink.setter
    def sink(self, sink: Sink | None, /) -> None:
        self._sink = sink


# =====================================================================================
#   Base
# =====================================================================================


class Handler(ABC, _HasSinkMixin):
    """
    Pure I/O handler protocol.
    Handlers receive pre-formatted messages and write to destinations.
    No formatting, filtering, or processing logic exists here.
    """

    __slots__: tuple[()] = ()

    def __init__(
        self,
        renderer: Renderer,
        processors: list[Processor] | None = None,
        # level: LogLevels = LogLevel.NOTSET,
    ) -> None:
        # Optional mixins
        super().__init__()
        self._sink: Sink | None = None

        self._renderer: Renderer = renderer
        self._processors: list[Processor] = processors or []

    @override
    def __repr__(self) -> str:
        return f"<${self.__class__.__name__}>"

    # ---------------------------------------------------------------------------------
    #   Sync writes
    # ---------------------------------------------------------------------------------

    def emit_sync(self, event_dict: EventDict, /) -> None:
        """Process `EventDict` with blocking write to destination."""

        fmtted_msg: str | None = self._fmt_msg(event_dict)
        if fmtted_msg is None:
            return  # Filtered out
        self._write_sync(fmtted_msg)

    @abstractmethod
    def _write_sync(self, msg: str, /) -> None:
        """Sync write pre-formatted message to destination."""
        raise NotImplementedError(
            "`_write_sync()` must be implemented by Handler subclasses"
        )

    # ---------------------------------------------------------------------------------
    #   Async writes
    # ---------------------------------------------------------------------------------

    async def emit_async(self, event_dict: EventDict, /) -> None:
        """Process `EventDict` through pipeline and write to destination."""

        fmtted_msg: str | None = self._fmt_msg(event_dict)
        if fmtted_msg is None:
            return  # Filtered out
        await self._write_async(fmtted_msg)

    @abstractmethod
    async def _write_async(self, msg: str, /) -> None:
        """Async write pre-formatted message to destination."""
        raise NotImplementedError(
            "`_write_async()` must be implemented by Handler subclasses"
        )

    @abstractmethod
    async def flush(self) -> None:
        raise NotImplementedError("`flush()` must be implemented by Handler subclasses")

    @abstractmethod
    async def close(self) -> None:
        raise NotImplementedError("`close()` must be implemented by Handler subclasses")

    # ---------------------------------------------------------------------------------
    #   Helper methods
    # ---------------------------------------------------------------------------------

    def _fmt_msg(self, event_dict: EventDict, /) -> str | None:
        processed: EventDict = event_dict
        for processor in self._processors:
            try:
                processed = processor(processed.copy())
            except DropLog:
                return None
            except AlProcessorError as exc:
                raise AlLoggerError(
                    "Failed to finish processing the message through top-level processors",
                    service=self.__class__.__name__,
                ) from exc
        return self._renderer(processed)

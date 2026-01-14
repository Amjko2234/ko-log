from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from types import TracebackType
from typing import Any, Literal, Protocol, TypeAlias, runtime_checkable

from .models.processors import ProcessorConfig, RendererConfig

# =====================================================================================
#   Base Logger protocol
# =====================================================================================


@runtime_checkable
class WrappedLogger(Protocol):
    name: str

    def __init__(self, name: str, *args, **kwargs) -> None:
        self.name = name

    def log(self, event_dict: EventDict) -> None:
        """Internal sync log method that creates the `LogRecord`."""
        pass

    async def async_log(self, event_dict: EventDict) -> None:
        """Internal async log method that creates the `LogRecord`."""
        pass


# =====================================================================================
#   Types
# =====================================================================================

# Generic
Scalar: TypeAlias = str | bool | int | float | None
JsonConfig: TypeAlias = Mapping[str, "JsonValue"] | Sequence["JsonValue"]
JsonValue: TypeAlias = Scalar | Mapping[str, "JsonValue"] | Sequence["JsonValue"]

FileTextMode: TypeAlias = Literal["wb", "ab"]

ExcType: TypeAlias = type[BaseException] | None
ExcValue: TypeAlias = BaseException | None
ExcTraceback: TypeAlias = TracebackType | None
ExcInfo: TypeAlias = tuple[ExcType, ExcValue, ExcTraceback]

# Logging-based
EventDict: TypeAlias = dict[str, Any]  # pyright: ignore[reportExplicitAny]

Context: TypeAlias = (
    Scalar | object | BaseException | Sequence["Context"] | Mapping[str, "Context"]
)
ContextScalar: TypeAlias = Scalar
LogContext: TypeAlias = dict[str, Context]

Renderer: TypeAlias = Callable[[EventDict], str]
FuncRenderer: TypeAlias = Callable[[RendererConfig], Renderer]

Processor: TypeAlias = Callable[[EventDict], EventDict]
FuncProcessor: TypeAlias = Callable[[ProcessorConfig], Processor]

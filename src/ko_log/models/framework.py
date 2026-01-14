from __future__ import annotations

import enum
from typing import ClassVar

from pydantic import BaseModel, ConfigDict, Field

from ..levels import LogLevel
from .handlers import HandlerConfig
from .processors import ProcessorConfig

# fmt: off


# =====================================================================================
#   Framework configurations
# =====================================================================================

class LoggerConfig(BaseModel):
    """Individual logger configuration."""

    name: str
    level: LogLevel = LogLevel.DEBUG
    processors: list[ProcessorConfig] = Field(default_factory=list)
    handlers: list[HandlerConfig] = Field(default_factory=list)
    propagate: bool = False
    context: dict[str, str] = Field(default_factory=dict)

    model_config: ClassVar[ConfigDict] = ConfigDict(
        extra="forbid",
        use_enum_values=True,
        str_strip_whitespace=True,
        str_min_length=1,
        str_max_length=1_000,
    )

class BackpressurePolicy(enum.StrEnum):
    """Define behavior when queue is full."""

    DROP = "drop"  # Silently drop new records
    BLOCK = "block"  # Wait until space is available
    DROP_OLDEST = "drop_oldest"  # Remove oldest, add new one


class QueueConfig(BaseModel):
    """Queue manager configuration."""

    max_queue_size: int = 10_000
    backpressure_policy: BackpressurePolicy = BackpressurePolicy.DROP_OLDEST
    drain_timeout: float = 5.0
    # * FUTURE: multiple workers
    worker_count: int = 1

    model_config: ClassVar[ConfigDict] = ConfigDict(
        extra="forbid",
        use_enum_values=True,
        str_strip_whitespace=True,
        str_min_length=1,
        str_max_length=1_000,
    )


class LoggingSystemConfig(BaseModel):
    """Root logging system configuration."""

    loggers: list[LoggerConfig] = Field(default_factory=list)
    default_level: LogLevel = LogLevel.INFO

    model_config: ClassVar[ConfigDict] = ConfigDict(
        extra="forbid",
        use_enum_values=True,
        str_strip_whitespace=True,
        str_min_length=1,
        str_max_length=1_000,
    )

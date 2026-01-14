from __future__ import annotations

import enum
from typing import ClassVar, Literal, TypeAlias

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ..types import FileTextMode
from ..utils import validate_file_path
from ._mixins import TypeDiscriminationValidatorMixin
from .processors import ProcessorConfig, RendererConfig

# =====================================================================================
#   Handler configurations
# =====================================================================================


class _HandlerParamsConfig(BaseModel):
    """Base handler params configuration."""

    model_config: ClassVar[ConfigDict] = ConfigDict(
        extra="allow",
        use_enum_values=True,
        str_strip_whitespace=True,
        str_min_length=1,
        str_max_length=1_000,
    )


class HandlerType(enum.StrEnum):
    FILE = "file"
    ROTATING_FILE = "rotating_file"
    STREAM = "stream"
    NULL = "null"


class NullHandlerConfig(_HandlerParamsConfig):
    type: Literal[HandlerType.NULL] = HandlerType.NULL


class AsyncFileHandlerConfig(_HandlerParamsConfig):
    type: Literal[HandlerType.FILE] = HandlerType.FILE

    filename: str
    mode: FileTextMode = "wb"
    encoding: str = "utf-8"
    override_existing: bool = True

    @field_validator("filename", mode="after")
    @classmethod
    def convert_filename(cls, value: str) -> str:
        filepath: str = str(validate_file_path(path=value, create_missing_dir=True))
        return filepath


class AsyncRotatingFileHandlerConfig(_HandlerParamsConfig):
    type: Literal[HandlerType.ROTATING_FILE] = HandlerType.ROTATING_FILE

    filename: str
    mode: FileTextMode = "ab"
    encoding: str = "utf-8"
    max_bytes: int | None = None
    backup_count: int | None = None
    rotation_interval: int | None = None

    @field_validator("filename", mode="after")
    @classmethod
    def convert_filename(cls, value: str) -> str:
        filepath: str = str(validate_file_path(path=value, create_missing_dir=True))
        return filepath


class AsyncStreamHandlerConfig(_HandlerParamsConfig):
    type: Literal[HandlerType.STREAM] = HandlerType.STREAM

    use_stderr: bool = False


HandlerConfigUnion: TypeAlias = (
    NullHandlerConfig
    | AsyncFileHandlerConfig
    | AsyncRotatingFileHandlerConfig
    | AsyncStreamHandlerConfig
)


class HandlerConfig(TypeDiscriminationValidatorMixin):
    """Base handler configuration."""

    type: HandlerType
    renderer: RendererConfig
    processors: list[ProcessorConfig] = Field(default_factory=list)
    params: HandlerConfigUnion = Field(discriminator="type")

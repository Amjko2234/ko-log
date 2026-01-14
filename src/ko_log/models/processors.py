from __future__ import annotations

import enum
from collections.abc import Mapping
from typing import ClassVar, Literal, TypeAlias

from pydantic import BaseModel, ConfigDict, Field
from rich import color as rich_color
from rich import emoji as rich_emoji
from rich import style as rich_style
from rich import theme as rich_theme

from ..levels import LogLevel, LogLevels
from ._mixins import TypeDiscriminationValidatorMixin

# =====================================================================================
#   Processor (formatters) configurations
# =====================================================================================


class ProcessorType(enum.StrEnum):
    """Available processor types."""

    # GENERAL
    ADD_CALLSITE_PARAMS = "add_callsite_params"
    ADD_CONTEXT_DEFAULTS = "add_context_defaults"
    DICT_TRACEBACKS = "dict_tracebacks"

    # FILTERS
    FILTER_BY_LEVEL = "filter_by_level"
    FILTER_KEYS = "filter_keys"
    FILTER_MARKUP = "filter_markup"
    # ROUTE_BY_LEVEL = "route_by_level"
    TIME_STAMPER = "time_stamper"


class _ProcessorParamsConfig(BaseModel):
    """Base processor params configuration."""

    model_config: ClassVar[ConfigDict] = ConfigDict(
        extra="allow",
        use_enum_values=True,
        str_strip_whitespace=True,
        str_min_length=1,
        str_max_length=1_000,
    )


# =====================================================================================


class CallsiteParameter(enum.StrEnum):
    """Callsite parameters that can be added to `event_dict`."""

    # Location
    PATHNAME = "pathname"
    FILENAME = "filename"
    LINENO = "lineno"
    # About
    FUNCNAME = "funcName"
    MODULE = "module"


class AddCallsiteParamsConfig(_ProcessorParamsConfig):
    """Add callsite parameters to `event_dict`."""

    type: Literal[ProcessorType.ADD_CALLSITE_PARAMS] = ProcessorType.ADD_CALLSITE_PARAMS
    parameters: set[CallsiteParameter] = Field(default_factory=set)


class AddContextDefaultConfig(_ProcessorParamsConfig):
    """Add default context fields to all events."""

    type: Literal[ProcessorType.ADD_CONTEXT_DEFAULTS] = (
        ProcessorType.ADD_CONTEXT_DEFAULTS
    )
    defaults: dict[str, str] = Field(default_factory=dict)


class DictTracebacksConfig(_ProcessorParamsConfig):
    """Capture tracebacks to event dict."""

    type: Literal[ProcessorType.DICT_TRACEBACKS] = ProcessorType.DICT_TRACEBACKS


class FilterByLevelConfig(_ProcessorParamsConfig):
    """Filter events by minimum log level."""

    type: Literal[ProcessorType.FILTER_BY_LEVEL] = ProcessorType.FILTER_BY_LEVEL
    min_level: LogLevels = LogLevel.INFO


class FilterKeysConfig(_ProcessorParamsConfig):
    """Remove specific keys from event dict."""

    type: Literal[ProcessorType.FILTER_KEYS] = ProcessorType.FILTER_KEYS
    keys_to_remove: list[str] = Field(default_factory=list)


# class RouteByLevelConfig(_ProcessorParamsConfig):
#     """Add handler routing metadata based on level."""
#
#     type: Literal[ProcessorType.ROUTE_BY_LEVEL] = ProcessorType.ROUTE_BY_LEVEL


class FilterMarkupConfig(_ProcessorParamsConfig):
    """Remove markup from event messages."""

    type: Literal[ProcessorType.FILTER_MARKUP] = ProcessorType.FILTER_MARKUP


# =====================================================================================

ProcessorParamsConfigUnion: TypeAlias = (
    # General procesors
    AddCallsiteParamsConfig
    | AddContextDefaultConfig
    | DictTracebacksConfig
    # Filter processors
    | FilterByLevelConfig
    | FilterKeysConfig
    | FilterMarkupConfig
    # | RouteByLevelConfig
)


class ProcessorConfig(TypeDiscriminationValidatorMixin):
    """Base processor configuration."""

    type: ProcessorType
    params: ProcessorParamsConfigUnion = Field(discriminator="type")


# =====================================================================================
#   Processor (renderers) configurations
# =====================================================================================


class _RendererParamsConfig(BaseModel):
    """Base console renderer params configuration."""

    fmt: str
    datefmt: str
    level: LogLevel = LogLevel.NOTSET

    model_config: ClassVar[ConfigDict] = ConfigDict(
        extra="allow",
        use_enum_values=True,
        str_strip_whitespace=True,
        str_min_length=1,
        str_max_length=1_000,
    )


class RendererType(enum.StrEnum):
    FILE_PLAIN = "file_plain"
    FILE_JSON = "file_json"
    STREAM_PLAIN = "stream_plain"
    STREAM_COLORED = "stream_colored"
    # !NOT RECOMMEND
    # *Stream logs are for brief, but important/significant executions at runtime
    STREAM_JSON = "stream_json"


# =====================================================================================


class PlainFileRendererConfig(_RendererParamsConfig):
    type: Literal[RendererType.FILE_PLAIN] = RendererType.FILE_PLAIN


class JSONFileRendererConfig(_RendererParamsConfig):
    """Key=val pair."""

    type: Literal[RendererType.FILE_JSON] = RendererType.FILE_JSON

    skip_keys: bool = False  # Skips keys that aren't basic types
    ensure_ascii: bool = True  # Non-ASCII characters are escaped
    allow_nan: bool = True  # Allow special floating point values
    indentation: int | None = 2
    sort_keys: bool = False


# =====================================================================================


class PlainStreamRendererConfig(_RendererParamsConfig):
    type: Literal[RendererType.STREAM_PLAIN] = RendererType.STREAM_PLAIN


COLOR_SYSTEM: TypeAlias = Literal["auto", "standard", "256", "truecolor", "windows"]
RichTheme: TypeAlias = rich_theme.Theme
RichStyle: TypeAlias = rich_style.Style
RichColor: TypeAlias = rich_color.Color
RichEmojiVariant: TypeAlias = rich_emoji.EmojiVariant
RichFormatTimeCallable: TypeAlias = str


class RichThemeConfig(BaseModel):
    styles: Mapping[str, str | RichStyleConfig] | None = None


class RichStyleConfig(BaseModel):
    color: RichColor | str | None = None
    bgcolor: RichColor | str | None = None
    bold: bool | None = None
    dim: bool | None = None
    italic: bool | None = None
    underline: bool | None = None
    blink: bool | None = None
    blink2: bool | None = None
    reverse: bool | None = None
    conceal: bool | None = None
    strike: bool | None = None
    underline2: bool | None = None
    frame: bool | None = None
    encircle: bool | None = None
    overline: bool | None = None
    link: str | None = None
    meta: Mapping[str, str] | None = None


class ColoredStreamRendererConfig(_RendererParamsConfig):
    """Colored renderer configuration."""

    type: Literal[RendererType.STREAM_COLORED] = RendererType.STREAM_COLORED

    color_system: COLOR_SYSTEM | None = "auto"
    force_terminal: bool | None = True
    force_interactive: bool | None = None
    soft_wrap: bool = False
    theme: RichThemeConfig | None = None
    quiet: bool = False
    width: int | None = None
    height: int | None = None
    style: RichStyleConfig | None = None
    no_color: bool | None = None
    tab_size: int = 8
    markup: bool = True
    emoji: bool = True
    emoji_variant: RichEmojiVariant | None = None
    highlight: bool = False
    log_time: bool = False
    log_path: bool = False
    log_time_format: RichFormatTimeCallable = "[%X]"
    legacy_windows: bool | None = None
    safe_box: bool = True
    environ: Mapping[str, str] | None = None


class JSONStreamRendererConfig(_RendererParamsConfig):
    """Key=val pair. NOT RECOMMENDED."""

    type: Literal[RendererType.STREAM_JSON] = RendererType.STREAM_JSON

    skip_keys: bool = False  # Skips keys that aren't basic types
    ensure_ascii: bool = True  # Non-ASCII characters are escaped
    allow_nan: bool = True  # Allow special floating point values
    indentation: int | None = 2
    separators: tuple[str, str] = ",", ":"
    sort_keys: bool = False


RendererConfigUnion: TypeAlias = (
    PlainFileRendererConfig
    | JSONFileRendererConfig
    | PlainStreamRendererConfig
    | ColoredStreamRendererConfig
    | JSONStreamRendererConfig
)


class RendererConfig(TypeDiscriminationValidatorMixin):
    """Base renderer configuration."""

    type: RendererType
    params: RendererConfigUnion = Field(discriminator="type")

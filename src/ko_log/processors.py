from __future__ import annotations

import json
import re
from collections.abc import Mapping
from datetime import datetime, timezone
from typing import cast, final

from rich import console as rich_console
from rich.console import Console

from .exceptions import AlConfigurationError
from .levels import LogLevel, check_level
from .models.processors import (
    COLOR_SYSTEM,
    CallsiteParameter,
    ProcessorConfig,
    ProcessorType,
    RendererConfig,
    RendererType,
    RichEmojiVariant,
    RichFormatTimeCallable,
    RichStyle,
    RichStyleConfig,
    RichTheme,
    RichThemeConfig,
)
from .types import EventDict, ExcInfo, Processor, Renderer

# =====================================================================================
#   Drop signal
# =====================================================================================


class DropLog(Exception):
    pass


# =====================================================================================
#   General Processors (formatters & filters)
# =====================================================================================


def add_callsite_params(config: ProcessorConfig) -> Processor:
    """Add callsite parameters (e.g., filename, lineno) to each log line."""

    if (config.type != ProcessorType.ADD_CALLSITE_PARAMS) or (
        config.params.type != ProcessorType.ADD_CALLSITE_PARAMS
    ):
        raise AlConfigurationError(
            "`ADD_CALLSITE_PARAMS` processor set with invalid params",
            service=add_callsite_params.__name__,
        )
    params: set[CallsiteParameter] = set(config.params.parameters)

    def processor(event_dict: EventDict) -> EventDict:
        # I dont know how to get the callsite values from this context TT
        # IM SORRYYYYYYYYY THIS IS THE ONLY WAY I KNOW AND IM LAZY TO THINK OF ANOTHER
        # WORKAROUND TT
        for cparam in [p.value for p in CallsiteParameter]:
            # All callsite parameters are automatically added per log call, only by
            # specifying which ones included--the rest are removed
            if cparam in params:
                continue
            else:
                del event_dict[cparam]
        return event_dict

    return processor


def add_context_defaults(config: ProcessorConfig) -> Processor:
    """Add default context fields to all events."""

    if (
        config.type != ProcessorType.ADD_CONTEXT_DEFAULTS
    ) or config.params.type != ProcessorType.ADD_CONTEXT_DEFAULTS:
        raise AlConfigurationError(
            "`ADD_CONTEXT_DEFAULTS` processor set with invalid params",
            service=add_context_defaults.__name__,
        )
    defaults: dict[str, str] = config.params.defaults

    def processor(event_dict: EventDict) -> EventDict:
        # Add defaults that aren't already present
        for key, val in defaults.items():
            event_dict.setdefault(key, val)
        return event_dict

    return processor


def dict_tracebacks(config: ProcessorConfig) -> Processor:
    """
    Converts `exc_info` tuple to a structured `dict` with traceback `frames`.
    Removes `exc_info` after processing to avoid serialization issues.
    """

    import sys
    import traceback

    if (config.type != ProcessorType.DICT_TRACEBACKS) or (
        config.params.type != ProcessorType.DICT_TRACEBACKS
    ):
        raise AlConfigurationError(
            "`DICT_TRACEBACKS` processor set with invalid params",
            service=dict_tracebacks.__name__,
        )

    def processor(event_dict: EventDict) -> EventDict:
        exc_info: ExcInfo | bool | None = event_dict.pop(  # pyright: ignore[reportAny]
            "exc_info", None
        )

        if (exc_info is None) or (exc_info is False):
            return event_dict

        if exc_info is True:
            exc_info = sys.exc_info()
        exc_type, exc_value, exc_tb = exc_info
        if exc_type is None:
            return event_dict

        # Build structured exception dictionary
        event_dict["exception"] = {
            "type": exc_type.__name__,
            "module": exc_type.__module__,
            "message": str(exc_value),
            "traceback": [
                {
                    "file": frame.filename,
                    "line": frame.lineno,
                    "function": frame.name,
                    "code": frame.line,
                }
                for frame in traceback.extract_tb(tb=exc_tb)
            ],
        }

        # Clear references to avoid leakage or double serialization
        del exc_info, exc_type, exc_value, exc_tb

        return event_dict

    return processor


def filter_by_level(config: ProcessorConfig) -> Processor:
    """
    Create level filter processor.
    Drops events below minimum level before formatting.

    Raises:
    * `DropLog`: if event has a level below minimum.
    """

    if (config.type != ProcessorType.FILTER_BY_LEVEL) or (
        config.params.type != ProcessorType.FILTER_BY_LEVEL
    ):
        raise AlConfigurationError(
            "`FILTER_BY_LEVEL` processor set with invalid params",
            service=filter_by_level.__name__,
        )
    min_level: int = check_level(level=config.params.min_level)

    def processor(event_dict: EventDict) -> EventDict:
        level: str = cast(str, event_dict.get("level"))
        if not level:
            return event_dict

        level_int: int = check_level(level=level.upper())
        if level_int < min_level:
            raise DropLog

        return event_dict

    return processor


def filter_keys(config: ProcessorConfig) -> Processor:
    """
    Remove specific keys from `EventDict`.
    Useful for excluding sensitive data before logging.
    """

    if (config.type != ProcessorType.FILTER_KEYS) or (
        config.params.type != ProcessorType.FILTER_KEYS
    ):
        raise AlConfigurationError(
            "`FILTER_KEYS` processor set with invalid params",
            service=filter_keys.__name__,
        )
    keys_to_remove: list[str] = config.params.keys_to_remove

    def processor(event_dict: EventDict) -> EventDict:
        for key in keys_to_remove:
            event_dict.pop(key, None)
        return event_dict

    return processor


# TODO: Implement when necessary
# def route_by_level_to_handler(config: ProcessorConfig) -> Processor:
#     """
#     Add handler routing hint based on level.
#
#     Example: ERROR+ logs go to stderr, others to stdout
#     """
#
#     def _route_by_level_to_handler(level_route: LogLevels) -> Processor:
#         def processor(
#             logger: WrappedLogger,
#
#             event_dict: EventDict,
#         ) -> EventDict:
#             _level: str = cast(str, event_dict.get("level", "info")).upper()
#             level_int: int = check_level(level=_level)
#             level_route_int: int = check_level(level=level_route)
#             # Add routing metadata
#             event_dict["_use_stderr"] = level_int >= level_route_int
#             return event_dict
#
#         return processor
#
#     if config.params.type != ProcessorType.ROUTE_BY_LEVEL:
#         raise RuntimeError("`ROUTE_BY_LEVEL` processor set without params")


def filter_markup(config: ProcessorConfig) -> Processor:
    """Remove markup from event messages."""

    if (config.type != ProcessorType.FILTER_MARKUP) or (
        config.params.type != ProcessorType.FILTER_MARKUP
    ):
        raise AlConfigurationError(
            "`filter_markup` processor set with invalid params",
            service=filter_markup.__name__,
        )
    pattern: re.Pattern[str] = re.compile(r"\[/?[^\]]*\]")

    def processor(event_dict: EventDict) -> EventDict:
        event_dict["event"] = pattern.sub(
            "",
            event_dict.get("event", ""),  # pyright: ignore[reportAny]
        )
        return event_dict

    return processor


# =====================================================================================
#   Processors (renderer)
# =====================================================================================


def plain_renderer(config: RendererConfig) -> Renderer:
    """Create a plain `PlainRenderer`."""

    # *Will never raise as the plain renderer does not have any params
    if (
        config.type != RendererType.FILE_PLAIN
        or config.params.type != RendererType.FILE_PLAIN
    ) and (
        config.type != RendererType.STREAM_PLAIN
        or config.params.type != RendererType.STREAM_PLAIN
    ):
        raise AlConfigurationError(
            "`PLAIN` renderer set with invalid params",
            service=plain_renderer.__name__,
        )

    return PlainRenderer(
        config.params.fmt,
        config.params.datefmt,
        config.params.level,
    )


def json_renderer(config: RendererConfig) -> Renderer:
    """Create configured `processors.JSONRenderer`."""

    if (
        config.type != RendererType.FILE_JSON
        or config.params.type != RendererType.FILE_JSON
    ) and (
        config.type != RendererType.STREAM_JSON
        or config.params.type != RendererType.STREAM_JSON
    ):
        raise AlConfigurationError(
            "`JSON` renderer set with invalid params",
            service=json_renderer.__name__,
        )
    return JSONRenderer(
        config.params.fmt,
        config.params.datefmt,
        config.params.level,
        config.params.skip_keys,
        config.params.ensure_ascii,
        config.params.allow_nan,
        config.params.indentation,
        config.params.sort_keys,
    )


def colored_renderer(config: RendererConfig) -> Renderer:
    """Create configured custom `ColoredRenderer`."""

    if (config.type != RendererType.STREAM_COLORED) or (
        config.params.type != RendererType.STREAM_COLORED
    ):
        raise AlConfigurationError(
            "`COLORED` renderer set with invalid params",
            service=colored_renderer.__name__,
        )
    return ColoredRenderer(
        config.params.fmt,
        config.params.datefmt,
        config.params.level,
        config.params.color_system,
        config.params.force_terminal,
        config.params.force_interactive,
        config.params.soft_wrap,
        config.params.theme,
        config.params.quiet,
        config.params.width,
        config.params.height,
        config.params.style,
        config.params.no_color,
        config.params.tab_size,
        config.params.markup,
        config.params.emoji,
        config.params.emoji_variant,
        config.params.highlight,
        config.params.log_time,
        config.params.log_path,
        config.params.log_time_format,
        config.params.legacy_windows,
        config.params.safe_box,
        config.params.environ,
    )


# =====================================================================================


class _RendererBase:
    def __init__(self, fmt: str, datefmt: str, level: LogLevel) -> None:
        self._fmt: str = fmt
        self._datefmt: str = datefmt
        self._lvl: LogLevel = level


def _percent_style_formatter(event_dict: EventDict, fmt: str, datefmt: str) -> str:
    date: datetime = event_dict.pop(  # pyright: ignore[reportAny]
        "timestamp", datetime.now(tz=timezone.utc)
    )
    event_dict["asctime"] = date.strftime(format=datefmt)
    fmtted_event: str = fmt % event_dict
    return fmtted_event


# =====================================================================================


@final
class PlainRenderer(_RendererBase):
    __slots__ = (
        "_fmt",
        "_datefmt",
        "_lvl",
    )

    def __init__(self, fmt: str, datefmt: str, level: LogLevel) -> None:
        super().__init__(fmt, datefmt, level)

    def __call__(self, event_dict: EventDict) -> str:
        # Useless to set level to logger's default; log will still push through
        if self._lvl == LogLevel.NOTSET:
            return _percent_style_formatter(
                event_dict, fmt=self._fmt, datefmt=self._datefmt
            )

        event_level: str = event_dict["level"]  # pyright: ignore[reportAny]
        if check_level(level=event_level) < check_level(level=self._lvl):
            raise DropLog

        return _percent_style_formatter(
            event_dict, fmt=self._fmt, datefmt=self._datefmt
        )


@final
class JSONRenderer(_RendererBase):
    __slots__ = (
        "_fmt",
        "_datefmt",
        "_lvl",
        "_skip_keys",
        "_ensure_ascii",
        "_allow_nan",
        "_indentation",
        "_sort_keys",
    )

    def __init__(
        self,
        fmt: str,
        datefmt: str,
        level: LogLevel,
        skip_keys: bool,  # False
        ensure_ascii: bool,  # True
        allow_nan: bool,  # True
        indentation: int | None,  # 2
        sort_keys: bool,  # False
    ) -> None:
        super().__init__(fmt, datefmt, level)

        self._skip_keys: bool = skip_keys
        self._ensure_ascii: bool = ensure_ascii
        self._allow_nan: bool = allow_nan
        self._indentation: int | None = indentation
        self._sort_keys: bool = sort_keys

    def __call__(self, event_dict: EventDict) -> str:
        # Useless to set level to logger's default; log will still push through
        if self._lvl != LogLevel.NOTSET:
            event_level: str = event_dict["level"]  # pyright: ignore[reportAny]
            if check_level(level=event_level) < check_level(level=self._lvl):
                raise DropLog

        assert isinstance(event_dict, dict)
        psfmt_event: str = _percent_style_formatter(
            event_dict=event_dict, fmt=self._fmt, datefmt=self._datefmt
        )

        ctx: str = event_dict.pop("context", "")  # pyright: ignore[reportAny]
        if not ctx:
            return f"{psfmt_event}"

        json_event_dict: str = json.dumps(
            obj=ctx,
            skipkeys=self._skip_keys,
            ensure_ascii=self._ensure_ascii,
            allow_nan=self._allow_nan,
            indent=self._indentation,
            separators=(",", ": "),
            sort_keys=self._sort_keys,
            default=str,
        )
        return f"{psfmt_event}:\n{json_event_dict}"


@final
class ColoredRenderer(_RendererBase):
    """
    Render logs with ANSI colors for console output.
    Must be last processor in chain (terminal handler).
    """

    __slots__ = (
        "_fmt",
        "_datefmt",
        "_lvl",
        "_color_system",
        "_force_terminal",
        "_force_interactive",
        "_soft_wrap",
        "_theme",
        "_quiet",
        "_width",
        "_height",
        "_style",
        "_no_color",
        "_tab_size",
        "markup",
        "_emoji",
        "_emoji_variant",
        "_highlight",
        "_log_time",
        "_log_path",
        "_log_time_format",
        "_legacy_windows",
        "_safe_box",
        "_environ",
    )

    def __init__(
        self,
        fmt: str,
        datefmt: str,
        level: LogLevel,
        color_system: COLOR_SYSTEM | None,  # "auto"
        force_terminal: bool | None,  # True
        force_interactive: bool | None,  # None
        soft_wrap: bool,  # False
        theme: RichThemeConfig | None,  # None
        quiet: bool,  # False
        width: int | None,  # None
        height: int | None,  # None
        style: RichStyleConfig | None,  # None
        no_color: bool | None,  # None
        tab_size: int,  # 8
        markup: bool,  # True
        emoji: bool,  # True
        emoji_variant: RichEmojiVariant | None,  # None
        highlight: bool,  # False
        log_time: bool,  # False
        log_path: bool,  # False
        log_time_format: RichFormatTimeCallable,  # "[%X]"
        legacy_windows: bool | None,  # None
        safe_box: bool,  # True
        environ: Mapping[str, str] | None,  # None
    ) -> None:
        super().__init__(fmt, datefmt, level)

        _styles = None
        if theme and theme.styles:
            _styles: Mapping[str, str | RichStyle] | None = {
                key: val for key, val in theme.styles if RichStyle(*val)
            }

        self._color_system: COLOR_SYSTEM | None = color_system
        self._force_terminal: bool | None = force_terminal
        self._force_interactive: bool | None = force_interactive
        self._soft_wrap: bool = soft_wrap
        self._theme: RichTheme | None = RichTheme(styles=_styles)
        self._quiet: bool = quiet
        self._width: int | None = width
        self._height: int | None = height
        self._style: RichStyle | None = RichStyle(*style) if style else None
        self._no_color: bool | None = no_color
        self._tab_size: int = tab_size
        self.markup: bool = markup
        self._emoji: bool = emoji
        self._emoji_variant: RichEmojiVariant | None = emoji_variant
        self._highlight: bool = highlight
        self._log_time: bool = log_time
        self._log_path: bool = log_path
        self._log_time_format: RichFormatTimeCallable = log_time_format
        self._legacy_windows: bool | None = legacy_windows
        self._safe_box: bool = safe_box
        self._environ: Mapping[str, str] | None = environ

    def __call__(self, event_dict: EventDict) -> str:
        # Useless to set level to logger's default; log will still push through
        if self._lvl != LogLevel.NOTSET:
            event_level: str = event_dict["level"]  # pyright: ignore[reportAny]
            if check_level(level=event_level) < check_level(level=self._lvl):
                raise DropLog

        console: Console = rich_console.Console(
            color_system=self._color_system,
            force_terminal=self._force_terminal,
            force_interactive=self._force_interactive,
            soft_wrap=self._soft_wrap,
            theme=self._theme,
            quiet=self._quiet,
            width=self._width,
            height=self._height,
            style=self._style,
            no_color=self._no_color,
            tab_size=self._tab_size,
            markup=self.markup,
            emoji=self._emoji,
            emoji_variant=self._emoji_variant,
            highlight=self._highlight,
            log_time=self._log_time,
            log_path=self._log_path,
            log_time_format=self._log_time_format,
            legacy_windows=self._legacy_windows,
            safe_box=self._safe_box,
            _environ=self._environ,
        )

        # Format to asctime
        date: datetime = event_dict.pop(  # pyright: ignore[reportAny]
            "timestamp", datetime.now(tz=timezone.utc)
        )
        event_dict["asctime"] = date.strftime(format=self._datefmt)

        # Convert markup syntax to ANSI syntax
        for key, value in list(event_dict.items()):  # pyright: ignore[reportAny]
            with console.capture() as capture:
                console.print(value, soft_wrap=True, end="")
            event_dict[key] = capture.get()

        fmtted_event: str = self._fmt % event_dict

        return str(fmtted_event + "\n")

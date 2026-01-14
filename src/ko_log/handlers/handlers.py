from ..exceptions import AlConfigurationError
from ..models import HandlerConfig, HandlerType
from ..types import Processor, Renderer
from .base import FuncHandler
from .file import AsyncFileHandler, AsyncRotatingFileHandler
from .null import AsyncNullHandler
from .stream import AsyncStreamHandler


def file_handler(
    config: HandlerConfig,
    renderer: Renderer,
    processors: list[Processor],
) -> AsyncFileHandler:
    """Create configured `handlers.file.AsyncFileHandler`."""

    if config.params.type != HandlerType.FILE:
        raise AlConfigurationError(
            "`FILE` handler set with invalid params",
            service=file_handler.__name__,
        )
    return AsyncFileHandler(
        renderer,
        processors,
        filename=config.params.filename,
        mode=config.params.mode,
        encoding=config.params.encoding,
        override_existing=config.params.override_existing,
    )


def rotating_file_handler(
    config: HandlerConfig,
    renderer: Renderer,
    processors: list[Processor],
) -> AsyncRotatingFileHandler:
    """Create configured `handlers.file.AsyncRotatingFileHandler`."""

    if config.params.type != HandlerType.ROTATING_FILE:
        raise AlConfigurationError(
            "`ROTATING_FILE` handler set with invalid params",
            service=rotating_file_handler.__name__,
        )
    return AsyncRotatingFileHandler(
        renderer,
        processors,
        filename=config.params.filename,
        mode=config.params.mode,
        encoding=config.params.encoding,
        max_bytes=config.params.max_bytes,
        backup_count=config.params.backup_count,
        rotation_interval=config.params.rotation_interval,
    )


def stream_handler(
    config: HandlerConfig,
    renderer: Renderer,
    processors: list[Processor],
) -> AsyncStreamHandler:
    """Create configured `handlers.stream.AsyncStreamHandler`."""

    if (config.type != HandlerType.STREAM) or (
        config.params.type != HandlerType.STREAM
    ):
        raise AlConfigurationError(
            "`CONSOLE` handler set with invalid params",
            service=stream_handler.__name__,
        )
    return AsyncStreamHandler(
        renderer,
        processors,
        use_stderr=config.params.use_stderr,
    )


def null_handler(
    config: HandlerConfig,
    renderer: Renderer,
    processors: list[Processor],
) -> AsyncNullHandler:
    """Create `handlers.null.AsyncNullHandler`."""

    _, _ = config, processors
    return AsyncNullHandler(renderer)


handler_map: dict[HandlerType, FuncHandler] = {
    HandlerType.NULL: null_handler,
    HandlerType.FILE: file_handler,
    HandlerType.ROTATING_FILE: rotating_file_handler,
    HandlerType.STREAM: stream_handler,
}

# pyright: reportPrivateUsage=false
from __future__ import annotations

import sys
import tempfile
from collections.abc import Generator
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest

from ko_log import LogLevel, Sink
from ko_log import file_handler as _file_handler
from ko_log import rotating_file_handler as _rotating_file_handler
from ko_log import stream_handler as _stream_handler
from ko_log.handlers import (
    AsyncFileHandler,
    AsyncRotatingFileHandler,
    AsyncStreamHandler,
    Handler,
)
from ko_log.models import (
    AddCallsiteParamsConfig,
    AddContextDefaultConfig,
    AsyncFileHandlerConfig,
    AsyncRotatingFileHandlerConfig,
    AsyncStreamHandlerConfig,
    CallsiteParameter,
    DictTracebacksConfig,
    FilterByLevelConfig,
    FilterKeysConfig,
    FilterMarkupConfig,
    HandlerConfig,
    HandlerType,
    JSONFileRendererConfig,
    PlainFileRendererConfig,
    PlainStreamRendererConfig,
    ProcessorConfig,
    ProcessorType,
    RendererConfig,
    RendererType,
)
from ko_log.processors import (
    _RendererBase,
    add_callsite_params,
    add_context_defaults,
    dict_tracebacks,
    filter_by_level,
    filter_keys,
    filter_markup,
)
from ko_log.types import EventDict, Processor, Renderer

# Allow users to test without downloading the module as an editable
# Get the project root directory
project_root: Path = Path(__file__).parent.parent

# Add `src` directory to Python path so imports work without installation
src_dir: Path = project_root / "src"
if src_dir.exists():
    sys.path.insert(0, str(src_dir))

#!======================================================================================
#! DISCLAIMER
#!   The following contains explicit configuration setup of all processors, renderers,
#!   and handlers. I, Amjko, do not recommend this approach of configuring loggers, as
#!   it is a hassle to do and immediately populates your imports.
#
#    However, it remains as a highly opinionated disclaimer. Therefore, it is *STILL UP
#    TO YOU* as to how you will configure the loggers. It will remain that the main
#    entrypoint (intentional design) for configuring loggers is through a dictionary
#    JSON/YAML data.
#!======================================================================================

# ======================================================================================
#   Generic
# ======================================================================================


@pytest.fixture
def temp_log_dir() -> Generator[Path, None]:
    """Create a temporary directory for testing."""

    with tempfile.TemporaryDirectory() as tempdir:
        yield Path(tempdir)


@pytest.fixture
def random_log_file() -> Generator[Path, None]:
    """Create a temporary file (name is randomly generated) for testing."""

    with tempfile.NamedTemporaryFile(suffix=".log", delete=False) as file:
        temp_path: Path = Path(file.name)
    yield temp_path
    if temp_path.exists():
        temp_path.unlink()


@pytest.fixture
def simple_log_file(temp_log_dir: Path) -> Path:
    """Create a temporary file for testing."""

    return temp_log_dir / "temporary.log"


@pytest.fixture
def temp_log_dir_with_file(
    temp_log_dir: Path, simple_log_file: Path
) -> Generator[tuple[Path, Path], None]:
    """Create a temporary directory with an existing file."""

    simple_log_file.touch()
    yield temp_log_dir, simple_log_file


@pytest.fixture
def sink() -> Sink:
    """Create a `Sink` for capturing output."""

    return Sink()


# ======================================================================================
#   Renderers
# ======================================================================================


@pytest.fixture
def mock_renderer() -> Renderer:
    class MockRenderer(_RendererBase):
        def __init__(self, fmt: str, datefmt: str, level: LogLevel) -> None:
            super().__init__(fmt, datefmt, level)

        def __call__(self, event_dict: EventDict) -> str:
            assert isinstance(event_dict["event"], str)
            return event_dict["event"]

    return MockRenderer(fmt="foobar", datefmt="foobar", level=LogLevel.DEBUG)


# ======================================================================================
#   Processors
# ======================================================================================


@pytest.fixture
def mock_processor() -> Processor:
    def processor(event_dict: EventDict) -> EventDict:
        assert isinstance(event_dict["event"], str)
        return event_dict

    return processor


@pytest.fixture
def proc_add_callsite_params() -> Processor:
    config: ProcessorConfig = ProcessorConfig(
        type=ProcessorType.ADD_CALLSITE_PARAMS,
        params=AddCallsiteParamsConfig(
            parameters={
                CallsiteParameter.FILENAME,
                CallsiteParameter.FUNCNAME,
                CallsiteParameter.LINENO,
                CallsiteParameter.MODULE,
                CallsiteParameter.PATHNAME,
            }
        ),
    )
    return add_callsite_params(config)


@pytest.fixture
def proc_add_context_defaults() -> Processor:
    config: ProcessorConfig = ProcessorConfig(
        type=ProcessorType.ADD_CONTEXT_DEFAULTS,
        params=AddContextDefaultConfig(
            defaults={
                "environment": "dev",
            },
        ),
    )
    return add_context_defaults(config)


@pytest.fixture
def proc_dict_tracebacks() -> Processor:
    config: ProcessorConfig = ProcessorConfig(
        type=ProcessorType.DICT_TRACEBACKS,
        params=DictTracebacksConfig(),
    )
    return dict_tracebacks(config)


@pytest.fixture
def proc_filter_by_level() -> Processor:
    config: ProcessorConfig = ProcessorConfig(
        type=ProcessorType.FILTER_BY_LEVEL,
        params=FilterByLevelConfig(
            min_level=LogLevel.INFO,
        ),
    )
    return filter_by_level(config)


@pytest.fixture
def proc_filter_keys() -> Processor:
    config: ProcessorConfig = ProcessorConfig(
        type=ProcessorType.FILTER_KEYS,
        params=FilterKeysConfig(
            keys_to_remove=[
                "remove_this_key1",
                "remove_this_key2",
                "remove_this_key3",
            ]
        ),
    )
    return filter_keys(config)


@pytest.fixture
def proc_filter_markup() -> Processor:
    config: ProcessorConfig = ProcessorConfig(
        type=ProcessorType.FILTER_MARKUP,
        params=FilterMarkupConfig(),
    )
    return filter_markup(config)


# ======================================================================================
#   Handlers
# ======================================================================================


@pytest.fixture
def mock_handler() -> Mock:
    """Create a mock `Handler` for testing."""

    handler: Mock = Mock(spec=Handler)
    handler.emit_sync = Mock()
    handler.emit_async = AsyncMock()
    return handler


# ======================================================================================
#   AsyncStreamHandler
# ======================================================================================


@pytest.fixture
def default_stream_handler_config() -> HandlerConfig:
    """Get default (or common) configuration of `AsyncStreamHandler`."""

    return HandlerConfig(
        type=HandlerType.STREAM,
        renderer=RendererConfig(
            type=RendererType.STREAM_PLAIN,
            params=PlainStreamRendererConfig(fmt="foobar", datefmt="foobar"),
        ),
        params=AsyncStreamHandlerConfig(use_stderr=False),
    )


@pytest.fixture
def stream_handler(
    mock_renderer: Renderer,
    default_stream_handler_config: HandlerConfig,
) -> AsyncStreamHandler:
    """`AsyncStreamHandler` instance with default configuration."""

    config: HandlerConfig = default_stream_handler_config
    renderer: Renderer = mock_renderer
    processors: list[Processor] = []
    return _stream_handler(config, renderer, processors)


@pytest.fixture
def stream_handler_to_stderr(
    mock_renderer: Renderer,
    default_stream_handler_config: HandlerConfig,
) -> AsyncStreamHandler:
    """`AsyncStreamHandler` instance with stream output to `stderr`."""

    config: HandlerConfig = default_stream_handler_config
    config.params.use_stderr = True  # pyright: ignore[reportAttributeAccessIssue]
    renderer: Renderer = mock_renderer
    processors: list[Processor] = []
    return _stream_handler(config, renderer, processors)


@pytest.fixture
def stream_handler_to_sink(
    mock_renderer: Renderer,
    default_stream_handler_config: HandlerConfig,
) -> AsyncStreamHandler:
    """`AsyncStreamHandler` instance with stream output to `Sink`."""

    config: HandlerConfig = default_stream_handler_config
    renderer: Renderer = mock_renderer
    processors: list[Processor] = []

    handler: AsyncStreamHandler = _stream_handler(config, renderer, processors)
    handler.sink = Sink()
    return handler


# ======================================================================================
#   AsyncFileHandler
# ======================================================================================


@pytest.fixture
def default_file_handler_config(simple_log_file: Path) -> HandlerConfig:
    """Get default (or common) configuration of `AsyncFileHandler`."""

    return HandlerConfig(
        type=HandlerType.FILE,
        renderer=RendererConfig(
            type=RendererType.FILE_JSON,
            params=JSONFileRendererConfig(fmt="foorbar", datefmt="foobar"),
        ),
        params=AsyncFileHandlerConfig(
            filename=str(simple_log_file),
            override_existing=True,
        ),
    )


@pytest.fixture
def file_handler(
    mock_renderer: Renderer,
    default_file_handler_config: HandlerConfig,
) -> AsyncFileHandler:
    """Default `AsyncFileHandler` instance."""

    config: HandlerConfig = default_file_handler_config
    renderer: Renderer = mock_renderer
    processors: list[Processor] = []

    return _file_handler(config, renderer, processors)


@pytest.fixture
def file_handler_without_override(
    mock_renderer: Renderer,
    default_file_handler_config: HandlerConfig,
) -> AsyncFileHandler:
    """`AsyncFileHandler` instance but it does not override existing file."""

    config: HandlerConfig = default_file_handler_config
    config.params.override_existing = False  # pyright: ignore[reportAttributeAccessIssue]
    renderer: Renderer = mock_renderer
    processors: list[Processor] = []

    return _file_handler(config, renderer, processors)


@pytest.fixture
def file_handler_with_existing_file(
    mock_renderer: Renderer,
    temp_log_dir_with_file: tuple[Path, Path],
) -> AsyncFileHandler:
    """`AsyncFileHandler` instance with an existing file in its temporary filepath."""

    _, simple_log_file = temp_log_dir_with_file

    config: HandlerConfig = HandlerConfig(
        type=HandlerType.FILE,
        renderer=RendererConfig(
            type=RendererType.FILE_JSON,
            params=JSONFileRendererConfig(fmt="foorbar", datefmt="foobar"),
        ),
        params=AsyncFileHandlerConfig(
            filename=str(simple_log_file),
            override_existing=False,
        ),
    )
    renderer: Renderer = mock_renderer
    processors: list[Processor] = []

    return _file_handler(config, renderer, processors)


@pytest.fixture
def file_handler_with_sink(
    mock_renderer: Renderer,
    default_file_handler_config: HandlerConfig,
) -> AsyncFileHandler:
    """`AsyncFileHandler` instance with output to `Sink`."""

    config: HandlerConfig = default_file_handler_config
    renderer: Renderer = mock_renderer
    processors: list[Processor] = []

    handler: AsyncFileHandler = _file_handler(config, renderer, processors)
    handler.sink = Sink()
    return handler


# ======================================================================================
#   AsyncRotatingFileHandler
# ======================================================================================


@pytest.fixture
def default_rotating_file_handler_config(simple_log_file: Path) -> HandlerConfig:
    """Get default (or common) configuration of `AsyncRotatingFileHandler`."""

    return HandlerConfig(
        type=HandlerType.ROTATING_FILE,
        renderer=RendererConfig(
            type=RendererType.FILE_PLAIN,
            params=PlainFileRendererConfig(fmt="foobar", datefmt="foobar"),
        ),
        params=AsyncRotatingFileHandlerConfig(
            filename=str(simple_log_file),
            max_bytes=100,  # For easier rotation testing
            backup_count=10,
        ),
    )


@pytest.fixture
def rotating_file_handler(
    mock_renderer: Renderer,
    default_rotating_file_handler_config: HandlerConfig,
) -> AsyncRotatingFileHandler:
    """Default `AsyncRotatingFileHandler` instance."""

    config: HandlerConfig = default_rotating_file_handler_config
    renderer: Renderer = mock_renderer
    processors: list[Processor] = []

    return _rotating_file_handler(config, renderer, processors)


@pytest.fixture
def rotating_file_handler_no_rotation(
    mock_renderer: Renderer,
    default_rotating_file_handler_config: HandlerConfig,
) -> AsyncRotatingFileHandler:
    """`AsyncRotatingFileHandler` instance with no rotation system."""

    config: HandlerConfig = default_rotating_file_handler_config
    config.params.max_bytes = 0  # pyright: ignore[reportAttributeAccessIssue]
    config.params.backup_count = 0  # pyright: ignore[reportAttributeAccessIssue]
    renderer: Renderer = mock_renderer
    processors: list[Processor] = []

    return _rotating_file_handler(config, renderer, processors)

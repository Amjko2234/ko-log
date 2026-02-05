# Ko-Log

An asynchronous, queue-based logging for Python with structured output and zero-dependency configuration.

---

## Table of Contents

1. [What is Ko-Log?](#what-is-ko-log)
2. [Why Ko-Log?](#why-ko-log)
3. [Features](#features)
4. [Installation](#installation)
    - [From Source](#from-source)
    - [Requirements](#requirements)
5. [Quick Start](#quick-start)
6. [Core Concepts](#core-concepts)
    - [Logger](#logger)
    - [Queueing Manager](#queueing-manager)
    - [Handler](#handler)
    - [Processor](#processor)
    - [Renderer](#renderer)
    - [Log Records](#log-records)
7. [Configuration](#configuration)
8. [Handlers](#handlers)
    - [File Handler](#file-handler)
    - [Rotating File Handler](#rotating-file-handler)
    - [Stream Handler](#stream-handler)
    - [Null Handler](#null-handler)
9. [Processors and Renderers](#processors-and-renderers)
    - [Built-in Processors](#built-in-processors)
    - [Built-in Renderers](#built-in-renderers)
    - [Custom Processor Example](#custom-processor-example)
10. [Advanced Usage](#advanced-usage)
    - [Context Binding](#context-binding)
    - [Lifecycle Contexts](#lifecycle-contexts)
    - [Error Logging](#error-handling)
11. [Type Safety](#type-safety)
12. [Error Handling](#error-handling)
    - [Exception Types](#exception-types)
    - [Error Code Format](#error-code-format)
    - [Reproducible Error Examples](#reproducible-error-examples)
    - [Exception Attributes](#exception-attributes)
    - [Error Context](#error-context)
    - [Best Practices](#best-practices)
13. [Testing](#testing)
14. [Philosophy](#philosophy)
15. [For Contributors](#for-contributors)
    - [Development Setup](#development-setup)
    - [Running Tests](#running-tests)
    - [Code Style](#code-style)
16. [License](#license)
17. [Documentation](#documentation)
18. [Acknowledgements](#acknowledgements)

---

## What is Ko-Log?

Ko-Log is an async-first logging framework that decouples log generation from I/O. It uses a queue-based dispatch system to ensure non-blocking writes, supports both sync and async logging APIs, and provides a modular pipeline for formatting and filtering log events.

Unlike traditional loggers that block on every write, Ko-Log pushes records to an async queue and lets a background worker handle I/O. This is what makes it suitable for high-throughput async task workers, and any application where blocking on logs is unacceptable.

## Why Ko-Log?

I experienced the following problems:

- Traditional logging blocks fully-async applications.
- Every `log.info()` waits for disk I/O or network sockets.
- Async code gets polluted with sync logging calls.

So, I needed a logger that:

- Is an **async-first design**, with non-blocking enqueues and background dispatches
- Enforces **structured logging** through context binding, JSON outputs, and support for custom processors
- Is **configuration-driven** by defining loggers, handlers, and processors in JSON/YAML
- Has **flexible routing** with hierarchical logger names, per-handler processors, and level-based filtering
- Supports **strict typing**

## Features

- ✅ **Dual API** - Sync (`logger.info()`) and async (`await logger.ainfo()`) methods.
- ✅ **Queue-Based Dispatch** - Background worker processes logs asynchronously.
- ✅ **Backpressure Policies** - Drop, block, or drop-oldest when queue is full.
- ✅ **Structured Context** - Bind key-value pairs to loggers for correlation.
- ✅ **Processor Pipeline** - Filter by level, add callsite info, serialize exceptions.
- ✅ **Multiple Renderers** - Plain text, JSON, colored console output (via Rich).
- ✅ **Handler Types** - File, rotating file, stream (stdout/stderr), null.
- ✅ **Lifecycle Contexts** - Measure execution time with `info_life()`, `ainfo_life()`.
- ✅ **Type-safe Configuration** - Pydantic models validate JSON/YAML at runtime.

---

## Installation

```bash
pip install git+https://github.com/Amjko2234/ko-log.git
```

### From Source

```bash
git clone https://github.com/Amjko2234/ko-log.git
cd ko-log
pip install -e .
```

### Requirements

- Python >= 3.14
- [`aiofiles`](https://pypi.org/project/aiofiles/), [`dotenv`](https://pypi.org/project/python-dotenv/), [`pydantic`](https://docs.pydantic.dev/latest/), [`rich`](https://rich.readthedocs.io/en/latest/introduction.html)

---

## Quick Start

```py
import asyncio
from pathlib import Path
from ko_log import LoggerFactory, QueueManager
from ko_log.models import (
    LoggingSystemConfig, LoggerConfig, QueueConfig,
    HandlerConfig, HandlerType, RendererConfig, RendererType,
    PlainStreamRendererConfig, AsyncStreamHandlerConfig,
)

async def main():
    # 1. Configure queue manager
    queue_config = QueueConfig(
        max_queue_size=10_000,
        backpressure_policy="block",
        drain_timeout=5.0,
    )
    queue_manager = QueueManager(config=queue_config)
    await queue_manager.start()

    # 2. Configure logging system
    system_config = LoggingSystemConfig(
        loggers=[
            LoggerConfig(
                name="app",
                level="INFO",
                handlers=[
                    HandlerConfig(
                        type=HandlerType.STREAM,
                        renderer=RendererConfig(
                            type=RendererType.STREAM_PLAIN,
                            params=PlainStreamRendererConfig(
                                fmt="[%(asctime)s] [%(level)-8s] [%(name)s]: %(event)s",
                                datefmt="%Y-%m-%d %H:%M:%S",
                            ),
                        ),
                        params=AsyncStreamHandlerConfig(use_stderr=False),
                    ),
                ],
            ),
        ],
    )

    # 3. Create logger factory
    factory = LoggerFactory(
        config=system_config,
        queue_manager=queue_manager,
        log_path=Path("./factory.log"),
    )

    # 4. Get logger and use it
    logger = factory.get_logger("app")
    
    # Synchronous logging
    logger.info("Application started", version="1.0.0")
    
    # Asynchronous logging
    await logger.ainfo("Processing request", user_id=123)
    
    # Context binding
    bound_logger = logger.bind(service="auth", env="prod")
    bound_logger.warning("Rate limit exceeded", ip="192.168.1.1")
    
    # Lifecycle tracking
    async with logger.ainfo_life("Database migration"):
        await asyncio.sleep(0.5)  # Simulated work
    
    # 5. Cleanup
    await queue_manager.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
```

**Output:**

```text
[2024-01-01 12:00:00] [INFO    ] [app]: Application started
[2024-01-01 12:00:00] [INFO    ] [app]: Processing request
[2024-01-01 12:00:00] [WARNING ] [app]: Rate limit exceeded
[2024-01-01 12:00:00] [INFO    ] [app]: Begin: Database migration
[2024-01-01 12:00:01] [INFO    ] [app]: End (0.50): Database migration
```

---

## Core Concepts

### Logger

A `BoundLoggerBase` instance that carries context and provides logging methods. Loggers are immutable; but, calling `bind()` returns a new logger with merged context.

### Queueing Manager

`QueueManager`. The central dispatch system. It receives `LogRecord` objects from loggers and routes them to registered handlers. It runs a background worker that processes the queue asynchronously.

### Handler

Responsible for writing formatted messages to a destination (file, stdout, stderr). Each handler has:

- A **renderer** as the formatter of the log events.
- A **processor pipeline** as the filterer/transformer of the events before rendering.

Learn more about [handlers here](#handlers)

### Processor

A callable that transforms `EventDict`. Examples include:

- `add_callsite_params`: Adds filename, line number, function name.

Learn more about [processors here](#processors-and-renderers).

### Renderer

Final formatting step. Converts `EventDict` to a string. Types include:

- `JSONRenderer`: Structured JSON output with context.

Learn more about [renderers here](#processors-and-renderers)

### Log Records

`LogRecord`. Immutable data structure containing:

- `logger_name`: For handler routing.
- `event`: Pre-processed log message.
- `timestamp`: Time of creation.
- `event_dict`: Complete structured data (level, context, callsite, etc.).

---

## Configuration

Ko-Log uses **Pydantic models** for type-safe configuration. You can define configs in Python or load from JSON/YAML.

> However, I (Amjko2234) highly discourage configuring in Python, similar to the example below, as not only it immediately populates your imports (if you are strictly typed) but it will force you to either place a configuration file (.py) inside your infrastructure codebase or place a python file inside your configuration directory.
>
> Although... The final judgement is still your call, you know your code better than I.

<details open>
    <summary>From JSON</summary>

```json
{
  "loggers": [
    {
      "name": "root",
      "level": "DEBUG",
      "handlers": [
        {
          "type": "file",
          "params": {
            "filename": "/var/log/app.log",
            "mode": "wb",
            "encoding": "utf-8",
            "override_existing": false
          },
          "renderer": {
            "type": "file_json",
            "params": {
              "fmt": "%(asctime)s - %(level)s - %(event)s",
              "datefmt": "%Y-%m-%d %H:%M:%S",
              "indentation": 2
            }
          },
          "processors": [
            {
              "type": "add_callsite_params",
              "params": {
                "parameters": ["filename", "lineno", "funcName"]
              }
            },
            {
              "type": "filter_by_level",
              "params": {
                "min_level": "INFO"
              }
            }
          ]
        }
      ],
      "context": {
        "app": "myapp",
        "env": "production"
      }
    }
  ],
  "default_level": "INFO"
}
```
    
</details>

Then load and use:

```py
import json
from ko_log import LoggerFactory, QueueManager

# Read JSON config file
with open("config.json") as f:
    config = json.load(f)

# Setup queueing manager
queue_manager = QueueManager.from_json({"max_queue_size": 10000})
await queue_manager.start()

# Create factory then logger from config
factory = LoggerFactory.from_json(
    config=config,
    queue_manager=queue_manager,
    log_path="./factory.log",
)
logger = factory.get_logger("root")
```

---

## Handlers

### File Handler

Writes to a file. Lazy-opens on first write.

<details open>
    <summary>Configuration through JSON</summary>
    
```json
{
    "type": "file",
    "params": {
        "filename": "/var/log/app.log",
        "mode": "wb",
        "encoding": "utf-8",
        "override_existing": true
    },
    ...
}
```

</details>

<details>
    <summary>Configuration through Python</summary>

```py
HandlerConfig(
    type=HandlerType.FILE,
    params=AsyncFileHandlerConfig(
        filename="/var/log/app.log",
        mode="wb",
        encoding="utf-8",
        override_existing=True,
    ),
    ...
)
```

</details>

### Rotating File Handler

Rotates logs based on file size or time.

<details open>
    <summary>Configuration through JSON</summary>

```json
{
    "type": "rotating_file",
    "params": {
        "filename": "/var/log/app.log",
        "max_bytes": 10485760,
        "backup_count": 5,
        "rotation_interval": null
    },
    ...
}
```

</details>

<details>
    <summary>Configuration through Python</summary>

```py
HandlerConfig(
    type=HandlerType.ROTATING_FILE,
    params=AsyncRotatingFileHandlerConfig(
        filename="/var/log/app.log",
        max_bytes=10_485_760,  # 10 MB
        backup_count=5,
        rotation_interval=None,
    ),
    ...
)
```

</details>

### Stream Handler

Writes to stdout/stderr.

<details open>
    <summary>Configuration through JSON</summary>

```json
{
    "type": "stream",
    "params": {
        "use_stderr": false
    },
    ...
}
```

</details>

<details>
    <summary>Configuration through Python</summary>

```py
HandlerConfig(
    type=HandlerType.STREAM,
    params=AsyncStreamHandlerConfig(use_stderr=False),
    ...
)
```

</details>

### Null Handler

Discards all logs (unless a `Sink` is attached). Useful only for testing.

<details open>
    <summary>Configuration through JSON</summary>

```json
{
    "type": "null",
    ...
}
```

</details>

<details>
    <summary>Configuration through Python</summary>

```py
HandlerConfig(
    type=HandlerType.NULL,
    ...
)
```

</details>

---

## Processors and Renderers

### Built-in Processors

| Processor | Purpose |
| -------- | ------- |
| `add_callsite_params` | Adds `filename`, `lineno`, `funcName`, `module`, `pathname` |
| `add_context_defaults` | Merges default key-value pairs into context |
| `dict_tracebacks` | Converts `exc_info` to structured dict with traceback frames |
| `filter_by_level` | Drops logs below `min_level` (raises `DropLog`) |
| `filter_keys` | Removes specified keys from event dict |
| `filter_markup` | Strips `Rich` markup tags from messages |

### Built-in Renderers

| Renderer | Output |
| -------- | ------- |
| `PlainRenderer` | Percent-style formatted output: `%(asctime)s - %(level)s - %(event)s` |
| `JSONRenderer` | Formatted message + JSON context block |
| `ColoredRenderer` | ANSI-colored output via `Rich` (for terminals) |

*In future updates, more processors and renderers will be added.*

### Custom Processor Example

```py
from ko_log.types import EventDict, Processor

# Configure the processor
def add_request_id(config: CustomConfig) -> Processor:
    request_id = config.params.request_id
    
    # Define the processor
    def processor(event_dict: EventDict) -> EventDict:
        event_dict.setdefault("request_id", request_id)
        return event_dict
    
    return processor
```

Register it in `processor_map` and use in config.

---

## Advanced Usage

### Context Binding

Bind new context to loggers:

```py
logger = factory.get_logger("app")

# Bind immutable context
api_logger = logger.bind(service="api", version="v1")
api_logger.info("Request received", endpoint="/users")

# Chain bindings
request_logger = api_logger.bind(request_id="abc123")
request_logger.info("Processing", user_id=456)
```

### Lifecycle Contexts

Explicitly state a context lifecycle start/end in logs:

```py
# Sync
with logger.info_life("Database query", table="users") as log:
    # Logs "Begin: Database query"
    do_work()
    log.info("Did work")
    # Logs "End (0.15): Database query"

# Async
async with logger.ainfo_life("API call", endpoint="/data") as log:
    await fetch_data()
    await log.ainfo("Data fetched")
```

### Error Logging with Tracebacks

Support for catching exception information and tracebacks:

```py
try:
    risky_operation()
except ValueError:
    logger.error("Operation failed", operation="risky")
    # Automatically captures sys.exc_info() if `dict_tracebacks` processor is enabled
```

---

## Type Safety

Ko-Log is **fully typed** with `Pydantic` models:

```py
from ko_log.models import LoggerConfig, HandlerConfig
from pydantic import ValidationError

try:
    config = LoggerConfig(
        name="test",
        level="INVALID",  # ❌ Validation error
    )
except ValidationError as e:
    print(e)
```

All public APIs have type hints. Use `mypy` or `pyright` for static analysis:

```bash
mypy your_app.py
pyright your_app.py
```

---

## Error Handling

Ko-Log defines custom exceptions with structured error code for diagnostics and monitoring. All exceptions inherit `_BaseException` and include machine-readable error codes.

### Exception Types

| Exception | Raised When | Common Causes |
| --------- | ----------- | ------------- |
| `AlConfigurationError` | Configuration validation fails | Missing logger in config, invalid enum values, malformed JSON |
| `AlLoggerCreationError` | Logger instantiation fails | Handler creation error, processor registration failure, invalid context |
| `AlLoggerError` | Runtime logging operation fails | Processor chain error, invalid event dict, serialization failure |
| `AlHandlerError` | Handler I/O operations fail | File not writable, disk full, network timeout, permission denied |
| `AlProcessorError` | Processor execution fails | Unknown processor type, invalid transformation, missing required field |
| `AlQueueManagerError` | Queue dispatch or routing fails | Handler not registered, dispatch timeout, worker crash |

### Error Code Format

```txt
LAYER::Service::CATEGORY::SEVERITY[::RECOVERABLE]
```

Example: `HANDLER::LoggerFactory::CONFIGURATION::ERROR`

- **LAYER**: Where the error occurred (i.e., `PROCESSOR`, `HANDLER`)
- **Service**: Component name (i.e., `LoggerFactory`, `QueueManager`)
- **CATEGORY**: Error type (i.e., `IO`, `CONFIGURATION`)
- **SEVERITY**: `WARNING`, `ERROR`, or `CRITICAL`
- **RECOVERABLE** *(optional)*: Indicates if operation can be retried

### Reproducible Error Examples

#### Configuration Error

```py
try:
    logger = factory.get_logger("non_existent")
except AlConfigurationError as e:
    print(e.msg)  # "Logger `non_existent` not found"
    print(e.code)  # "CONFIGURATION::LoggerFactory::VALIDATION::ERROR"
```

#### Handler I/O Error

```py
try:
    handler = AsyncFileHandler(
        renderer=renderer,
        processors=[],
        filename="/read-only/path/app.log",
        mode="wb",
        encoding="utf-8",
        override_existing=True,
    )
    handler._write_sync("Test message")
except AlHandlerError as e:
    print(e.msg)  # "Failed to open the file at path `/temp/read-only.log`"
    print(e.code)  # "HANDLER::AsyncFileHandler::IO::ERROR"
    # Log to fallback handler, send alert, etc.
```

#### Processor Error

```py
try:
    factory.get_logger_from_json({
        "name": "app",
        "processors": [{"type": "unknown_processor"}]
    })
except AlLoggerCreationError as e:
    print(e.msg)  # "Failed to create logger `root`"
    print(e.__cause__)  # AlProcessorError: Unknown processor type: unknown_processor
```

#### Queue Manager Error

```py
try:
    queue_manager.push_sync(record)
except AlQueueManagerError as e:
    print(e.msg)  # "Failed to synchronously emit log message of logger `root` to handlers `[<$AsyncNullHandler>]`"
    print(e.code)  # "DISPATCH::QueueManager::ROUTING::ERROR"
```

### Exception Attributes

All Ko-Log exceptions expose:

```py
exception.msg          # Human-readable message
exception.msg_code     # Message + error code
exception.code         # Machine-readable error code
exception.user_msg     # Optional user-facing message
exception.recoverable  # Boolean: can retry?
exception.__cause__    # Underlying exception (if any)
```

### Error Context

Exceptions can carry structured context for debugging:

```py
try:
    processor(event_dict)
except AlProcessorError as e:
    print(repr(e))  # Shows JSON context
    # "PROCESSOR::ProcessorName::FORMATTING::ERROR:
    # {
    #   "event_dict": {...},
    #   "processor_type": "filter_by_level",
    #   "timestamp": "2024-01-01T12:00:00Z"
    # }"
```

### Best Practices

1. **Catch specific exceptions** at API boundaries:

    ```py
    try:
        logger = factory.get_logger("app")
    except AlConfigurationError:
        # Use fallback logger
        logger = factory.get_logger("root")
    ```

2. **Log exceptions with context**:

    ```py
    try:
        risky_operation()
    except AlHandlerError as e:
        fallback_logger.error(
            "Handler failed", error_code=e.code, path=e._ctx.get("path")
        )
    ```

3. **Use error codes** for monitoring:

    ```py
    except AlQueueManagerError as e:
        if "CRITICAL" in e.code:
            send_alert(e.msg_code)
    ```

4. **Check recoverability**:

    ```py
    except AlHandlerError as e:
        if e.recoverable:
            retry_with_backoff()
        else:
            switch_to_fallback_handler()
    ```

---

## Testing

Ko-Log provides a `Sink` mechanism for capturing output in tests:

```py
import pytest
from collections.abc import Generator
from ko_log import Sink, QueueManager, LoggerFactory

@pytest.fixture
def logger_with_sink(
    queue_manager: QueueManager, factory: LoggerFactory
) -> Generator[tuple[LoggerFactory, Sink], None]:

    # Get a logger and attach the `Sink` into it's handler
    logger = factory.get_logger("test")
    sink = Sink()
    queue_manager.add_sink(logger_name="test", sink=sink)

    yield logger, sink
    
    # Necessary if it is intended to use the handler's I/O
    queue_manager.remove_sink(logger_name="test")

def test_logging(logger_with_sink: tuple[LoggerFactory, Sink]):
    logger, sink = logger_with_sink
    logger.info("Test message")
    
    # `Sink` captures all outputs
    assert len(sink.events) == 1
    assert "Test message" in sink.events[0]
```

---

## Philosophy

This is a personal tool built for specific use. It follows these simple principles:

1. **Async by Default** - Logging should never block your application
2. **Configuration Over Code** - Define logging behavior in JSON/YAML, not Python
3. **Structured Output** - Every log is a structured event, not just a string
4. **Processor Pipelines** - Composable transformations over monolithic formatters
5. **Type Safety First** - Validate configs at runtime with Pydantic, catch errors early
6. **Pythonic Patterns** - context managers, protocols, type hints

---

## For Contributors

While this is primarily a personal project, I'm open to:

- Bug reports with reproducible examples
- Documentation improvements
- Performance optimizations
- Feature requests (with clear use cases)

*If you find it useful, that's reward enough.* ✨

### Development Setup

```bash
git clone https://github.com/Amjko2234/ko-log.git
cd ko-log
python -m venv .venv
source .venv/bin/active # or .venv/Scripts/Activate on Windows

pip install -e ".[dev]"
```

### Running Tests

```bash
pytest tests/ -vv
```

### Code Style

- Formatter: `black`, `isort`
- Linter: `ruff`
- Type Checker: `basedpyright`

---

## License

MIT License. See [LICENSE](LICENSE.rst) for details.

---

## Documentation

- [How to Create Custom Processors](docs/custom-processor.md)
- [How to Create Custom Renderers](docs/custom-renderer.md)
- [How to Create Custom Handlers](docs/custom-handler.md)
- [How to Extend Log Records](docs/extend-log-records.md)
- [Testing Guide](docs/testing-guide.md)
- [Architecture Overview](docs/architecture.md)

---

## Acknowledgements

Creation of Ko-Log was inspired by:

- [structlog](https://github.com/hynek/structlog): Structured logging with processor pipelines
- [loguru](https://github.com/Delgan/loguru): Simplicity and async support
- Python's [asyncio](https://docs.python.org/3/library/asyncio.html) and [logging](https://docs.python.org/3/library/logging.html) stdlib modules

---

*Built for practical use, shared in the case it helps others build better software.* 🙂

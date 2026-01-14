# How to Test Loggers

Use `Sink` to capture log output in unit tests without writing to disk/stdout.

## Basic Test with Sink

```py
import pytest
import pytest_asyncio
from ko_log import Sink, QueueManager, LoggerFactory, BoundLoggerBase
from ko_log.models import QueueConfig, LoggingSystemConfig

@pytest_asyncio.fixture
async def logger_with_sink():
    # Setup queue manager
    queue_manager = QueueManager(QueueConfig())
    await queue_manager.start()
    
    # Create logger
    config = LoggingSystemConfig(loggers=[...])
    factory = LoggerFactory(config, queue_manager, log_path="./test.log")
    logger = factory.get_logger("test")
    
    # Attach sink
    sink = Sink()
    queue_manager.add_sink(logger_name="test", sink=sink)
    
    yield logger, sink
    
    # Cleanup
    await queue_manager.shutdown()

@pytest.mark.asyncio
async def test_logging(logger_with_sink: tuple[BoundLoggerBase, Sink]):
    logger, sink = logger_with_sink
    
    await logger.ainfo("Test message", user_id=123)
    await asyncio.sleep(0.1)  # Wait for async dispatch
    
    assert len(sink.events) == 1
    assert "Test message" in sink.events[0]
    assert "user_id" in sink.events[0] or "123" in sink.events[0]
```

## Testing Sync Logs

```py
def test_sync_logging(logger_with_sink: tuple[BoundLoggerBase, Sink]):
    logger, sink = logger_with_sink
    
    logger.info("Sync message")
    
    # Sync logs go directly to handler
    assert len(sink.events) == 1
    assert "Sync message" in sink.events[0]
```

## Testing Log Levels

```py
@pytest.mark.asyncio
async def test_filter_by_level(logger_with_sink: tuple[BoundLoggerBase, Sink]):
    logger, sink = logger_with_sink
    
    # Assuming min_level=INFO in config
    logger.debug("Debug message")  # Filtered out
    await logger.ainfo("Info message")
    
    await asyncio.sleep(0.1)
    
    assert len(sink.events) == 1
    assert "Info message" in sink.events[0]
```

## Testing Context Binding

```py
def test_context_binding(logger_with_sink: tuple[BoundLoggerBase, Sink]):
    logger, sink = logger_with_sink
    
    bound_logger = logger.bind(request_id="abc123")
    bound_logger.info("Test")
    
    assert "abc123" in sink.events[0]
```

## Testing Error Handling

```py
def test_exception_logging(logger_with_sink: tuple[BoundLoggerBase, Sink]):
    logger, sink = logger_with_sink
    
    try:
        raise ValueError("Test error")
    except ValueError:
        logger.error("Operation failed")
    
    # If dict_tracebacks processor is enabled
    assert "Operation failed" in sink.events[0]
    # Check for exception data if processor is configured
```

## Key Points

- Always `await asyncio.sleep()` after async logs to let queue process (in tests only).
- Use `queue_manager.add_sink()` to attach sink to specific loggers.
- Sink captures formatted output (after renderer), not raw `EventDict`.
- For integration tests, use real handlers but point to temp files.

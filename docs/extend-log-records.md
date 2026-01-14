# How to Extend Log Records

Add custom fields to `EventDict` or `LogRecord` for specialized handlers.

## Use Case: Add Trace ID to All Logs

### Option 1: Via Processor (Recommended)

```py
from ko_log.types import EventDict, Processor

def add_trace_id(config) -> Processor:
    """Inject trace ID from context or generate one."""

    import uuid
    
    def processor(event_dict: EventDict) -> EventDict:
        context = event_dict.get("context", {})
        if "trace_id" not in context:
            context["trace_id"] = str(uuid.uuid4())
        event_dict["context"] = context
        return event_dict
    
    return processor
```

### Option 2: Via Logger Binding

```py
import uuid
from ko_log import BoundLoggerBase

logger = factory.get_logger("app")
request_logger = logger.bind(trace_id=str(uuid.uuid4()))
request_logger.info("Processing request")
```

## Use Case: Add Extra Metadata to LogRecord

If you need fields **outside** `EventDict` (e.g., for custom handler routing):

### Step 1: Extend LogRecord

```py
# my_records.py
from dataclasses import dataclass
from ko_log.record import LogRecord

@dataclass(slots=True, frozen=True)
class ExtendedLogRecord(LogRecord):
    priority: int = 0  # Custom field
    tags: list[str] = None  # Custom field
```

### Step 2: Modify QueueManager (Advanced)

This requires subclassing `QueueManager` and overriding `_dispatch()` to create your custom record type. **Not recommended** unless you have specific routing needs.

### Better Approach: Use Processors

```py
def add_priority(config) -> Processor:
    def processor(event_dict: EventDict) -> EventDict:
        level = event_dict.get("level", "INFO")
        priority_map = {"DEBUG": 1, "INFO": 2, "WARNING": 3, "ERROR": 4}
        event_dict["priority"] = priority_map.get(level, 0)
        return event_dict
    return processor
```

Your custom handler can then access `event_dict["priority"]`.

## Key Points

- Prefer processors for adding fields (cleaner, more composable).
- Use logger binding for per-request context.
- Avoid modifying `LogRecord` unless building custom dispatch logic.

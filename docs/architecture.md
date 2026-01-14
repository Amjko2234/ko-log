# Ko-Log Architecture

High-level flow of a log message through the system.

## Components

```text
[Logger] --> [Queueing Manager] --> [Handler] --> [Destination]
          ↑                      ↑
          |                      |
     [Processors]    [Processors -> Renderer]
```

## Flow

### 1. Log Creation

```py
logger.info("User login", user_id=123)
```

**What happens:**

- `BoundLoggerBase._sync_log()` creates `EventDict`:

```py
  {
    "event": "User login",
    "level": "INFO",
    "name": "app",
    "timestamp": datetime.now(),
    "context": {"user_id": 123},
    "filename": "main.py",
    "lineno": "42",
    # ... callsite info
    # ... exc_info (if set or detected)
  }
```

### 2. Logger-Level Processing

- Run logger's processors (if any)
- Create `LogRecord` from `EventDict`
- Send to `QueueManager`

### 3. Queue Dispatch

**Sync path:**

```text
logger.info() -> QueueManager.push_sync() -> Handler.emit_sync()
```

**Async path:**

```text
await logger.ainfo() -> QueueManager.enqueue() -> Queue -> Worker -> Handler.emit_async()
```

### 4. Handler Processing

- Run handler's processors (filters, enrichers)
- Pass `EventDict` to renderer
- Renderer returns formatted `str`
- Write to destination (file, stdout, HTTP, etc.)

## Key Decisions

**Why queue-based?**

- Decouples log generation from I/O
- Non-blocking writes in async code
- Backpressure management

**Why processor pipelines?**

- Composable transformations
- Reusable across handlers
- Easy to test in isolation

**Why separate renderer from handler?**

- Handler = destination logic (where to write)
- Renderer = format logic (how to format)
- Mix and match (e.g., JSON to file, JSON to HTTP)

## Threading Model

- **Sync logs**: Direct write to handler (thread-safe via locks)
- **Async logs**: Enqueue → background worker → handler
- **QueueManager worker**: Single async task (can be scaled in future)
- **Handler locks**: Per-handler async/sync locks for concurrent safety

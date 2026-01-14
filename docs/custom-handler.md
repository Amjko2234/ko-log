# How to Create a Custom Handler

Handlers write formatted messages to destinations. Use cases:

- Send logs to external services (Sentry, Elasticsearch, Datadog)
- Write to databases
- Custom protocols (gRPC, WebSocket)

## Step 1: Subclass `Handler`

```py
# my_handlers.py
import asyncio
import httpx
from typing import override
from ko_log.handlers.base import Handler
from ko_log.types import Processor, Renderer

class HTTPHandler(Handler):
    """POST logs to an HTTP endpoint."""
    
    def __init__(
        self,
        renderer: Renderer,
        processors: list[Processor],
        *,
        url: str,
        headers: dict[str, str] | None = None,
    ):
        super().__init__(renderer, processors)
        self._url = url
        self._headers = headers or {}
        self._client: httpx.AsyncClient | None = None
    
    @override
    def _write_sync(self, msg: str) -> None:
        """Sync writes not supported for HTTP handler."""

        raise NotImplementedError("Use async logging with HTTPHandler")
    
    @override
    async def _write_async(self, msg: str) -> None:
        if self._client is None:
            self._client = httpx.AsyncClient()
        
        try:
            response = await self._client.post(
                self._url,
                json={"message": msg},
                headers=self._headers,
                timeout=5.0,
            )
            response.raise_for_status()
        except httpx.HTTPError as e:
            # Handle errors (log to stderr, metrics, etc.)
            print(f"HTTP handler error: {e}")
    
    @override
    async def flush(self) -> None:
        """No-op for HTTP handler."""
        pass
    
    @override
    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None
```

## Step 2: Define Config Model

```py
# In ko_log/models/handlers.py or separate file
from typing import Literal
from pydantic import BaseModel

class HTTPHandlerConfig(BaseModel):
    type: Literal["http"] = "http"
    url: str
    headers: dict[str, str] = {}
```

## Step 3: Create Factory Function

```py
from ko_log.models import HandlerConfig
from ko_log.types import Processor, Renderer
from my_handlers import HTTPHandler

def http_handler(
    config: HandlerConfig,
    renderer: Renderer,
    processors: list[Processor],
) -> HTTPHandler:
    if config.params.type != "http":
        raise ValueError("Invalid config for HTTP handler")
    
    return HTTPHandler(
        renderer,
        processors,
        url=config.params.url,
        headers=config.params.headers,
    )
```

## Step 4: Register Handler

```py
# In ko_log/handlers/handlers.py or app init
from ko_log.handlers.handlers import handler_map
from my_handlers import http_handler

handler_map["http"] = http_handler
```

## Step 5: Use in Config

```json
{
  "loggers": [
    {
      "name": "app",
      "handlers": [
        {
          "type": "http",
          "params": {
            "url": "https://logs.example.com/ingest",
            "headers": {
              "Authorization": "Bearer token"
            }
          },
          "renderer": {
            "type": "file_json",
            "params": {...}
          }
        }
      ]
    }
  ]
}
```

## Key Points

- Implement both `_write_sync()` and `_write_async()`.
- Call `super().__init__(renderer, processors)` to initialize base.
- Handler receives **formatted strings** from renderer, not raw `EventDict`.
- Use `self.sink` for testing (check if `self.sink is not None`).

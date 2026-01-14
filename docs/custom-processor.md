# How to Create a Custom Processor

Processors transform `EventDict` before it reaches the renderer. Use cases:

- Add computed fields (e.g., request duration, hostname)
- Filter sensitive data (e.g., mask passwords)
- Enrich context (e.g., inject trace IDs)

## Step 1: Define Config Model

```py
# my_processors.py
from typing import Literal
from pydantic import BaseModel
from ko_log.models.processors import _ProcessorParamsConfig

class AddHostnameConfig(_ProcessorParamsConfig):
    type: Literal["add_hostname"] = "add_hostname"
    hostname: str  # Static or fetch from environment
```

## Step 2: Implement Processor Factory

```py
import socket
from ko_log.exceptions import AlConfigurationError
from ko_log.types import EventDict, Processor
from ko_log.models import ProcessorConfig

def add_hostname(config: ProcessorConfig) -> Processor:
    """Add hostname to every log event."""

    if config.params.type != "add_hostname":
        raise ValueError("Invalid config for add_hostname")
        # or raise AlConfigurationError(...)
    
    hostname = config.params.hostname or socket.gethostname()
    
    def processor(event_dict: EventDict) -> EventDict:
        event_dict.setdefault("hostname", hostname)
        return event_dict
    
    return processor
```

## Step 3: Register in Processor Map

```py
# In ko_log/maps.py or your app initialization
from ko_log.maps import processor_map
from ko_log.models.processors import ProcessorType
from my_processors import add_hostname

# Add to enum (in production, extend ProcessorType)
# For now, we'll use dynamic registration
processor_map["add_hostname"] = add_hostname
```

## Step 4: Use in Config

```json
{
  "loggers": [
    {
      "name": "app",
      "handlers": [
        {
          "type": "stream",
          "processors": [
            {
              "type": "add_hostname",
              "params": {
                "hostname": "prod-server-01"
              }
            }
          ],
          "renderer": {...}
        }
      ]
    }
  ]
}
```

## Advanced: Filtering Processor

```py
from ko_log.processors import DropLog

def filter_sensitive_keys(config: ProcessorConfig) -> Processor:
    sensitive = config.params.keys_to_mask
    
    def processor(event_dict: EventDict) -> EventDict:
        context = event_dict.get("context", {})
        for key in sensitive:
            if key in context:
                context[key] = "***REDACTED***"
        return event_dict
    
    return processor
```

## Key Points

- Processors are called **before** renderers.
- Raise `DropLog` to prevent a log from being written.
- Processors at handler-level override logger-level processors.

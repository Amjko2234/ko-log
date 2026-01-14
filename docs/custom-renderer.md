# How to Create a Custom Renderer

Renderers convert `EventDict` to formatted strings. Use cases:

- Custom formats (CSV, MessagePack, Protobuf)
- Template-based rendering (Jinja2)
- Performance-critical serialization

## Step 1: Implement Renderer Callable

```py
# my_renderers.py
import csv
from io import StringIO
from ko_log.types import EventDict, Renderer

def csv_renderer(config) -> Renderer:
    """Render logs as CSV lines."""

    fields = config.params.fields  # ["timestamp", "level", "event"]
    
    def render(event_dict: EventDict) -> str:
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
        writer.writerow(event_dict)
        return output.getvalue().strip()
    
    return render
```

## Step 2: Define Config Model

```py
from typing import Literal
from pydantic import BaseModel

class CSVRendererConfig(BaseModel):
    type: Literal["csv"] = "csv"
    fields: list[str] = ["timestamp", "level", "event"]
    delimiter: str = ","
```

## Step 3: Register Renderer

```py
from ko_log.maps import renderer_map
from my_renderers import csv_renderer

renderer_map["csv"] = csv_renderer
```

## Step 4: Use in Config

```json
{
  "handlers": [
    {
      "type": "file",
      "renderer": {
        "type": "csv",
        "params": {
          "fields": ["timestamp", "level", "event", "context"],
          "delimiter": "|"
        }
      }
    }
  ]
}
```

## Advanced: Level-Aware Renderer

```py
from ko_log.processors import DropLog
from ko_log.levels import check_level, LogLevel

def filtered_json_renderer(config) -> Renderer:
    import json
    min_level = config.params.min_level
    
    def render(event_dict: EventDict) -> str:
        level = event_dict.get("level", "INFO")
        if check_level(level) < check_level(min_level):
            raise DropLog  # Don't render this log
        
        return json.dumps(event_dict, default=str)
    
    return render
```

## Key Points

- Renderers run **after** processors.
- Return a `str` (will have `\n` appended by handler).
- Raise `DropLog` to skip rendering (handler won't write).
- Access `event_dict["timestamp"]` (already added by logger).

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from .types import EventDict

# =====================================================================================
#   Record
# =====================================================================================


@dataclass(slots=True, frozen=True)
class LogRecord:
    """
    Minimal log record for queue-based dispatch.
    Contains pre-formatted message and routing metadata.
    All forms of formatting and processing is handled by `structlog.Processors`.
    """

    logger_name: str
    """Logger name for handler routing."""
    event: str
    """Pre-formatted log message."""
    timestamp: datetime
    """Time of creation."""
    event_dict: EventDict
    """Complete pre-formatted list of events from `structlog.Processors`."""

    @classmethod
    def create(cls, event_dict: EventDict) -> LogRecord:
        """Factory method for creating log records."""

        return cls(
            logger_name=event_dict.get("name", "notset"),
            event=event_dict.get("event", ""),
            timestamp=event_dict.get("timestamp", datetime.now(tz=timezone.utc)),
            event_dict=event_dict,
        )

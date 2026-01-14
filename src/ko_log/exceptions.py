import json
from datetime import datetime, timezone
from typing import Literal, TypeAlias, override

# ======================================================================================
#   Models
# ======================================================================================

# fmt: off
Layer: TypeAlias = Literal[ # Literals based from: "Where did it happen?"
    # Creation & Validation
    "CONFIGURATION",    # Config validation
    "FACTORY",          # Instance factory
    
    # Manager
    "DISPATCH",         # Internal dispatcher to IOs
                           
    # Formatting
    "HANDLER",          # I/O implementation
    "PROCESSOR",        # Data formatters

    # Generic
    "UNKNOWN",
]
"""System layers for error categorization."""

Category: TypeAlias = Literal[ # Literals based from: "What type of problem?"
    # Data & Processing
    "CONFIGURATION",    # Generic data structure invalidation
    "FORMATTING",       # Transforming data
    "ROUTING",          # Where data goes
    "VALIDATION",       # Data validation

    # Input/Output
    "IO",               # Disk input and outputs

    # Generic
    "UNEXPECTED",       # Unexpected errors (should catch all)
    "UNKNOWN",          
]
"""Error categories for error classification."""

Severity: TypeAlias = Literal["WARNING", "ERROR", "CRITICAL"]
"""Error severity levels."""
# fmt: on


# ======================================================================================
#   Base
# ======================================================================================


class _BaseException(BaseException):
    msg: str
    default_layer: Layer = "UNKNOWN"
    default_service: str = "unknown"
    default_category: Category = "UNKNOWN"
    default_severity: Severity = "ERROR"
    recoverable: bool | None = None

    def __init__(
        self,
        message: str,
        /,
        user_message: str | None = None,
        description: str | None = None,
        document_url: str | None = None,
        cause: BaseException | None = None,
        *,
        context: dict[str, object] | None = None,
        service: str | None = None,
        layer: Layer | None = None,
        category: Category | None = None,
        severity: Severity | None = None,
        recoverable: bool | None = None,
    ) -> None:
        self.msg = message.strip()
        self.user_msg: str = user_message.strip() if user_message else ""

        layer_: Layer = layer or self.default_layer
        # Don't `upper()` so camelNaming doesn't turn into UPPERNAMING, which is
        # difficult to read
        service_: str = service.strip() if service else self.default_service
        category_: Category = category or self.default_category
        severity_: Severity = severity or self.default_severity
        self.code: str = self._generate_code(
            layer=layer_,
            service=service_,
            category=category_,
            severity=severity_,
        )
        self.msg_code: str = f"{self.msg}\n>> {self.code}"

        # Recoverability (value upon call has overwriting priority)
        if isinstance(recoverable, bool):
            self.recoverable = recoverable
        elif self.recoverable is None:
            self.recoverable = False

        # Context
        self.__cause__: BaseException | None = cause
        self._ctx: dict[str, object] | None = context
        self._tstamp: datetime = datetime.now(tz=timezone.utc)

        super().__init__(self.msg_code)

    @override
    def __str__(self) -> str:
        return f"{self.msg_code}"

    @override
    def __repr__(self) -> str:
        json_context: str = json.dumps(obj=self._ctx, indent=2, default=str)
        return f"{self.msg_code}:\n{json_context}"

    def _generate_code(
        self,
        layer: str,
        service: str,
        category: str,
        severity: str,
    ) -> str:
        code: str = f"{layer}::{service}::{category}::{severity}"
        if self.recoverable:
            return f"{code}::RECOVERABLE"
        else:
            return code


# ======================================================================================
#   Models
# ======================================================================================


class AlConfigurationError(_BaseException):
    """Errors during validation of configuration or mismatch of configuration type."""

    default_layer: Layer = "CONFIGURATION"
    default_category: Category = "VALIDATION"
    default_severity: Severity = "ERROR"
    recoverable: bool | None = False


class AlLoggerCreationError(_BaseException):
    """General errors from the logger."""

    default_layer: Layer = "FACTORY"
    default_category: Category = "CONFIGURATION"
    default_severity: Severity = "ERROR"
    recoverable: bool | None = False


class AlLoggerError(_BaseException):
    """Problem trying to log."""

    default_layer: Layer = "PROCESSOR"
    default_category: Category = "CONFIGURATION"
    default_severity: Severity = "ERROR"
    recoverable: bool | None = False


class AlHandlerError(_BaseException):
    """
    Errors during async I/O (or during configuration validation for creating a
    handler).
    """

    default_layer: Layer = "HANDLER"
    default_category: Category = "IO"
    default_severity: Severity = "ERROR"
    recoverable: bool | None = False


class AlProcessorError(_BaseException):
    """
    Errors caused during processing in one of the processors or renderers (or
    during configuration validation for creating a processor).
    """

    default_layer: Layer = "PROCESSOR"
    default_category: Category = "FORMATTING"
    default_severity: Severity = "ERROR"
    recoverable: bool | None = False


class AlQueueManagerError(_BaseException):
    """Errors involving the async `QueueManager` backend framework."""

    default_layer: Layer = "DISPATCH"
    default_category: Category = "ROUTING"
    default_severity: Severity = "ERROR"
    recoverable: bool | None = False

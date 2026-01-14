from __future__ import annotations

from pathlib import Path
from typing import Self, final

from pydantic import ValidationError

from ._logger import InternalLog
from .bridge import BoundLoggerBase, QueueLoggerWrapper
from .exceptions import (
    AlConfigurationError,
    AlHandlerError,
    AlLoggerCreationError,
    AlProcessorError,
)
from .handlers.base import FuncHandler, Handler
from .handlers.handlers import handler_map
from .manager import QueueManager
from .maps import processor_map, renderer_map
from .models.framework import (
    LoggerConfig,
    LoggingSystemConfig,
)
from .models.handlers import HandlerConfig
from .models.processors import ProcessorConfig, RendererConfig
from .types import (
    FuncProcessor,
    FuncRenderer,
    JsonConfig,
    JsonValue,
    Processor,
    Renderer,
)


@final
class LoggerFactory:
    """
    Factory for creating structured loggers with queue-based async I/O.
    Each logger instance has independent handlers, but all share `QueueManager`.
    """

    __slots__ = (
        "_config",
        "_queue_manager",
        "_loggers",
        "_log",
    )

    def __init__(
        self,
        config: LoggingSystemConfig,
        queue_manager: QueueManager,
        *,
        log_path: str | Path,
    ) -> None:
        self._config: LoggingSystemConfig = config
        self._queue_manager: QueueManager = queue_manager
        self._loggers: dict[str, BoundLoggerBase] = {}

        self._log: InternalLog = InternalLog(
            filename=log_path,
            mode="wb",
            encoding="utf-8",
        )
        self._log.debug(f"Successfully initialized `{self.__class__.__name__}`")

    @classmethod
    def from_json(
        cls,
        config: JsonConfig | JsonValue,
        queue_manager: QueueManager,
        *,
        log_path: str | Path,
    ) -> Self:
        """
        Creates an instance of this factory from config data native to JSON.

        Raises:
            * `AlConfigurationError`: The provided config is invalid for factory.
        """

        try:
            v_cfg: LoggingSystemConfig = LoggingSystemConfig.model_validate(obj=config)
            return cls(
                config=v_cfg,
                queue_manager=queue_manager,
                log_path=log_path,
            )
        except ValidationError as exc:
            raise AlConfigurationError(
                "Could not create `LoggerFactory` instance due to invalid of config"
            ) from exc

    def get_logger(self, name: str) -> BoundLoggerBase:
        """
        Get an existing logger instance, otherwise create it.

        Raises:
            * `AlConfigurationError`: Configuration not found for `name` of logger.
            * `AlLoggerCreationError`: Failure to create logger due to other errors.
        """

        if name in self._loggers:
            return self._loggers[name]

        # Find config for this logger
        logger_config: LoggerConfig | None = next(
            (cfg for cfg in self._config.loggers if cfg.name == name), None
        )
        if logger_config is None:
            raise AlConfigurationError(
                f"Logger `{name}` not found in configuration",
                service=self.__class__.__name__,
            )
        self._log.debug(f"Found logger config of name `{logger_config.name}`")
        logger: BoundLoggerBase = self._create_logger(config=logger_config)
        self._log.debug(
            f"Successfully created logger `{logger_config.name}` from existing config"
        )
        self._loggers[name] = logger
        return logger

    def get_logger_from_config(self, config: LoggerConfig) -> BoundLoggerBase:
        """
        Creates a new logger instance from validated config.

        Raises:
            * `AlLoggerCreationError`: Failure to create logger due to other errors.
        """

        logger: BoundLoggerBase = self._create_logger(config)
        self._log.debug(f"Successfully created logger `{config.name}` from config")
        return logger

    def get_logger_from_json(self, config: JsonConfig | JsonValue) -> BoundLoggerBase:
        """
        Creates a new logger instance from config data native to JSON.

        Raises:
            * `AlConfigurationError`: Failure to create logger due to other errors.
        """

        try:
            v_cfg: LoggerConfig = LoggerConfig.model_validate(obj=config)
        except ValidationError as exc:
            raise AlConfigurationError(
                "Failed to create logger due to invalid config structure",
                service=self.__class__.__name__,
            ) from exc

        logger: BoundLoggerBase = self._create_logger(config=v_cfg)
        self._log.debug(f"Successfully created logger `{v_cfg.name}` from config")
        return logger

    def _create_logger(self, config: LoggerConfig) -> BoundLoggerBase:
        """Create logger with handlers."""

        # Create handlers and register to specific logger
        try:
            for h_cfg in config.handlers:
                handler: Handler = self._create_handler(config=h_cfg)
                _ = self._queue_manager.register_handler(
                    logger_name=config.name, handler=handler
                )

            # Create processor pipeline
            processors: list[Processor] = []
            for cfg in config.processors:
                processors = [self._create_processor(config=cfg)]

        except (AlHandlerError, AlProcessorError) as exc:
            raise AlLoggerCreationError(
                f"Failed to create logger `{config.name}`",
                service=self.__class__.__name__,
            ) from exc

        logger: BoundLoggerBase = BoundLoggerBase(
            logger=QueueLoggerWrapper(
                name=config.name,
                queue_manager=self._queue_manager,
            ),
            processors=processors,
            context={},
        )
        self._log.debug(f"Created logger `{config.name}`")

        # Bind initial context
        if config.context:
            logger = logger.bind(**config.context)
            self._log.debug(
                f"Binded context to logger `{config.name}`",
                binded_context=config.context,
            )

        return logger

    # ---------------------------------------------------------------------------------
    #   Processor, Renderer, Handler creators
    # ---------------------------------------------------------------------------------

    def _create_processor(self, config: ProcessorConfig) -> Processor:
        """Create processor instance from config."""

        proc_creator: FuncProcessor | None = processor_map.get(config.type)
        if proc_creator is None:
            raise AlProcessorError(
                f"Unknown processor type: `{config.type}`",
                service=self.__class__.__name__,
                category="CONFIGURATION",
            )

        processor: Processor = proc_creator(config)
        self._log.debug(f"Successfully created processor of type `{config.type.value}`")
        return processor

    def _create_renderer(self, config: RendererConfig) -> Renderer:
        """Create renderer from configuration."""

        rend_creator: FuncRenderer | None = renderer_map.get(config.type)
        if rend_creator is None:
            raise AlProcessorError(
                f"Unknown renderer type: `{config.type}`",
                service=self.__class__.__name__,
                category="CONFIGURATION",
            )

        renderer: Renderer = rend_creator(config)
        self._log.debug(f"Successfully created renderer of type `{config.type.value}`")
        return renderer

    def _create_handler(self, config: HandlerConfig) -> Handler:
        """Create handler from configuration."""

        # Build handler-specific processors
        try:
            processors: list[Processor] = []
            for cfg in config.processors:
                processors = [self._create_processor(config=cfg)]
            renderer: Renderer = self._create_renderer(config=config.renderer)
        except (RuntimeError, AlProcessorError) as exc:
            raise AlHandlerError(
                f"Failed to create handler of type `{config.type.value}`",
                service=self.__class__.__name__,
                category="CONFIGURATION",
            ) from exc

        hdlr_creator: FuncHandler | None = handler_map.get(config.type)
        if hdlr_creator is None:
            raise AlHandlerError(
                f"Unknown handler type `{config.type.value}`",
                service=self.__class__.__name__,
                category="CONFIGURATION",
            )

        handler: Handler = hdlr_creator(config, renderer, processors)
        self._log.debug(f"Successfully created handler of type `{config.type.value}`")
        return handler

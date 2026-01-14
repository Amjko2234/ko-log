# pyright: reportPrivateUsage=false

from collections.abc import AsyncGenerator, Mapping
from pathlib import Path
from typing import TypeAlias

import pytest
import pytest_asyncio

from ko_log import BoundLoggerBase, LoggerFactory, LogLevel, QueueManager
from ko_log.exceptions import AlConfigurationError
from ko_log.models import (
    BackpressurePolicy,
    LoggerConfig,
    LoggingSystemConfig,
    QueueConfig,
)

_FactoryWithManager: TypeAlias = tuple[LoggerFactory, QueueManager]


class TestLoggerFactoryIntegration:
    """Integration tests for `LoggerFactory` for creating real loggers."""

    @pytest_asyncio.fixture
    async def factory_with_queue_manager(
        self, random_log_file: Path
    ) -> AsyncGenerator[_FactoryWithManager, None]:
        """Create a `LoggerFactory` with a running `QueueManager`."""

        queue_config = QueueConfig(
            max_queue_size=100,
            backpressure_policy=BackpressurePolicy.BLOCK,
            drain_timeout=2.0,
        )
        queue_manager: QueueManager = QueueManager(config=queue_config)
        await queue_manager.start()

        # Create minimal system config
        system_config: LoggingSystemConfig = LoggingSystemConfig(
            loggers=[], default_level=LogLevel.INFO
        )

        factory: LoggerFactory = LoggerFactory(
            config=system_config,
            queue_manager=queue_manager,
            log_path=random_log_file,
        )

        yield factory, queue_manager

        await queue_manager.shutdown()

    # ----------------------------------------------------------------------------------
    #   Helpers
    # ----------------------------------------------------------------------------------

    def create_test_logger_config(self, name: str = "test_logger") -> LoggerConfig:
        """Helper to create a logger configuration for testing."""

        return LoggerConfig(
            name=name,
            level=LogLevel.DEBUG,
            processors=[],
            handlers=[],
            propagate=False,
            context={},
        )

    def test_create_logger_from_config(
        self, factory_with_queue_manager: _FactoryWithManager
    ) -> None:
        """Test creating a `BoundLoggerBase` logger from a `LoggerConfig`."""

        factory, _ = factory_with_queue_manager

        # Create a logger config
        logger_config: LoggerConfig = self.create_test_logger_config(name="test_logger")

        # Create logger from config
        logger: BoundLoggerBase = factory.get_logger_from_config(config=logger_config)

        # Verify logger was created
        assert isinstance(logger, BoundLoggerBase)
        assert logger._logger.name == "test_logger"
        pass

    def test_get_logger_creates_and_caches(
        self, factory_with_queue_manager: _FactoryWithManager
    ) -> None:
        """Test that `LoggerFactory.get_logger` creates and caches loggers."""

        factory, _ = factory_with_queue_manager

        # Add a logger config to the factory's system config
        logger_config: LoggerConfig = self.create_test_logger_config(
            name="cached_logger"
        )
        factory._config.loggers.append(logger_config)

        # First call should create the logger
        logger1: BoundLoggerBase = factory.get_logger(name="cached_logger")

        # Second call should return the cached logger
        logger2: BoundLoggerBase = factory.get_logger(name="cached_logger")

        # Should be the same instance
        assert logger1 is logger2

    def test_logger_with_context_binding(
        self, factory_with_queue_manager: _FactoryWithManager
    ) -> None:
        """Test logger creation with initial context."""

        factory, _ = factory_with_queue_manager

        # Create logger config with context
        logger_config: LoggerConfig = LoggerConfig(
            name="context_logger",
            level=LogLevel.DEBUG,
            processors=[],
            handlers=[],
            propagate=False,
            context={"app": "test_app", "version": "1.0.0"},
        )
        logger: BoundLoggerBase = factory.get_logger_from_config(config=logger_config)

        # Verify context was bound
        assert "app" in logger._context
        assert logger._context["app"] == "test_app"
        assert logger._context["version"] == "1.0.0"

    def test_logger_missing_config_raises_error(
        self, factory_with_queue_manager: _FactoryWithManager
    ) -> None:
        """Test that getting a non-existent logger raises error."""

        factory, _ = factory_with_queue_manager

        # Factory config has no loggers
        with pytest.raises(
            AlConfigurationError, match="not found in configuration"
        ) as exc_info:
            _ = factory.get_logger(name="non_existent_logger")

        assert "Logger `non_existent_logger` not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_logger_from_json_config(
        self, factory_with_queue_manager: _FactoryWithManager
    ) -> None:
        """Test creating logger from JSON configuration."""

        factory, _ = factory_with_queue_manager

        # JSON configuration
        json_config: Mapping[str, object] = {
            "name": "json_logger",
            "level": "WARNING",
            "processors": [],
            "handlers": [],
            "propagate": True,
            "context": {"source": "json"},
        }
        logger: BoundLoggerBase = factory.get_logger_from_json(config=json_config)

        # Verify logger was created correctly
        assert isinstance(logger, BoundLoggerBase)
        assert logger._logger.name == "json_logger"

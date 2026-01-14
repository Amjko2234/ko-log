# pyright: reportPrivateUsage=false


from pathlib import Path

import pytest
from _pytest.capture import CaptureResult
from pytest import CaptureFixture

from ko_log import BoundLoggerBase, LoggerFactory, QueueManager
from ko_log.exceptions import AlConfigurationError
from ko_log.models import BackpressurePolicy, QueueConfig
from ko_log.types import JsonConfig


class TestConfigurationIntegration:
    """Tests for configuration loading and validation."""

    def test_queue_manager_from_json(self) -> None:
        """Test creating `QueueManager` from JSON configuration."""

        json_config: JsonConfig = {
            "max_queue_size": 5000,
            "backpressure_policy": "drop",
            "drain_timeout": 3.0,
            "worker_count": 2,
        }

        manager: QueueManager = QueueManager.from_json(config=json_config)

        # Verify values are as defined from JSON config
        assert manager._config.max_queue_size == 5000
        assert manager._config.backpressure_policy == BackpressurePolicy.DROP
        assert manager._config.drain_timeout == 3.0
        assert manager._config.worker_count == 2

    def test_invalid_queue_manager_json_raises_error(self) -> None:
        """Test invalid JSON configuration raises."""

        invalid_config: JsonConfig = {
            "max_queue_size": "not_an_integer",  # Wrong type
            "backpressure_policy": "invalid_policy",  # Invalid enum
        }

        with pytest.raises(
            AlConfigurationError, match="Could not create queueing manager instance"
        ):
            _ = QueueManager.from_json(config=invalid_config)

    @pytest.mark.asyncio
    async def test_factory_from_json_with_real_handlers(
        self, capsys: CaptureFixture[str], random_log_file: Path
    ) -> None:
        """Test creating a complete factory from JSON with real handlers."""

        json_config: JsonConfig = {
            "loggers": [
                {
                    "name": "root",
                    "level": "DEBUG",
                    "processors": [],
                    "propagate": False,
                    "handlers": [
                        {
                            "type": "stream",
                            "params": {"use_stderr": False},
                            "processors": [],
                            "renderer": {
                                "type": "stream_plain",
                                "params": {
                                    "fmt": "%(asctime)s - %(name)s - %(level)s - %(event)s",
                                    "datefmt": "%Y-%m-%d %H:%M:%S",
                                    "level": "NOTSET",
                                },
                            },
                        }
                    ],  # Hahaha, WTF brace hell
                }
            ],
            "default_level": "INFO",
        }

        # Create QueueManager
        queue_config: QueueConfig = QueueConfig()
        queue_manager: QueueManager = QueueManager(config=queue_config)
        await queue_manager.start()

        # Create factory from JSON, then logger
        factory: LoggerFactory = LoggerFactory.from_json(
            config=json_config, queue_manager=queue_manager, log_path=random_log_file
        )
        logger: BoundLoggerBase = factory.get_logger(name="root")

        # Should be able to log
        logger.info("Test from JSON config")

        # Capture log output to `stdout` and assert
        captured: CaptureResult[str] = capsys.readouterr()
        assert "root - INFO - Test from JSON config" in captured.out

        # Cleanup
        await queue_manager.shutdown()

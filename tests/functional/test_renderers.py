import json
from datetime import datetime, timezone
from unittest.mock import MagicMock, Mock, patch

import pytest

from ko_log import LogLevel
from ko_log.exceptions import AlConfigurationError
from ko_log.models import (
    ColoredStreamRendererConfig,
    JSONFileRendererConfig,
    JSONStreamRendererConfig,
    PlainFileRendererConfig,
    PlainStreamRendererConfig,
    RendererConfig,
    RendererType,
)
from ko_log.processors import (
    ColoredRenderer,
    DropLog,
    JSONRenderer,
    PlainRenderer,
    colored_renderer,
    json_renderer,
    plain_renderer,
)
from ko_log.types import EventDict, Renderer


@pytest.fixture
def sample_time() -> datetime:
    return datetime(year=2024, month=1, day=1, hour=12, tzinfo=timezone.utc)


@pytest.fixture
def sample_event_dict(sample_time: datetime) -> EventDict:
    """Sample event dictionary for testing."""

    return {
        "event": "Test log message",
        "level": "INFO",
        "timestamp": sample_time,
        "context": {"user_id": 123, "action": "login"},
    }


@pytest.fixture
def sample_event_dict_no_context(sample_time: datetime) -> EventDict:
    """Event dictionary without context."""

    return {"event": "Test message", "level": "DEBUG", "timestamp": sample_time}


@pytest.fixture
def sample_event_dict_custom_fields(sample_time: datetime) -> EventDict:
    """Event dictionary with custom fields."""
    return {
        "event": "Custom log",
        "level": "WARNING",
        "timestamp": sample_time,
        "custom_field": "custom_value",
        "numeric_field": 42,
    }


class TestPlainRendererFactory:
    """Tests for `plain_renderer` factory function of `PlainRenderer` renderer."""

    def test_plain_renderer_creates_renderer(self) -> None:
        """Test factory creates a `PlainRenderer` instance."""

        config: RendererConfig = RendererConfig(
            type=RendererType.FILE_PLAIN,
            params=PlainFileRendererConfig(
                fmt="%(asctime)s - %(level)s - %(event)s",
                datefmt="%Y-%m-%d %H:%M:%S",
                level=LogLevel.INFO,
            ),
        )

        renderer: Renderer = plain_renderer(config)
        assert isinstance(renderer, PlainRenderer)

    def test_plain_renderer_with_file_type(self) -> None:
        """Test factory accepts `STREAM_PLAIN` type."""

        config: RendererConfig = RendererConfig(
            type=RendererType.STREAM_PLAIN,
            params=PlainStreamRendererConfig(
                fmt="%(asctime)s - %(event)s",
                datefmt="%Y-%m-%d",
                level=LogLevel.DEBUG,
            ),
        )

        renderer: Renderer = plain_renderer(config)
        assert isinstance(renderer, PlainRenderer)

    def test_plain_renderer_raises_on_wrong_type(self) -> None:
        """Test factory raises with wrong renderer type."""

        config: RendererConfig = RendererConfig(
            type=RendererType.STREAM_JSON,
            params=JSONStreamRendererConfig(
                fmt="foobar", datefmt="foobar", level=LogLevel.NOTSET
            ),
        )

        with pytest.raises(
            AlConfigurationError, match="renderer set with invalid params"
        ):
            _ = plain_renderer(config)


class TestPlainRenderer:
    """Tests for `PlainRenderer` renderer class."""

    @pytest.fixture
    def plain_renderer_instance(self) -> PlainRenderer:
        """Create a `PlainRenderer` instance."""

        return PlainRenderer(
            fmt="%(asctime)s - %(level)s - %(event)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            level=LogLevel.INFO,
        )

    @pytest.fixture
    def plain_renderer_notset(self) -> PlainRenderer:
        """Create a `PlainRenderer` with `NOTSET` level."""

        return PlainRenderer(
            fmt="%(asctime)s - %(level)s - %(event)s",
            datefmt="%Y-%m-%d",
            level=LogLevel.NOTSET,
        )

    def test_plain_renderer_output_format(
        self, plain_renderer_instance: PlainRenderer, sample_event_dict: EventDict
    ) -> None:
        """Test `PlainRenderer` formats output according to format string."""

        result: str = plain_renderer_instance(event_dict=sample_event_dict.copy())

        # Should contain the formatted elements
        assert "2024-01-01 12:00:00" in result
        assert "INFO" in result
        assert "Test log message" in result

    def test_plain_renderer_with_notset_level(
        self, plain_renderer_notset: PlainRenderer, sample_event_dict: EventDict
    ) -> None:
        """Test `PlainRenderer` with `NOTSET` level always renders."""

        # Should not raise `DropLog`` for any level
        sample_event_dict["level"] = "DEBUG"
        result: str = plain_renderer_notset(event_dict=sample_event_dict.copy())

        assert "Test log message" in result

    def test_plain_renderer_filters_by_level(
        self, plain_renderer_instance: PlainRenderer, sample_time: datetime
    ) -> None:
        """Test `PlainRenderer` raises `DropLog` for events below configured level."""

        event_dict: EventDict = {
            "event": "Debug message",
            "level": "DEBUG",  # Below INFO
            "timestamp": sample_time,
        }

        with pytest.raises(DropLog):
            _ = plain_renderer_instance(event_dict)

    def test_plain_renderer_allows_equal_or_higher_level(
        self, plain_renderer_instance: PlainRenderer
    ) -> None:
        """Test `PlainRenderer` renders events at or above configured level."""

        # INFO level (equal to configured level)
        event_dict_info: EventDict = {
            "event": "Info message",
            "level": "INFO",
            "timestamp": datetime.now(tz=timezone.utc),
        }

        result_info: str = plain_renderer_instance(event_dict=event_dict_info)
        assert "Info message" in result_info

        # WARNING level (above configured level)
        event_dict_warning: EventDict = {
            "event": "Warning message",
            "level": "WARNING",
            "timestamp": datetime.now(tz=timezone.utc),
        }

        result_warning: str = plain_renderer_instance(event_dict=event_dict_warning)
        assert "Warning message" in result_warning

    def test_plain_renderer_with_custom_fields(
        self, sample_event_dict_custom_fields: EventDict
    ) -> None:
        """Test `PlainRenderer` includes custom fields in format."""

        # Use a format that includes custom fields
        renderer: PlainRenderer = PlainRenderer(
            fmt="%(asctime)s - %(level)s - %(event)s - %(custom_field)s - %(numeric_field)d",
            datefmt="%Y-%m-%d %H:%M:%S",
            level=LogLevel.INFO,
        )

        result: str = renderer(event_dict=sample_event_dict_custom_fields.copy())

        assert "custom_value" in result
        assert "42" in result

    def test_plain_renderer_with_missing_format_field(
        self, plain_renderer_instance: PlainRenderer, sample_event_dict: EventDict
    ) -> None:
        """Test `PlainRenderer` handles missing format fields gracefully."""

        # Remove a field that's in the format string
        event_dict: EventDict = sample_event_dict.copy()
        event_dict.pop("event")

        # Should handle missing field (likely by inserting placeholder or raising KeyError)
        # Based on % formatting, this would raise KeyError
        with pytest.raises(KeyError):
            _ = plain_renderer_instance(event_dict)


class TestJSONRendererFactory:
    """Tests for `json_renderer` factory function for `JSONRenderer` renderer."""

    def test_json_renderer_creates_renderer(self) -> None:
        """Test factory creates a JSONRenderer instance."""

        config: RendererConfig = RendererConfig(
            type=RendererType.STREAM_JSON,
            params=JSONStreamRendererConfig(
                fmt="%(asctime)s - %(level)s - %(event)s",
                datefmt="%Y-%m-%d %H:%M:%S",
                level=LogLevel.INFO,
                skip_keys=False,
                ensure_ascii=True,
                allow_nan=True,
                indentation=2,
                sort_keys=False,
            ),
        )

        renderer: Renderer = json_renderer(config)
        assert isinstance(renderer, JSONRenderer)

    def test_json_renderer_with_file_type(self) -> None:
        """Test factory accepts `FILE_JSON` type."""

        config: RendererConfig = RendererConfig(
            type=RendererType.FILE_JSON,
            params=JSONFileRendererConfig(
                fmt="%(asctime)s - %(level)s - %(message)s",
                datefmt="%Y-%m-%d",
                level=LogLevel.DEBUG,
                skip_keys=True,
                ensure_ascii=False,
                allow_nan=False,
                indentation=None,
                sort_keys=True,
            ),
        )

        renderer: Renderer = json_renderer(config)
        assert isinstance(renderer, JSONRenderer)

    def test_json_renderer_raises_on_wrong_type(self) -> None:
        """Test factory raises with wrong renderer type."""

        config: RendererConfig = RendererConfig(
            type=RendererType.STREAM_PLAIN,
            params=PlainStreamRendererConfig(
                fmt="foobar", datefmt="foobar", level=LogLevel.NOTSET
            ),
        )

        with pytest.raises(
            AlConfigurationError, match="renderer set with invalid params"
        ):
            _ = json_renderer(config)


class TestJSONRenderer:
    """Tests for `JSONRenderer` renderer class."""

    @pytest.fixture
    def json_renderer_instance(self) -> JSONRenderer:
        """Create a `JSONRenderer` instance."""

        return JSONRenderer(
            fmt="%(asctime)s - %(level)s - %(event)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            level=LogLevel.INFO,
            skip_keys=False,
            ensure_ascii=True,
            allow_nan=True,
            indentation=2,
            sort_keys=False,
        )

    @pytest.fixture
    def json_renderer_no_indent(self) -> JSONRenderer:
        """Create a `JSONRenderer` without indentation."""

        return JSONRenderer(
            fmt="%(asctime)s - %(level)s - %(event)s",
            datefmt="%Y-%m-%d",
            level=LogLevel.NOTSET,
            skip_keys=False,
            ensure_ascii=False,
            allow_nan=False,
            indentation=None,
            sort_keys=True,
        )

    def test_json_renderer_output_format_with_context(
        self, json_renderer_instance: JSONRenderer, sample_event_dict: EventDict
    ) -> None:
        """Test `JSONRenderer` includes formatted event and JSON context."""

        result: str = json_renderer_instance(event_dict=sample_event_dict.copy())

        # Should contain the formatted plain part
        lines: list[str] = result.split(sep="\n")
        assert len(lines) > 1

        # First line should be the formatted event
        assert "2024-01-01 12:00:00" in lines[0]
        assert "INFO" in lines[0]
        assert "Test log message" in lines[0]

        # Should have JSON context
        assert '"user_id": 123' in result
        assert '"action": "login"' in result

    def test_json_renderer_output_format_without_context(
        self,
        json_renderer_instance: JSONRenderer,
        sample_event_dict_no_context: EventDict,
    ) -> None:
        """Test `JSONRenderer` output when context is missing."""

        # Don't raise a `DropLog` lol
        sample_event_dict_no_context["level"] = "INFO"
        result: str = json_renderer_instance(
            event_dict=sample_event_dict_no_context.copy()
        )

        # Should not have newline or JSON part
        assert "\n" not in result
        assert "Test message" in result

    def test_json_renderer_with_empty_context(
        self, json_renderer_instance: JSONRenderer, sample_time: datetime
    ) -> None:
        """Test `JSONRenderer` with empty context string."""

        event_dict: EventDict = {
            "event": "Test",
            "level": "INFO",
            "timestamp": sample_time,
            "context": "",
        }

        result: str = json_renderer_instance(event_dict)

        # Should not have JSON part
        assert "\n" not in result
        assert "Test" in result

    def test_json_renderer_filters_by_level(
        self, json_renderer_instance: JSONRenderer, sample_time: datetime
    ) -> None:
        """Test `JSONRenderer` raises DropLog for events below configured level."""

        event_dict: EventDict = {
            "event": "Debug message",
            "level": "DEBUG",  # Below INFO
            "timestamp": sample_time,
            "context": {"test": "value"},
        }

        with pytest.raises(DropLog):
            _ = json_renderer_instance(event_dict)

    def test_json_renderer_with_notset_level(self, sample_time: datetime) -> None:
        """Test `JSONRenderer` with NOTSET level doesn't filter."""

        renderer: JSONRenderer = JSONRenderer(
            fmt="%(event)s",
            datefmt="%Y-%m-%d",
            level=LogLevel.NOTSET,
            skip_keys=False,
            ensure_ascii=True,
            allow_nan=True,
            indentation=2,
            sort_keys=False,
        )

        event_dict: EventDict = {
            "event": "Debug message",
            "level": "DEBUG",
            "timestamp": sample_time,
            "context": {"debug": True},
        }

        result: str = renderer(event_dict)
        assert "Debug message" in result
        assert '"debug": true' in result

    def test_json_renderer_json_parameters(
        self, json_renderer_no_indent: JSONRenderer, sample_time: datetime
    ) -> None:
        """Test `JSONRenderer` respects JSON formatting parameters."""

        event_dict: EventDict = {
            "event": "Test",
            "level": "INFO",
            "timestamp": sample_time,
            "context": {"b": 2, "a": 1, "c": 3},
        }

        result: str = json_renderer_no_indent(event_dict)

        # Should have JSON part
        json_part: str = result.split(sep="\n")[1]

        # Parse JSON to verify sorting
        parsed = json.loads(s=json_part)  # pyright: ignore[reportAny]
        keys = list(parsed.keys())  # pyright: ignore[reportAny]

        # With sort_keys=True, keys should be sorted
        assert keys == ["a", "b", "c"]

        # With ensure_ascii=False, Unicode should be preserved
        event_dict_unicode: EventDict = {
            "event": "Test",
            "level": "INFO",
            "timestamp": sample_time,
            "context": {"text": "café"},
        }

        result_unicode: str = json_renderer_no_indent(event_dict=event_dict_unicode)
        assert "café" in result_unicode  # Not "caf\u00e9"

    def test_json_renderer_with_non_serializable_context(
        self, json_renderer_instance: JSONRenderer, sample_time: datetime
    ) -> None:
        """
        Test `JSONRenderer` handles non-serializable context with `default=str` set.
        """

        event_dict: EventDict = {
            "event": "Test",
            "level": "INFO",
            "timestamp": sample_time,
            "context": {"date": datetime(year=2024, month=1, day=1), "set": {1, 2, 3}},
        }

        # Should not raise exception due to `default=str`
        result: str = json_renderer_instance(event_dict)

        # The non-serializable objects should be converted to strings
        assert "datetime" in result or "2024" in result


class TestColoredRendererFactory:
    """Tests for `colored_renderer` factory function of `ColoredRenderer` renderer."""

    def test_colored_renderer_creates_renderer(self) -> None:
        """Test factory creates a `ColoredRenderer` instance."""

        config: RendererConfig = RendererConfig(
            type=RendererType.STREAM_COLORED,
            params=ColoredStreamRendererConfig(
                fmt="%(asctime)s - %(level)s - %(event)s",
                datefmt="%Y-%m-%d %H:%M:%S",
                level=LogLevel.INFO,
                color_system="auto",
                force_terminal=True,
                force_interactive=None,
                soft_wrap=False,
                theme=None,
                quiet=False,
                width=None,
                height=None,
                style=None,
                no_color=None,
                tab_size=8,
                markup=True,
                emoji=True,
                emoji_variant=None,
                highlight=False,
                log_time=False,
                log_path=False,
                log_time_format="[%X]",
                legacy_windows=None,
                safe_box=True,
                environ=None,
            ),
        )

        renderer: Renderer = colored_renderer(config)
        assert isinstance(renderer, ColoredRenderer)

    def test_colored_renderer_raises_on_wrong_type(self):
        """Test factory raises with wrong renderer type."""

        config: RendererConfig = RendererConfig(
            type=RendererType.STREAM_PLAIN,  # Wrong type
            params=PlainStreamRendererConfig(
                fmt="foobar", datefmt="foobar", level=LogLevel.NOTSET
            ),
        )

        with pytest.raises(
            AlConfigurationError, match="renderer set with invalid params"
        ):
            _ = colored_renderer(config)


class TestColoredRenderer:
    """Tests for `ColoredRenderer` renderer class."""

    @pytest.fixture
    def colored_renderer_instance(self) -> ColoredRenderer:
        """Create a ColoredRenderer instance with mocked dependencies."""
        return ColoredRenderer(
            fmt="%(asctime)s - %(level)s - %(event)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            level=LogLevel.INFO,
            color_system="auto",
            force_terminal=True,
            force_interactive=None,
            soft_wrap=False,
            theme=None,
            quiet=False,
            width=None,
            height=None,
            style=None,
            no_color=None,
            tab_size=8,
            markup=True,
            emoji=True,
            emoji_variant=None,
            highlight=False,
            log_time=False,
            log_path=False,
            log_time_format="[%X]",
            legacy_windows=None,
            safe_box=True,
            environ=None,
        )

    def test_colored_renderer_output_contains_newline(
        self, colored_renderer_instance: ColoredRenderer, sample_event_dict: EventDict
    ) -> None:
        """Test `ColoredRenderer` output ends with newline."""

        # Mock the console to avoid actual rendering with `rich.console.Console`
        mock_console: MagicMock = MagicMock()
        # Amjko:
        # Don't ask how I got to this solution.
        # I'm not saying that I went through so much (even though I did) just to end
        # up with this approach--it's just that I genuinely will not remember in the
        # future what the frck this does and how I got it
        mock_console.capture.return_value.__enter__.return_value.get.return_value = (  # pyright: ignore[reportAny]
            "MockedValue"
        )

        with patch("rich.console.Console", return_value=mock_console):
            result: str = colored_renderer_instance(event_dict=sample_event_dict.copy())

        # Should end with newline
        assert result.endswith("\n")

    def test_colored_renderer_filters_by_level(
        self, colored_renderer_instance: ColoredRenderer, sample_time: datetime
    ) -> None:
        """Test `ColoredRenderer` raises `DropLog` for events below configured level."""

        event_dict: EventDict = {
            "event": "Debug message",
            "level": "DEBUG",  # Below INFO
            "timestamp": sample_time,
        }

        with pytest.raises(DropLog):
            _ = colored_renderer_instance(event_dict)

    def test_colored_renderer_with_notset_level(self, sample_time: datetime) -> None:
        """Test `ColoredRenderer` with `NOTSET` level doesn't filter."""

        renderer: ColoredRenderer = ColoredRenderer(
            fmt="%(level)s",
            datefmt="%Y-%m-%d",
            level=LogLevel.NOTSET,
            color_system=None,
            force_terminal=None,
            force_interactive=None,
            soft_wrap=False,
            theme=None,
            quiet=False,
            width=None,
            height=None,
            style=None,
            no_color=None,
            tab_size=8,
            markup=True,
            emoji=True,
            emoji_variant=None,
            highlight=False,
            log_time=False,
            log_path=False,
            log_time_format="[%X]",
            legacy_windows=None,
            safe_box=True,
            environ=None,
        )

        event_dict: EventDict = {
            "event": "Debug message",
            "level": "DEBUG",
            "timestamp": sample_time,
        }

        # Mock console
        mock_console: MagicMock = MagicMock()
        mock_console.capture.return_value.__enter__.return_value.get.return_value = (  # pyright: ignore[reportAny]
            "MockedValue"
        )

        with patch("rich.console.Console", return_value=mock_console):
            result: str = renderer(event_dict)

        assert result.endswith("\n")

    def test_colored_renderer_processes_all_values(
        self,
        colored_renderer_instance: ColoredRenderer,
        sample_event_dict_custom_fields: EventDict,
    ) -> None:
        """
        Test `ColoredRenderer` processes all `event_dict` values through `rich` module.
        """

        mock_console: Mock = Mock()
        # Set up the capture mock to return different values for different inputs
        mock_capture: MagicMock = MagicMock()
        mock_capture.__enter__.return_value.get.side_effect = lambda: "ProcessedValue"  # pyright: ignore[reportAny]
        mock_console.capture.return_value = mock_capture  # pyright: ignore[reportAny]

        with patch("rich.console.Console", return_value=mock_console):
            _ = colored_renderer_instance(
                event_dict=sample_event_dict_custom_fields.copy()
            )

        # Should have called capture for each value in event_dict
        # (though we can't easily assert which values without mocking more)
        assert mock_console.capture.called  # pyright: ignore[reportAny]
        assert mock_console.print.called  # pyright: ignore[reportAny]

    def test_colored_renderer_formats_asctime(
        self, colored_renderer_instance: ColoredRenderer, sample_time: datetime
    ) -> None:
        """Test `ColoredRenderer` adds `asctime` to `event_dict`."""

        mock_console: MagicMock = MagicMock()
        mock_console.capture.return_value.__enter__.return_value.get.return_value = (  # pyright: ignore[reportAny]
            "ProcessedValue"
        )

        event_dict: EventDict = {
            "event": "Test",
            "level": "INFO",
            "timestamp": sample_time,
        }

        with patch("rich.console.Console", return_value=mock_console):
            _ = colored_renderer_instance(event_dict=event_dict.copy())

        # The asctime should be in the formatted result
        # Since we mock the console, we can't check the exact output
        # But we can verify the console was used
        assert mock_console.capture.called  # pyright: ignore[reportAny]

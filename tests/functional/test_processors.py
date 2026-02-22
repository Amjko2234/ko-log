import sys

import pytest

from ko_log import DropLog
from ko_log.exceptions import AlConfigurationError
from ko_log.models import (
    AddCallsiteParamsConfig,
    AddContextDefaultConfig,
    CallsiteParameter,
    FilterKeysConfig,
    FilterMarkupConfig,
    ProcessorConfig,
    ProcessorType,
)
from ko_log.processors import (
    add_callsite_params,
    add_context_defaults,
    filter_by_level,
    filter_keys,
    filter_markup,
)
from ko_log.types import EventDict, ExcInfo, Processor


@pytest.fixture()
def event_dict_default() -> EventDict:
    return {
        "name": "test logger",
        "event": "test event",
        "level": "DEBUG",
        "exc_info": False,
        "context": {},
    }


class TestAddCallsiteParams:
    """Tests for the `add_callsite_params` processor."""

    def test_added_all_callsite_params(
        self, proc_add_callsite_params: Processor
    ) -> None:
        """Test processor "adds" all callsite info."""

        processor: Processor = proc_add_callsite_params
        event_dict: EventDict = {
            "filename": "test_filename",
            "funcname": "test_funcname",
            "lineno": "test_lineno",
            "module": "test_module",
            "pathname": "test_pathnam",
        }

        result: EventDict = processor(event_dict.copy())
        assert result == event_dict

    def test_added_few_callsite_params(self) -> None:
        """Test processor "adds" only a few callsite info."""

        config: ProcessorConfig = ProcessorConfig(
            type=ProcessorType.ADD_CALLSITE_PARAMS,
            params=AddCallsiteParamsConfig(
                parameters={
                    CallsiteParameter.FUNCNAME,
                    CallsiteParameter.LINENO,
                }
            ),
        )
        processor: Processor = add_callsite_params(config)

        event_dict: EventDict = {
            "filename": "test_filename",
            "funcname": "test_funcname",
            "lineno": "test_lineno",
            "module": "test_module",
            "pathname": "test_pathnam",
        }

        result: EventDict = processor(event_dict.copy())
        assert result != event_dict

        # Callsite info are minimized to what's left
        pairs_left: list[tuple[str, str]] = [
            ("funcname", "test_funcname"),
            ("lineno", "test_lineno"),
        ]
        pairs_removed: list[tuple[str, str]] = [
            ("filename", "test_filename"),
            ("module", "test_module"),
            ("pathname", "test_pathname"),
        ]

        assert all(item in result.items() for item in pairs_left)
        assert all(item not in result.items() for item in pairs_removed)

    def test_incorrect_processor_config_raises(self) -> None:
        """Test processor raises if it receives invalid configuration data."""

        # As if mistaken `add_context_defaults` for `add_callsite_params`
        config: ProcessorConfig = ProcessorConfig(
            type=ProcessorType.ADD_CONTEXT_DEFAULTS,
            params=AddContextDefaultConfig(
                defaults={},
            ),
        )

        with pytest.raises(
            AlConfigurationError, match="processor set with invalid params"
        ):
            _ = add_callsite_params(config)


class TestAddContextDefaults:
    """Tests for the `add_context_defaults` processor."""

    def test_defaults_added(self, proc_add_context_defaults: Processor) -> None:
        """Test processor adds defaults to non-existing context keys."""

        processor: Processor = proc_add_context_defaults
        # Intentionally empty, will be added later with a default by the processor
        event_dict: EventDict = {}

        result: EventDict = processor(event_dict.copy())
        assert result != event_dict

        assert ("environment", "dev") in result.items()

    def test_default_not_added_if_key_exists(self) -> None:
        """Test processor will not override value if the key already exists."""

        config: ProcessorConfig = ProcessorConfig(
            type=ProcessorType.ADD_CONTEXT_DEFAULTS,
            params=AddContextDefaultConfig(
                defaults={
                    "environment": "dev",
                },
            ),
        )
        processor: Processor = add_context_defaults(config)
        event_dict: EventDict = {"environment": "prod"}

        result: EventDict = processor(event_dict.copy())
        assert result == event_dict

    def test_incorrect_processor_config_raises(self) -> None:
        """Test processor raises if it receives invalid configuration data."""

        # As if mistaken `add_callsite_params` for `add_context_defaults`
        config: ProcessorConfig = ProcessorConfig(
            type=ProcessorType.ADD_CALLSITE_PARAMS,
            params=AddCallsiteParamsConfig(
                parameters=set[CallsiteParameter](),
            ),
        )

        with pytest.raises(
            AlConfigurationError, match="processor set with invalid params"
        ):
            _ = add_context_defaults(config)


class TestDictTracebacks:
    """Tests for the `dict_tracebacks` processor."""

    def test_no_exc_info_none(
        self,
        event_dict_default: EventDict,
        proc_dict_tracebacks: Processor,
    ) -> None:
        """Test processor returns unchanged dict when `exc_info` is None."""

        processor: Processor = proc_dict_tracebacks
        event_dict: EventDict = event_dict_default
        event_dict["exc_info"] = None

        event_dict_without_exc_info: EventDict = event_dict_default
        _ = event_dict_without_exc_info.pop("exc_info")

        result: EventDict = processor(event_dict.copy())
        assert result == event_dict
        assert "exc_info" not in event_dict
        assert "exception" not in event_dict

    def test_no_exc_info_false(
        self,
        event_dict_default: EventDict,
        proc_dict_tracebacks: Processor,
    ) -> None:
        """Test processor returns unchanged dict when `exc_info` is False."""

        processor: Processor = proc_dict_tracebacks
        event_dict: EventDict = event_dict_default
        # Logger converts user-input "exc_info" to either `ExcInfo` or `None`
        # Assume `"exc_info"=False` was converted into `"exc_info"=None`
        event_dict["exc_info"] = None

        result: EventDict = processor(event_dict.copy())
        # Should be removed
        assert "exc_info" not in result
        assert "exception" not in result

    def test_exc_info_tuple_with_no_exception(
        self,
        event_dict_default: EventDict,
        proc_dict_tracebacks: Processor,
    ) -> None:
        """Test processor handles `exc_info` tuple with `None` values."""

        processor: Processor = proc_dict_tracebacks
        event_dict: EventDict = event_dict_default
        event_dict["exc_info"] = (None, None, None)

        result: EventDict = processor(event_dict.copy())
        assert "exc_info" not in result
        assert "exception" not in result

    def test_exc_info_tuple_with_nonverbose_exception(
        self,
        event_dict_default: EventDict,
        proc_dict_tracebacks: Processor,
    ) -> None:
        """Test processor converts exception tuple to a non-verbose structured dict."""

        try:
            raise ValueError("Test error message")

        except ValueError:
            exc_info: ExcInfo = sys.exc_info()

        processor: Processor = proc_dict_tracebacks
        event_dict: EventDict = event_dict_default
        event_dict["exc_info"] = exc_info
        event_dict["context"]["verbose_exc"] = False

        result: EventDict = processor(event_dict.copy())
        # Exception structure should look like:
        #   "exception": {
        #       "exc_type": "builtins.ValueError"
        #       "exc_value": "Test error message"
        #   }
        assert "exc_info" not in result

        # Verify exception structure was generated
        assert "exception" in result
        exc_dict: object = result["exception"]  # pyright: ignore[reportAny]
        assert isinstance(exc_dict, dict)

        # Verify exception type and message
        assert exc_dict["exc_type"] is ValueError
        assert "Test error message" in exc_dict["exc_value"]

        # Verify traceback is not included in the structure
        assert "traceback" not in exc_dict

    def test_exc_info_tuple_with_verbose_exception(
        self,
        event_dict_default: EventDict,
        proc_dict_tracebacks: Processor,
    ) -> None:
        """Test processor converts exception tuple to a verbose structured dict."""

        try:
            raise ValueError("Test error message")

        except ValueError:
            exc_info: ExcInfo = sys.exc_info()

        processor: Processor = proc_dict_tracebacks
        event_dict: EventDict = event_dict_default
        event_dict["exc_info"] = exc_info
        event_dict["context"]["verbose_exc"] = True

        result: EventDict = processor(event_dict.copy())
        # Exception structure should look like:
        #   "exception": {
        #       "type": "ValueError"
        #       "module": "builtins"
        #       "message": "Test error message"
        #       "traceback": [
        #           "...traceback lines..."
        #       ]
        #   }
        assert "exc_info" not in result

        # Verify exception structure was generated
        assert "exception" in result
        exc_dict: object = result["exception"]  # pyright: ignore[reportAny]
        assert isinstance(exc_dict, dict)

        # Verify exception type and message
        assert exc_dict["type"] == "ValueError"
        assert exc_dict["module"] == "builtins"
        assert exc_dict["message"] == "Test error message"

        # Verify traceback structure exists
        assert "traceback" in exc_dict
        traceback_frames: object = exc_dict["traceback"]  # pyright: ignore[reportUnknownVariableType]
        assert isinstance(traceback_frames, list)
        assert len(traceback_frames) > 0  # pyright: ignore[reportUnknownArgumentType]

    def test_incorrect_processor_config_raises(self) -> None:
        """Test processor raises if it receives invalid configuration data."""

        # As if mistaken `add_context_defaults` for `dict_tracebacks`
        config: ProcessorConfig = ProcessorConfig(
            type=ProcessorType.ADD_CONTEXT_DEFAULTS,
            params=(AddContextDefaultConfig()),
        )

        with pytest.raises(
            AlConfigurationError, match="processor set with invalid params"
        ):
            _ = filter_markup(config)


class TestFilterByLevel:
    """Tests for the `filter_by_level` processor."""

    def test_lower_log_is_filtered(self, proc_filter_by_level: Processor) -> None:
        """Test processor correctly filters logs by level."""

        processor: Processor = proc_filter_by_level
        event_dict: EventDict = {"level": "DEBUG"}

        # Internally, the queue manager catches these `DropLog`s as signals to drop the log
        with pytest.raises(DropLog):
            _ = processor(event_dict.copy())

    def test_higher_log_passes(self, proc_filter_by_level: Processor) -> None:
        """Test processor lets higher logs than `DEBUG` pass."""

        processor: Processor = proc_filter_by_level
        info_log_dict: EventDict = {"level": "INFO"}
        warn_log_dict: EventDict = {"level": "WARN"}

        # Doesn't raise `DropLog`
        _ = processor(info_log_dict.copy())
        _ = processor(warn_log_dict.copy())

    def test_incorrect_processor_config_raises(self) -> None:
        """Test processor raises if it receives invalid configuration data."""

        # As if mistaken `filter_keys` for `filter_by_level`
        config: ProcessorConfig = ProcessorConfig(
            type=ProcessorType.FILTER_KEYS,
            params=(
                FilterKeysConfig(
                    keys_to_remove=[],
                )
            ),
        )

        with pytest.raises(
            AlConfigurationError, match="processor set with invalid params"
        ):
            _ = filter_by_level(config)


class TestFilterKeys:
    """Tests for the `filter_keys` processor."""

    def test_correctly_filters_keys(self, proc_filter_keys: Processor) -> None:
        """Test processor removes specified keys from the event dictionary."""

        processor: Processor = proc_filter_keys
        event_dict: EventDict = {
            "remove_this_key1": "",
            "remove_this_key2": "",
            "remove_this_key3": "",
            "dont_remove_this_key": "",
        }

        result: EventDict = processor(event_dict.copy())
        assert result != event_dict

        keys_remained: list[tuple[str, str]] = [
            ("dont_remove_this_key", ""),
        ]
        keys_removed: list[tuple[str, str]] = [
            ("remove_this_key1", ""),
            ("remove_this_key2", ""),
            ("remove_this_key3", ""),
        ]

        assert all(key not in result.items() for key in keys_removed)
        assert all(key in result.items() for key in keys_remained)

    def test_incorrect_processor_config_raises(self) -> None:
        """Test processor raises if it receives invalid configuration data."""

        # As if mistaken `filter_markup` for `filter_keys`
        config: ProcessorConfig = ProcessorConfig(
            type=ProcessorType.FILTER_MARKUP,
            params=(FilterMarkupConfig()),
        )

        with pytest.raises(
            AlConfigurationError, match="processor set with invalid params"
        ):
            _ = filter_keys(config)


class TestFilterMarkup:
    """Tests for the `filter_markup` processor."""

    def test_removes_single_tags(self, proc_filter_markup: Processor) -> None:
        """Test processor removes `[bold]text[/bold]` (markup) tags."""

        processor: Processor = proc_filter_markup
        event_dict: EventDict = {"event": "Hello [bold]world[/bold]!"}

        result: EventDict = processor(event_dict.copy())

        assert result["event"] == "Hello world!"

    def test_removes_nested_tags(self, proc_filter_markup: Processor) -> None:
        """Test processor removes nested markup tags."""

        processor: Processor = proc_filter_markup
        event_dict: EventDict = {"event": "Hello [bold][blue]world[/blue][/bold]!"}

        result: EventDict = processor(event_dict.copy())

        assert result["event"] == "Hello world!"

    def test_removes_self_closing_tags(self, proc_filter_markup: Processor) -> None:
        """Test processor removes self-closing markup tags."""

        processor: Processor = proc_filter_markup
        event_dict: EventDict = {"event": "Processing [br/] complete"}

        result: EventDict = processor(event_dict.copy())

        # You may notice the double space is not taken care of. No worries as it is
        # not a big deal--the intended usage of the colored renderer is to render
        # ANSI-formatted characters anyways
        #
        # IM JUST TOO LAZY TO WORRY ABOUT IT MAN TT
        assert result["event"] == "Processing  complete"

    def test_removes_non_markup_tags(self, proc_filter_markup: Processor) -> None:
        """Test processor also (unintentionally) removes non-markup tags."""

        processor: Processor = proc_filter_markup
        event_dict: EventDict = {
            "event": "[INFO] [2024-01-01] [user=admin] Action performed"
        }

        result: EventDict = processor(event_dict.copy())

        # Who the hell even manually adds log tags on log messages???
        # I'm not taking care of that edge case.
        # Those log tags are automatically added by the renderer processor, which is
        # always executed last
        assert result["event"] == "   Action performed"

    def test_preserves_non_tagged_event(self, proc_filter_markup: Processor) -> None:
        """Test processor preserves text without markup tags."""

        processor: Processor = proc_filter_markup
        event_dict: EventDict = {"event": "Text without markup tags"}

        result: EventDict = processor(event_dict.copy())

        assert result == event_dict

    def test_handles_missing_key(self, proc_filter_markup: Processor) -> None:
        """Test processor handles missing key gracefully."""

        processor: Processor = proc_filter_markup
        event_dict: EventDict = {"level": "INFO"}

        # Literally the most important parameter of a log shouldn't be empty--
        # but we're testing this edge case anywys
        # Shouldn't raise an error
        result: EventDict = processor(event_dict.copy())
        assert result["level"] == event_dict["level"]
        assert result["event"] == ""

    def test_incorrect_processor_config_raises(self) -> None:
        """Test processor raises if it receives invalid configuration data."""

        # As if mistaken `filter_keys` for `filter_markup`
        config: ProcessorConfig = ProcessorConfig(
            type=ProcessorType.FILTER_KEYS,
            params=(FilterKeysConfig()),
        )

        with pytest.raises(
            AlConfigurationError, match="processor set with invalid params"
        ):
            _ = filter_markup(config)

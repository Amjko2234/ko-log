from .models.processors import (
    ProcessorType,
    RendererType,
)
from .processors import (
    add_callsite_params,
    add_context_defaults,
    colored_renderer,
    dict_tracebacks,
    filter_by_level,
    filter_keys,
    filter_markup,
    json_renderer,
    plain_renderer,
)
from .types import FuncProcessor, FuncRenderer

# =====================================================================================
#   Processors (formatters & filters)
# =====================================================================================

processor_map: dict[ProcessorType, FuncProcessor] = {
    ProcessorType.ADD_CALLSITE_PARAMS: add_callsite_params,
    ProcessorType.ADD_CONTEXT_DEFAULTS: add_context_defaults,
    ProcessorType.DICT_TRACEBACKS: dict_tracebacks,
    ProcessorType.FILTER_BY_LEVEL: filter_by_level,
    ProcessorType.FILTER_KEYS: filter_keys,
    ProcessorType.FILTER_MARKUP: filter_markup,
    # ProcessorType.ROUTE_BY_LEVEL: _processors.route_by_level_to_handler,
}

# =====================================================================================
#   Processors (renderers)
# =====================================================================================

renderer_map: dict[RendererType, FuncRenderer] = {
    RendererType.FILE_PLAIN: plain_renderer,
    RendererType.FILE_JSON: json_renderer,
    RendererType.STREAM_PLAIN: plain_renderer,
    RendererType.STREAM_COLORED: colored_renderer,
    RendererType.STREAM_JSON: json_renderer,
}

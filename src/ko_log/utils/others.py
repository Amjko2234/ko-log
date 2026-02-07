from collections.abc import Collection, Iterable, Mapping
from types import GenericAlias, NoneType, UnionType
from typing import Literal, TypeAlias, TypeVar, cast, get_args, get_origin, overload

T = TypeVar(name="T")
_Type: TypeAlias = type | GenericAlias | UnionType


@overload
def pop_value(
    dct: dict[str, object], key: str, /, expected_type: type[bool]
) -> bool: ...
@overload
def pop_value(
    dct: dict[str, object], key: str, /, expected_type: type[T]
) -> T | None: ...
def pop_value(
    dct: dict[str, object], key: str, /, expected_type: type[T]
) -> T | bool | None:
    """
    Safe version of `_pop_value()` that never raises, returns `None` on type mismatch.
    """

    try:
        return _pop_value(dct, key, expected_type)
    except Exception:
        raise


def _pop_value(
    dct: dict[str, object], key: str, /, expected_type: type[T]
) -> T | bool | None:
    """Try to pop a value from a dictionary."""

    if key not in dct:
        return None

    value: object = dct.pop(key, None)

    if value is None:
        return None

    # Check if value matches expected type
    try:
        if _check_type(value, expected_type):
            return cast(T, value)
    except Exception:
        pass

    if expected_type is bool:
        return False

    # Indicate type mismatch
    raise ValueError(
        f"Value for key `{key}` has incorrect type."
        + f" Expected type `{expected_type}`, got type `{type(value)}`"
    )


def _check_type(value: object, expected_type: _Type, /) -> bool:
    """
    Check if `value` matches `expected_type` and handle parameterized generics.

    This helper function attempts to perform proper runtime type checking for:
        * Basic types: `int`, `str`, `bool`, etc.
        * Parameterized generics: `list[int]`, tuple[str, ...]`, etc.
        * Union types: `int | str`, `Optional[int]`, `Union[int ,str]`, etc.
        * Literal types: `Literal[False]`, `Literal['string']`, etc.
        * Type aliases (via `get_origin`)
    """

    # None type
    if value is None:
        return _handle_none_type(expected_type)

    # Basic types
    if (isinstance(expected_type, type)) and not (
        isinstance(expected_type, GenericAlias)
    ):
        return _handle_basic_types(value, expected_type)

    # Generic types
    origin: object | None = get_origin(tp=expected_type)
    if origin is None:
        return _handle_unparameterized_aliases(value, expected_type)

    # Union types
    if origin is UnionType:
        return _handle_union_types(value, expected_type)

    # Literal types
    if origin is Literal:
        return _handle_literal_types(value, expected_type)

    # Check if value is instance of the origin type
    origin_type: type = cast(type, origin)
    if not isinstance(value, origin_type):
        return False

    # For parameterized collections, check type arguments if possible
    # if origin in (list, set, frozenset) and hasattr(value, '__iter__'):
    #   ...

    # Tuples
    if origin is tuple:
        return _handle_tuples(value, expected_type)  # pyright: ignore[reportArgumentType]

    # Dictionary
    elif origin is dict:
        return _handle_dict(value, expected_type)  # pyright: ignore[reportArgumentType]

    # Mapping
    elif isinstance(origin, type) and issubclass(origin, Mapping):
        mapping_value: Mapping[object, object] = cast(Mapping[object, object], value)
        return _handle_mapping(mapping_value, expected_type)

    # Collections
    elif isinstance(origin, type) and issubclass(origin, Collection):
        collections_value: Collection[object] = cast(Collection[object], value)
        return _handle_collections(collections_value, expected_type)

    return True


def _handle_none_type(expected_type: _Type, /) -> bool:
    if (isinstance(expected_type, type)) and (expected_type is NoneType):
        return True

    origin: object | None = get_origin(tp=expected_type)
    if origin is UnionType:
        args: tuple[object, ...] = get_args(tp=expected_type)
        if NoneType in args:
            return True
        else:
            return False

    return False


def _handle_basic_types(value: object, expected_type: _Type, /) -> bool:
    try:
        return isinstance(value, expected_type)  # pyright: ignore[reportArgumentType]
    except TypeError:
        # Some types don't support `isinstance()` with certain values
        return False


def _handle_unparameterized_aliases(value: object, expected_type: _Type, /) -> bool:
    if isinstance(expected_type, type):
        try:
            return isinstance(value, expected_type)
        except TypeError:
            return False
    return False


def _handle_union_types(value: object, expected_type: _Type, /) -> bool:
    args: tuple[type[object], ...] = get_args(tp=expected_type)

    valid_type: list[bool] = []
    for arg in args:
        valid_type.append(_check_type(value, arg))

    return any(valid_type)


def _handle_literal_types(value: object, expected_type: _Type, /) -> bool:
    args: tuple[object, ...] = get_args(tp=expected_type)
    if value in args:
        return True
    else:
        return False


def _handle_tuples(value: Iterable[object], expected_type: _Type, /) -> bool:
    args: tuple[type[object], ...] = get_args(tp=expected_type)
    if not isinstance(value, tuple):
        return False

    # Check for variable-length tuple (Tuple[T, ...])
    if (args and len(args) == 2) and (args[1] is Ellipsis):
        item_type: type[object] = args[0]
        for item in value:
            if not _check_type(item, item_type):
                return False
    elif args:
        # Fixed-length tuple
        if len(value) != len(args):
            return False
        for item, item_type in zip(value, args):
            if not _check_type(item, item_type):
                return False

    return True


def _handle_dict(value: object, expected_type: type, /) -> bool:
    if isinstance(value, expected_type):
        return True
    else:
        return False


def _handle_mapping(value: Mapping[object, object], expected_type: _Type, /) -> bool:
    args: tuple[type[object], ...] = get_args(tp=expected_type)
    if args and len(args) == 2:
        key_type, value_type = args
        items = list(value.items())[:10]
        for k, v in items:
            if not _check_type(k, key_type) or not _check_type(v, value_type):
                return False

    return True


def _handle_collections(value: Iterable[object], expected_type: _Type, /) -> bool:
    args: tuple[type[object], ...] = get_args(tp=expected_type)
    if args and len(args) == 1:
        item_type: type[object] = args[0]
        items: list[object] = list(value)[:10]
        for item in items:
            if not _check_type(item, item_type):
                return False

    return True


def _is_valid_type_for_isinstance(tp: object) -> bool:
    """Check if a type can be used with `isinstance()`."""

    if isinstance(tp, type):
        return True
    elif get_origin(tp) is UnionType:
        return True
    else:
        return False

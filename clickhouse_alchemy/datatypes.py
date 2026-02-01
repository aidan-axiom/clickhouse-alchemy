"""ClickHouse data types."""

from __future__ import annotations
from typing import Any, Tuple, Type, Optional, Union


class TypeEngine:
    """Base class for all ClickHouse types."""

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"

    def compile(self) -> str:
        """Render the type as SQL."""
        return self.__class__.__name__


# Integer types
class UInt8(TypeEngine):
    """8-bit unsigned integer (0 to 255)."""
    pass


class UInt16(TypeEngine):
    """16-bit unsigned integer."""
    pass


class UInt32(TypeEngine):
    """32-bit unsigned integer."""
    pass


class UInt64(TypeEngine):
    """64-bit unsigned integer."""
    pass


class UInt128(TypeEngine):
    """128-bit unsigned integer."""
    pass


class UInt256(TypeEngine):
    """256-bit unsigned integer."""
    pass


class Int8(TypeEngine):
    """8-bit signed integer."""
    pass


class Int16(TypeEngine):
    """16-bit signed integer."""
    pass


class Int32(TypeEngine):
    """32-bit signed integer."""
    pass


class Int64(TypeEngine):
    """64-bit signed integer."""
    pass


class Int128(TypeEngine):
    """128-bit signed integer."""
    pass


class Int256(TypeEngine):
    """256-bit signed integer."""
    pass


# Float types
class Float32(TypeEngine):
    """32-bit floating point."""
    pass


class Float64(TypeEngine):
    """64-bit floating point."""
    pass


# String types
class String(TypeEngine):
    """Variable-length string."""
    pass


class FixedString(TypeEngine):
    """Fixed-length string."""

    def __init__(self, length: int):
        self.length = length

    def __repr__(self) -> str:
        return f"FixedString({self.length})"

    def compile(self) -> str:
        return f"FixedString({self.length})"


# Date/Time types
class Date(TypeEngine):
    """Date (YYYY-MM-DD)."""
    pass


class Date32(TypeEngine):
    """Extended range date."""
    pass


class DateTime(TypeEngine):
    """DateTime with optional timezone."""

    def __init__(self, timezone: Optional[str] = None):
        self.timezone = timezone

    def __repr__(self) -> str:
        if self.timezone:
            return f"DateTime('{self.timezone}')"
        return "DateTime()"

    def compile(self) -> str:
        if self.timezone:
            return f"DateTime('{self.timezone}')"
        return "DateTime"


class DateTime64(TypeEngine):
    """DateTime with sub-second precision."""

    def __init__(self, precision: int = 3, timezone: Optional[str] = None):
        self.precision = precision
        self.timezone = timezone

    def __repr__(self) -> str:
        if self.timezone:
            return f"DateTime64({self.precision}, '{self.timezone}')"
        return f"DateTime64({self.precision})"

    def compile(self) -> str:
        if self.timezone:
            return f"DateTime64({self.precision}, '{self.timezone}')"
        return f"DateTime64({self.precision})"


# Special types
class UUID(TypeEngine):
    """UUID type."""
    pass


class IPv4(TypeEngine):
    """IPv4 address."""
    pass


class IPv6(TypeEngine):
    """IPv6 address."""
    pass


class Boolean(TypeEngine):
    """Boolean type (alias for UInt8)."""

    def compile(self) -> str:
        return "Bool"


# Decimal type
class Decimal(TypeEngine):
    """Decimal with precision and scale."""

    def __init__(self, precision: int, scale: int):
        self.precision = precision
        self.scale = scale

    def __repr__(self) -> str:
        return f"Decimal({self.precision}, {self.scale})"

    def compile(self) -> str:
        return f"Decimal({self.precision}, {self.scale})"


# Enum types
class Enum8(TypeEngine):
    """8-bit enum."""

    def __init__(self, *values: Tuple[str, int], **named_values: int):
        self.values = dict(values)
        self.values.update(named_values)

    def __repr__(self) -> str:
        items = ", ".join(f"'{k}' = {v}" for k, v in self.values.items())
        return f"Enum8({items})"

    def compile(self) -> str:
        items = ", ".join(f"'{k}' = {v}" for k, v in self.values.items())
        return f"Enum8({items})"


class Enum16(TypeEngine):
    """16-bit enum."""

    def __init__(self, *values: Tuple[str, int], **named_values: int):
        self.values = dict(values)
        self.values.update(named_values)

    def __repr__(self) -> str:
        items = ", ".join(f"'{k}' = {v}" for k, v in self.values.items())
        return f"Enum16({items})"

    def compile(self) -> str:
        items = ", ".join(f"'{k}' = {v}" for k, v in self.values.items())
        return f"Enum16({items})"


# Composite types
class Array(TypeEngine):
    """Array of elements."""

    def __init__(self, element_type: Union[TypeEngine, Type[TypeEngine]]):
        if isinstance(element_type, type):
            element_type = element_type()
        self.element_type = element_type

    def __repr__(self) -> str:
        return f"Array({self.element_type!r})"

    def compile(self) -> str:
        return f"Array({self.element_type.compile()})"


class Nullable(TypeEngine):
    """Nullable wrapper type."""

    def __init__(self, inner_type: Union[TypeEngine, Type[TypeEngine]]):
        if isinstance(inner_type, type):
            inner_type = inner_type()
        self.inner_type = inner_type

    def __repr__(self) -> str:
        return f"Nullable({self.inner_type!r})"

    def compile(self) -> str:
        return f"Nullable({self.inner_type.compile()})"


class LowCardinality(TypeEngine):
    """LowCardinality wrapper for dictionary encoding."""

    def __init__(self, inner_type: Union[TypeEngine, Type[TypeEngine]]):
        if isinstance(inner_type, type):
            inner_type = inner_type()
        self.inner_type = inner_type

    def __repr__(self) -> str:
        return f"LowCardinality({self.inner_type!r})"

    def compile(self) -> str:
        return f"LowCardinality({self.inner_type.compile()})"


class Tuple_(TypeEngine):
    """Tuple type."""

    def __init__(self, *element_types: Union[TypeEngine, Type[TypeEngine]]):
        self.element_types = tuple(
            t() if isinstance(t, type) else t for t in element_types
        )

    def __repr__(self) -> str:
        types_repr = ", ".join(repr(t) for t in self.element_types)
        return f"Tuple_({types_repr})"

    def compile(self) -> str:
        types_sql = ", ".join(t.compile() for t in self.element_types)
        return f"Tuple({types_sql})"


# Alias for cleaner API
Tuple = Tuple_


class Map(TypeEngine):
    """Map type (key-value pairs)."""

    def __init__(
        self,
        key_type: Union[TypeEngine, Type[TypeEngine]],
        value_type: Union[TypeEngine, Type[TypeEngine]]
    ):
        if isinstance(key_type, type):
            key_type = key_type()
        if isinstance(value_type, type):
            value_type = value_type()
        self.key_type = key_type
        self.value_type = value_type

    def __repr__(self) -> str:
        return f"Map({self.key_type!r}, {self.value_type!r})"

    def compile(self) -> str:
        return f"Map({self.key_type.compile()}, {self.value_type.compile()})"


class Nested(TypeEngine):
    """Nested structure (array of named tuples)."""

    def __init__(self, **fields: Union[TypeEngine, Type[TypeEngine]]):
        self.fields = {
            name: (t() if isinstance(t, type) else t)
            for name, t in fields.items()
        }

    def __repr__(self) -> str:
        fields_repr = ", ".join(f"{k}={v!r}" for k, v in self.fields.items())
        return f"Nested({fields_repr})"

    def compile(self) -> str:
        fields_sql = ", ".join(
            f"{name} {t.compile()}" for name, t in self.fields.items()
        )
        return f"Nested({fields_sql})"


class SimpleAggregateFunction(TypeEngine):
    """SimpleAggregateFunction type for AggregatingMergeTree."""

    def __init__(self, func_name: str, inner_type: Union[TypeEngine, Type[TypeEngine]]):
        self.func_name = func_name
        if isinstance(inner_type, type):
            inner_type = inner_type()
        self.inner_type = inner_type

    def __repr__(self) -> str:
        return f"SimpleAggregateFunction({self.func_name!r}, {self.inner_type!r})"

    def compile(self) -> str:
        return f"SimpleAggregateFunction({self.func_name}, {self.inner_type.compile()})"


class AggregateFunction(TypeEngine):
    """AggregateFunction type for AggregatingMergeTree."""

    def __init__(self, func_name: str, *arg_types: Union[TypeEngine, Type[TypeEngine]]):
        self.func_name = func_name
        self.arg_types = tuple(
            t() if isinstance(t, type) else t for t in arg_types
        )

    def __repr__(self) -> str:
        args_repr = ", ".join(repr(t) for t in self.arg_types)
        return f"AggregateFunction({self.func_name!r}, {args_repr})"

    def compile(self) -> str:
        args_sql = ", ".join(t.compile() for t in self.arg_types)
        return f"AggregateFunction({self.func_name}, {args_sql})"

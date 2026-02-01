"""Tests for ClickHouse data types."""

import pytest

from clickhouse_alchemy import (
    # Integer types
    UInt8, UInt16, UInt32, UInt64, UInt128, UInt256,
    Int8, Int16, Int32, Int64, Int128, Int256,
    # Float types
    Float32, Float64,
    # String types
    String, FixedString,
    # Date/Time types
    Date, Date32, DateTime, DateTime64,
    # Special types
    UUID, IPv4, IPv6, Boolean,
    # Decimal
    Decimal,
    # Enums
    Enum8, Enum16,
    # Composites
    Array, Nullable, LowCardinality, Tuple, Map, Nested,
    SimpleAggregateFunction, AggregateFunction,
)


class TestIntegerTypes:
    """Tests for integer types."""

    def test_uint8(self):
        t = UInt8()
        assert t.compile() == 'UInt8'

    def test_uint16(self):
        t = UInt16()
        assert t.compile() == 'UInt16'

    def test_uint32(self):
        t = UInt32()
        assert t.compile() == 'UInt32'

    def test_uint64(self):
        t = UInt64()
        assert t.compile() == 'UInt64'

    def test_uint128(self):
        t = UInt128()
        assert t.compile() == 'UInt128'

    def test_uint256(self):
        t = UInt256()
        assert t.compile() == 'UInt256'

    def test_int8(self):
        t = Int8()
        assert t.compile() == 'Int8'

    def test_int16(self):
        t = Int16()
        assert t.compile() == 'Int16'

    def test_int32(self):
        t = Int32()
        assert t.compile() == 'Int32'

    def test_int64(self):
        t = Int64()
        assert t.compile() == 'Int64'

    def test_int128(self):
        t = Int128()
        assert t.compile() == 'Int128'

    def test_int256(self):
        t = Int256()
        assert t.compile() == 'Int256'


class TestFloatTypes:
    """Tests for float types."""

    def test_float32(self):
        t = Float32()
        assert t.compile() == 'Float32'

    def test_float64(self):
        t = Float64()
        assert t.compile() == 'Float64'


class TestStringTypes:
    """Tests for string types."""

    def test_string(self):
        t = String()
        assert t.compile() == 'String'

    def test_fixed_string(self):
        t = FixedString(32)
        assert t.compile() == 'FixedString(32)'
        assert t.length == 32

    def test_fixed_string_repr(self):
        t = FixedString(16)
        assert repr(t) == 'FixedString(16)'


class TestDateTimeTypes:
    """Tests for date/time types."""

    def test_date(self):
        t = Date()
        assert t.compile() == 'Date'

    def test_date32(self):
        t = Date32()
        assert t.compile() == 'Date32'

    def test_datetime(self):
        t = DateTime()
        assert t.compile() == 'DateTime'

    def test_datetime_with_timezone(self):
        t = DateTime(timezone='UTC')
        assert t.compile() == "DateTime('UTC')"

    def test_datetime64(self):
        t = DateTime64()
        assert t.compile() == 'DateTime64(3)'

    def test_datetime64_with_precision(self):
        t = DateTime64(precision=6)
        assert t.compile() == 'DateTime64(6)'

    def test_datetime64_with_timezone(self):
        t = DateTime64(precision=6, timezone='America/New_York')
        assert t.compile() == "DateTime64(6, 'America/New_York')"


class TestSpecialTypes:
    """Tests for special types."""

    def test_uuid(self):
        t = UUID()
        assert t.compile() == 'UUID'

    def test_ipv4(self):
        t = IPv4()
        assert t.compile() == 'IPv4'

    def test_ipv6(self):
        t = IPv6()
        assert t.compile() == 'IPv6'

    def test_boolean(self):
        t = Boolean()
        assert t.compile() == 'Bool'


class TestDecimalType:
    """Tests for Decimal type."""

    def test_decimal(self):
        t = Decimal(18, 4)
        assert t.compile() == 'Decimal(18, 4)'
        assert t.precision == 18
        assert t.scale == 4

    def test_decimal_repr(self):
        t = Decimal(10, 2)
        assert repr(t) == 'Decimal(10, 2)'


class TestEnumTypes:
    """Tests for enum types."""

    def test_enum8(self):
        t = Enum8(active=1, inactive=2)
        sql = t.compile()
        assert 'Enum8' in sql
        assert "'active' = 1" in sql
        assert "'inactive' = 2" in sql

    def test_enum16(self):
        t = Enum16(pending=0, approved=1, rejected=2)
        sql = t.compile()
        assert 'Enum16' in sql


class TestCompositeTypes:
    """Tests for composite types."""

    def test_array_with_instance(self):
        t = Array(String())
        assert t.compile() == 'Array(String)'

    def test_array_with_class(self):
        t = Array(String)
        assert t.compile() == 'Array(String)'

    def test_array_repr(self):
        t = Array(UInt64)
        assert repr(t) == 'Array(UInt64())'

    def test_nullable_with_instance(self):
        t = Nullable(String())
        assert t.compile() == 'Nullable(String)'

    def test_nullable_with_class(self):
        t = Nullable(Int32)
        assert t.compile() == 'Nullable(Int32)'

    def test_lowcardinality_with_instance(self):
        t = LowCardinality(String())
        assert t.compile() == 'LowCardinality(String)'

    def test_lowcardinality_with_class(self):
        t = LowCardinality(String)
        assert t.compile() == 'LowCardinality(String)'

    def test_tuple(self):
        t = Tuple(UInt64, String, Float64)
        assert t.compile() == 'Tuple(UInt64, String, Float64)'

    def test_map(self):
        t = Map(String, UInt64)
        assert t.compile() == 'Map(String, UInt64)'

    def test_map_repr(self):
        t = Map(String, Int32)
        assert repr(t) == 'Map(String(), Int32())'

    def test_nested(self):
        t = Nested(id=UInt64, name=String)
        sql = t.compile()
        assert 'Nested' in sql
        assert 'id UInt64' in sql
        assert 'name String' in sql


class TestNestedComposites:
    """Tests for nested composite types."""

    def test_nullable_array(self):
        t = Nullable(Array(String))
        assert t.compile() == 'Nullable(Array(String))'

    def test_array_nullable(self):
        t = Array(Nullable(UInt32))
        assert t.compile() == 'Array(Nullable(UInt32))'

    def test_lowcardinality_nullable(self):
        t = LowCardinality(Nullable(String))
        assert t.compile() == 'LowCardinality(Nullable(String))'

    def test_map_with_array_value(self):
        t = Map(String, Array(UInt64))
        assert t.compile() == 'Map(String, Array(UInt64))'

    def test_array_of_tuples(self):
        t = Array(Tuple(String, UInt64))
        assert t.compile() == 'Array(Tuple(String, UInt64))'


class TestAggregateFunctionTypes:
    """Tests for aggregate function types."""

    def test_simple_aggregate_function(self):
        t = SimpleAggregateFunction('sum', UInt64)
        assert t.compile() == 'SimpleAggregateFunction(sum, UInt64)'

    def test_aggregate_function(self):
        t = AggregateFunction('uniq', String)
        assert t.compile() == 'AggregateFunction(uniq, String)'

    def test_aggregate_function_multiple_args(self):
        t = AggregateFunction('quantile', Float64, Float64)
        sql = t.compile()
        assert 'AggregateFunction(quantile' in sql

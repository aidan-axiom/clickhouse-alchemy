"""Tests for ClickHouse dialect and type parsing."""

import pytest

from clickhouse_alchemy.dialects import ClickHouseDialect, parse_clickhouse_type
from clickhouse_alchemy import (
    UInt8, UInt16, UInt32, UInt64,
    Int8, Int16, Int32, Int64,
    Float32, Float64,
    String, DateTime, Date, UUID,
    Nullable, Array, LowCardinality, Map, Tuple,
    Decimal, FixedString, DateTime64,
)


class TestParseClickHouseType:
    """Tests for parse_clickhouse_type function."""

    def test_parse_simple_types(self):
        assert isinstance(parse_clickhouse_type('UInt8'), UInt8)
        assert isinstance(parse_clickhouse_type('UInt16'), UInt16)
        assert isinstance(parse_clickhouse_type('UInt32'), UInt32)
        assert isinstance(parse_clickhouse_type('UInt64'), UInt64)
        assert isinstance(parse_clickhouse_type('Int8'), Int8)
        assert isinstance(parse_clickhouse_type('Int16'), Int16)
        assert isinstance(parse_clickhouse_type('Int32'), Int32)
        assert isinstance(parse_clickhouse_type('Int64'), Int64)
        assert isinstance(parse_clickhouse_type('Float32'), Float32)
        assert isinstance(parse_clickhouse_type('Float64'), Float64)
        assert isinstance(parse_clickhouse_type('String'), String)
        assert isinstance(parse_clickhouse_type('Date'), Date)
        assert isinstance(parse_clickhouse_type('DateTime'), DateTime)
        assert isinstance(parse_clickhouse_type('UUID'), UUID)

    def test_parse_nullable(self):
        result = parse_clickhouse_type('Nullable(String)')
        assert isinstance(result, Nullable)
        assert isinstance(result.inner_type, String)

    def test_parse_array(self):
        result = parse_clickhouse_type('Array(UInt64)')
        assert isinstance(result, Array)
        assert isinstance(result.element_type, UInt64)

    def test_parse_lowcardinality(self):
        result = parse_clickhouse_type('LowCardinality(String)')
        assert isinstance(result, LowCardinality)
        assert isinstance(result.inner_type, String)

    def test_parse_nested_nullable_array(self):
        result = parse_clickhouse_type('Nullable(Array(String))')
        assert isinstance(result, Nullable)
        assert isinstance(result.inner_type, Array)
        assert isinstance(result.inner_type.element_type, String)

    def test_parse_array_nullable(self):
        result = parse_clickhouse_type('Array(Nullable(UInt32))')
        assert isinstance(result, Array)
        assert isinstance(result.element_type, Nullable)
        assert isinstance(result.element_type.inner_type, UInt32)

    def test_parse_map(self):
        result = parse_clickhouse_type('Map(String, UInt64)')
        assert isinstance(result, Map)
        assert isinstance(result.key_type, String)
        assert isinstance(result.value_type, UInt64)

    def test_parse_map_with_complex_value(self):
        result = parse_clickhouse_type('Map(String, Array(UInt64))')
        assert isinstance(result, Map)
        assert isinstance(result.key_type, String)
        assert isinstance(result.value_type, Array)

    def test_parse_tuple(self):
        result = parse_clickhouse_type('Tuple(UInt64, String, Float64)')
        assert isinstance(result, Tuple)
        assert len(result.element_types) == 3
        assert isinstance(result.element_types[0], UInt64)
        assert isinstance(result.element_types[1], String)
        assert isinstance(result.element_types[2], Float64)

    def test_parse_fixed_string(self):
        result = parse_clickhouse_type('FixedString(32)')
        assert isinstance(result, FixedString)
        assert result.length == 32

    def test_parse_datetime_with_timezone(self):
        result = parse_clickhouse_type("DateTime('UTC')")
        assert isinstance(result, DateTime)
        assert result.timezone == 'UTC'

    def test_parse_datetime64(self):
        result = parse_clickhouse_type('DateTime64(3)')
        assert isinstance(result, DateTime64)
        assert result.precision == 3

    def test_parse_datetime64_with_timezone(self):
        result = parse_clickhouse_type("DateTime64(6, 'America/New_York')")
        assert isinstance(result, DateTime64)
        assert result.precision == 6
        assert result.timezone == 'America/New_York'

    def test_parse_decimal(self):
        result = parse_clickhouse_type('Decimal(18, 4)')
        assert isinstance(result, Decimal)
        assert result.precision == 18
        assert result.scale == 4

    def test_parse_decimal32(self):
        result = parse_clickhouse_type('Decimal32(4)')
        assert isinstance(result, Decimal)
        assert result.precision == 9
        assert result.scale == 4

    def test_parse_decimal64(self):
        result = parse_clickhouse_type('Decimal64(8)')
        assert isinstance(result, Decimal)
        assert result.precision == 18
        assert result.scale == 8

    def test_parse_unknown_defaults_to_string(self):
        result = parse_clickhouse_type('SomeUnknownType')
        assert isinstance(result, String)

    def test_parse_whitespace_handling(self):
        result = parse_clickhouse_type('  Nullable( String )  ')
        assert isinstance(result, Nullable)


class TestClickHouseDialect:
    """Tests for ClickHouseDialect class."""

    def test_dialect_attributes(self):
        dialect = ClickHouseDialect()

        assert dialect.name == 'clickhouse'
        assert dialect.supports_sequences is False
        assert dialect.supports_native_boolean is False
        assert dialect.supports_native_enum is True
        assert dialect.supports_prewhere is True
        assert dialect.supports_final is True
        assert dialect.supports_sample is True
        assert dialect.supports_array_join is True
        assert dialect.supports_mutations is True

    def test_dialect_has_reflection_methods(self):
        """Verify all reflection methods exist."""
        assert hasattr(ClickHouseDialect, 'get_columns')
        assert hasattr(ClickHouseDialect, 'get_table_names')
        assert hasattr(ClickHouseDialect, 'get_view_names')
        assert hasattr(ClickHouseDialect, 'has_table')
        assert hasattr(ClickHouseDialect, 'get_indexes')
        assert hasattr(ClickHouseDialect, 'get_pk_constraint')
        assert hasattr(ClickHouseDialect, 'get_table_options')
        assert hasattr(ClickHouseDialect, 'get_table_comment')


class TestDialectRegistry:
    """Tests for dialect registry."""

    def test_get_dialect(self):
        from clickhouse_alchemy.dialects import get_dialect

        dialect = get_dialect('clickhouse')
        assert isinstance(dialect, ClickHouseDialect)

    def test_get_unknown_dialect(self):
        from clickhouse_alchemy.dialects import get_dialect

        with pytest.raises(ValueError, match="Unknown dialect"):
            get_dialect('unknown')

    def test_register_dialect(self):
        from clickhouse_alchemy.dialects import register_dialect, get_dialect

        class CustomDialect:
            name = 'custom'

        register_dialect('custom', CustomDialect)
        dialect = get_dialect('custom')
        assert dialect.name == 'custom'

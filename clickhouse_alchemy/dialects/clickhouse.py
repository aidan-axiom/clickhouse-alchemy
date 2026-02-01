"""ClickHouse SQL dialect with reflection support."""

from __future__ import annotations
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..engine import Connection
    from ..schema import Table, Column


# Mapping from ClickHouse type names to our type classes
TYPE_MAP = {
    'UInt8': 'UInt8',
    'UInt16': 'UInt16',
    'UInt32': 'UInt32',
    'UInt64': 'UInt64',
    'UInt128': 'UInt128',
    'UInt256': 'UInt256',
    'Int8': 'Int8',
    'Int16': 'Int16',
    'Int32': 'Int32',
    'Int64': 'Int64',
    'Int128': 'Int128',
    'Int256': 'Int256',
    'Float32': 'Float32',
    'Float64': 'Float64',
    'String': 'String',
    'UUID': 'UUID',
    'Date': 'Date',
    'Date32': 'Date32',
    'DateTime': 'DateTime',
    'DateTime64': 'DateTime64',
    'IPv4': 'IPv4',
    'IPv6': 'IPv6',
    'Bool': 'Boolean',
    'Boolean': 'Boolean',
}


def parse_clickhouse_type(type_str: str) -> Any:
    """Parse a ClickHouse type string into a type object.

    Args:
        type_str: ClickHouse type string like 'UInt64', 'Nullable(String)', etc.

    Returns:
        A type instance from clickhouse_alchemy.datatypes
    """
    from .. import datatypes as types

    type_str = type_str.strip()

    # Handle Nullable
    if type_str.startswith('Nullable(') and type_str.endswith(')'):
        inner = type_str[9:-1]
        return types.Nullable(parse_clickhouse_type(inner))

    # Handle LowCardinality
    if type_str.startswith('LowCardinality(') and type_str.endswith(')'):
        inner = type_str[15:-1]
        return types.LowCardinality(parse_clickhouse_type(inner))

    # Handle Array
    if type_str.startswith('Array(') and type_str.endswith(')'):
        inner = type_str[6:-1]
        return types.Array(parse_clickhouse_type(inner))

    # Handle Map
    if type_str.startswith('Map(') and type_str.endswith(')'):
        inner = type_str[4:-1]
        # Need to parse "KeyType, ValueType" - but be careful with nested types
        depth = 0
        comma_pos = -1
        for i, c in enumerate(inner):
            if c in '([':
                depth += 1
            elif c in ')]':
                depth -= 1
            elif c == ',' and depth == 0:
                comma_pos = i
                break
        if comma_pos > 0:
            key_type = inner[:comma_pos].strip()
            val_type = inner[comma_pos + 1:].strip()
            return types.Map(parse_clickhouse_type(key_type), parse_clickhouse_type(val_type))

    # Handle Tuple
    if type_str.startswith('Tuple(') and type_str.endswith(')'):
        inner = type_str[6:-1]
        # Parse comma-separated types, respecting nesting
        elem_types = []
        depth = 0
        start = 0
        for i, c in enumerate(inner):
            if c in '([':
                depth += 1
            elif c in ')]':
                depth -= 1
            elif c == ',' and depth == 0:
                elem_types.append(parse_clickhouse_type(inner[start:i].strip()))
                start = i + 1
        if start < len(inner):
            elem_types.append(parse_clickhouse_type(inner[start:].strip()))
        return types.Tuple_(*elem_types)

    # Handle FixedString(N)
    if type_str.startswith('FixedString(') and type_str.endswith(')'):
        length = int(type_str[12:-1])
        return types.FixedString(length)

    # Handle DateTime with timezone
    if type_str.startswith('DateTime(') and type_str.endswith(')'):
        tz = type_str[9:-1].strip("'\"")
        return types.DateTime(timezone=tz)

    # Handle DateTime64
    if type_str.startswith('DateTime64(') and type_str.endswith(')'):
        inner = type_str[11:-1]
        parts = inner.split(',', 1)
        precision = int(parts[0].strip())
        tz = parts[1].strip().strip("'\"") if len(parts) > 1 else None
        return types.DateTime64(precision=precision, timezone=tz)

    # Handle Decimal
    if type_str.startswith('Decimal(') and type_str.endswith(')'):
        inner = type_str[8:-1]
        parts = inner.split(',')
        precision = int(parts[0].strip())
        scale = int(parts[1].strip())
        return types.Decimal(precision, scale)

    # Handle Decimal32/64/128/256
    for bits in ['32', '64', '128', '256']:
        if type_str.startswith(f'Decimal{bits}(') and type_str.endswith(')'):
            scale = int(type_str[8 + len(bits):-1])
            precision = {'32': 9, '64': 18, '128': 38, '256': 76}[bits]
            return types.Decimal(precision, scale)

    # Handle Enum8/Enum16
    if type_str.startswith('Enum8(') and type_str.endswith(')'):
        return types.Enum8()  # Values would need parsing
    if type_str.startswith('Enum16(') and type_str.endswith(')'):
        return types.Enum16()

    # Handle SimpleAggregateFunction
    if type_str.startswith('SimpleAggregateFunction(') and type_str.endswith(')'):
        inner = type_str[24:-1]
        parts = inner.split(',', 1)
        func_name = parts[0].strip()
        inner_type = parse_clickhouse_type(parts[1].strip()) if len(parts) > 1 else types.UInt64()
        return types.SimpleAggregateFunction(func_name, inner_type)

    # Handle AggregateFunction
    if type_str.startswith('AggregateFunction(') and type_str.endswith(')'):
        inner = type_str[18:-1]
        parts = inner.split(',', 1)
        func_name = parts[0].strip()
        if len(parts) > 1:
            arg_types = [parse_clickhouse_type(t.strip()) for t in parts[1].split(',')]
            return types.AggregateFunction(func_name, *arg_types)
        return types.AggregateFunction(func_name)

    # Simple type lookup
    if type_str in TYPE_MAP:
        type_class = getattr(types, TYPE_MAP[type_str])
        return type_class()

    # Default to String for unknown types
    return types.String()


class ClickHouseDialect:
    """ClickHouse SQL dialect configuration with reflection support."""

    name = "clickhouse"
    supports_sequences = False
    supports_native_boolean = False  # Uses UInt8
    supports_native_enum = True
    supports_statement_cache = True
    supports_multivalues_insert = True

    # ClickHouse-specific
    supports_prewhere = True
    supports_final = True
    supports_sample = True
    supports_array_join = True
    supports_mutations = True

    # Default settings
    default_schema_name: Optional[str] = None

    def __init__(self, **kwargs: Any):
        self._kwargs = kwargs

    @classmethod
    def get_columns(
        cls,
        connection: Connection,
        table_name: str,
        schema: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get column information for a table.

        Args:
            connection: Database connection
            table_name: Name of the table
            schema: Database/schema name (defaults to current database)

        Returns:
            List of column info dicts with keys: name, type, nullable, default, comment
        """
        database = schema or 'currentDatabase()'
        if schema:
            db_condition = f"database = '{schema}'"
        else:
            db_condition = "database = currentDatabase()"

        query = f"""
            SELECT
                name,
                type,
                default_kind,
                default_expression,
                comment
            FROM system.columns
            WHERE {db_condition}
              AND table = '{table_name}'
            ORDER BY position
        """

        result = connection.execute(query)
        columns = []

        for row in result:
            name, type_str, default_kind, default_expr, comment = row

            # Parse nullable from type
            nullable = type_str.startswith('Nullable(')

            # Parse the type
            col_type = parse_clickhouse_type(type_str)

            col_info = {
                'name': name,
                'type': col_type,
                'nullable': nullable,
                'default': default_expr if default_kind else None,
                'default_kind': default_kind,  # '', 'DEFAULT', 'MATERIALIZED', 'ALIAS'
                'comment': comment if comment else None,
            }
            columns.append(col_info)

        return columns

    @classmethod
    def get_table_names(
        cls,
        connection: Connection,
        schema: Optional[str] = None
    ) -> List[str]:
        """Get all table names in the database.

        Args:
            connection: Database connection
            schema: Database name (defaults to current database)

        Returns:
            List of table names
        """
        if schema:
            db_condition = f"database = '{schema}'"
        else:
            db_condition = "database = currentDatabase()"

        query = f"""
            SELECT name
            FROM system.tables
            WHERE {db_condition}
              AND engine NOT LIKE '%View%'
            ORDER BY name
        """

        result = connection.execute(query)
        return [row[0] for row in result]

    @classmethod
    def get_view_names(
        cls,
        connection: Connection,
        schema: Optional[str] = None
    ) -> List[str]:
        """Get all view names in the database.

        Args:
            connection: Database connection
            schema: Database name (defaults to current database)

        Returns:
            List of view names
        """
        if schema:
            db_condition = f"database = '{schema}'"
        else:
            db_condition = "database = currentDatabase()"

        query = f"""
            SELECT name
            FROM system.tables
            WHERE {db_condition}
              AND engine LIKE '%View%'
            ORDER BY name
        """

        result = connection.execute(query)
        return [row[0] for row in result]

    @classmethod
    def has_table(
        cls,
        connection: Connection,
        table_name: str,
        schema: Optional[str] = None
    ) -> bool:
        """Check if a table exists.

        Args:
            connection: Database connection
            table_name: Name of the table
            schema: Database name (defaults to current database)

        Returns:
            True if table exists
        """
        if schema:
            db_condition = f"database = '{schema}'"
        else:
            db_condition = "database = currentDatabase()"

        query = f"""
            SELECT count()
            FROM system.tables
            WHERE {db_condition}
              AND name = '{table_name}'
        """

        result = connection.execute(query)
        count = result.scalar()
        return count > 0

    @classmethod
    def get_indexes(
        cls,
        connection: Connection,
        table_name: str,
        schema: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get secondary index information for a table.

        Args:
            connection: Database connection
            table_name: Name of the table
            schema: Database name (defaults to current database)

        Returns:
            List of index info dicts
        """
        if schema:
            db_condition = f"database = '{schema}'"
        else:
            db_condition = "database = currentDatabase()"

        # Query system.data_skipping_indices for secondary indexes
        query = f"""
            SELECT
                name,
                expr,
                type,
                granularity
            FROM system.data_skipping_indices
            WHERE {db_condition}
              AND table = '{table_name}'
        """

        try:
            result = connection.execute(query)
            indexes = []
            for row in result:
                name, expr, idx_type, granularity = row
                indexes.append({
                    'name': name,
                    'expression': expr,
                    'type': idx_type,
                    'granularity': granularity,
                })
            return indexes
        except Exception:
            # Table might not exist or no indexes
            return []

    @classmethod
    def get_pk_constraint(
        cls,
        connection: Connection,
        table_name: str,
        schema: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get primary key / sorting key information.

        In ClickHouse, the ORDER BY clause defines the primary key for MergeTree tables.

        Args:
            connection: Database connection
            table_name: Name of the table
            schema: Database name (defaults to current database)

        Returns:
            Dict with 'name' (always None for ClickHouse) and 'constrained_columns'
        """
        if schema:
            db_condition = f"database = '{schema}'"
        else:
            db_condition = "database = currentDatabase()"

        query = f"""
            SELECT
                sorting_key,
                primary_key
            FROM system.tables
            WHERE {db_condition}
              AND name = '{table_name}'
        """

        result = connection.execute(query)
        row = result.first()

        if row:
            sorting_key, primary_key = row
            # Parse the key expression into column names
            # This is simplified - real keys can have expressions
            key_str = primary_key or sorting_key or ''
            if key_str:
                columns = [c.strip() for c in key_str.split(',')]
            else:
                columns = []

            return {
                'name': None,  # ClickHouse doesn't have named PK constraints
                'constrained_columns': columns,
            }

        return {'name': None, 'constrained_columns': []}

    @classmethod
    def get_table_options(
        cls,
        connection: Connection,
        table_name: str,
        schema: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get table engine and configuration options.

        Args:
            connection: Database connection
            table_name: Name of the table
            schema: Database name (defaults to current database)

        Returns:
            Dict with engine info, partition key, sorting key, etc.
        """
        if schema:
            db_condition = f"database = '{schema}'"
        else:
            db_condition = "database = currentDatabase()"

        query = f"""
            SELECT
                engine,
                engine_full,
                partition_key,
                sorting_key,
                primary_key,
                sampling_key
            FROM system.tables
            WHERE {db_condition}
              AND name = '{table_name}'
        """

        result = connection.execute(query)
        row = result.first()

        if row:
            engine, engine_full, partition_key, sorting_key, primary_key, sampling_key = row
            return {
                'engine': engine,
                'engine_full': engine_full,
                'partition_by': partition_key or None,
                'order_by': sorting_key or None,
                'primary_key': primary_key or None,
                'sample_by': sampling_key or None,
            }

        return {}

    @classmethod
    def get_table_comment(
        cls,
        connection: Connection,
        table_name: str,
        schema: Optional[str] = None
    ) -> Optional[str]:
        """Get table comment.

        Args:
            connection: Database connection
            table_name: Name of the table
            schema: Database name (defaults to current database)

        Returns:
            Table comment or None
        """
        if schema:
            db_condition = f"database = '{schema}'"
        else:
            db_condition = "database = currentDatabase()"

        query = f"""
            SELECT comment
            FROM system.tables
            WHERE {db_condition}
              AND name = '{table_name}'
        """

        result = connection.execute(query)
        row = result.first()
        if row and row[0]:
            return row[0]
        return None


# Dialect registry for potential future multi-dialect support
_dialect_registry: Dict[str, type] = {
    "clickhouse": ClickHouseDialect,
}


def get_dialect(name: str = "clickhouse") -> ClickHouseDialect:
    """Get a dialect instance by name."""
    dialect_cls = _dialect_registry.get(name)
    if dialect_cls is None:
        raise ValueError(f"Unknown dialect: {name}")
    return dialect_cls()


def register_dialect(name: str, dialect_cls: type) -> None:
    """Register a custom dialect."""
    _dialect_registry[name] = dialect_cls

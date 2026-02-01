"""Schema definitions: Table, Column, MetaData, Index."""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Sequence, Type, Union, TYPE_CHECKING

from .sql.expression import ColumnElement, ColumnClause, _ensure_clause, Literal
from .datatypes import TypeEngine

if TYPE_CHECKING:
    from .engines import TableEngine


class Column(ColumnElement):
    """A table column definition."""

    def __init__(
        self,
        name: str,
        type_: Union[TypeEngine, Type[TypeEngine]],
        primary_key: bool = False,
        nullable: bool = True,
        default: Any = None,
        server_default: Optional[str] = None,
        materialized: Optional[str] = None,
        alias: Optional[str] = None,
        codec: Optional[str] = None,
        ttl: Optional[str] = None,
        comment: Optional[str] = None,
    ):
        self._name = name
        self._type = type_() if isinstance(type_, type) else type_
        self.primary_key = primary_key
        self.nullable = nullable
        self.default = default
        self.server_default = server_default
        self.materialized = materialized
        self._alias = alias
        self.codec = codec
        self.ttl = ttl
        self.comment = comment
        self._table: Optional[Table] = None

    @property
    def name(self) -> str:
        return self._name

    @property
    def type(self) -> TypeEngine:
        return self._type

    @property
    def table(self) -> Optional[Table]:
        return self._table

    def compile(self) -> str:
        """Compile column reference for use in expressions."""
        if self._table is not None:
            return f"{self._table.name}.{self._name}"
        return self._name

    def compile_definition(self) -> str:
        """Compile column definition for CREATE TABLE."""
        parts = [self._name]

        type_sql = self._type.compile()
        parts.append(type_sql)

        # Default expressions
        if self.materialized is not None:
            parts.append(f"MATERIALIZED {self.materialized}")
        elif self._alias is not None:
            parts.append(f"ALIAS {self._alias}")
        elif self.server_default is not None:
            parts.append(f"DEFAULT {self.server_default}")
        elif self.default is not None:
            parts.append(f"DEFAULT {Literal(self.default).compile()}")

        # Codec
        if self.codec:
            parts.append(f"CODEC({self.codec})")

        # TTL
        if self.ttl:
            parts.append(f"TTL {self.ttl}")

        # Comment
        if self.comment:
            parts.append(f"COMMENT '{self.comment}'")

        return " ".join(parts)


class Index:
    """Secondary index definition for ClickHouse."""

    def __init__(
        self,
        name: str,
        expression: Any,
        type_: str,
        granularity: int = 1,
    ):
        self.name = name
        self.expression = expression
        self.type_ = type_
        self.granularity = granularity

    def compile(self) -> str:
        """Compile index definition."""
        expr_sql = _ensure_clause(self.expression).compile()
        return f"INDEX {self.name} {expr_sql} TYPE {self.type_} GRANULARITY {self.granularity}"


class Constraint:
    """Table constraint definition."""

    def __init__(self, name: str, expression: Any):
        self.name = name
        self.expression = expression

    def compile(self) -> str:
        """Compile constraint definition."""
        expr_sql = _ensure_clause(self.expression).compile()
        return f"CONSTRAINT {self.name} CHECK {expr_sql}"


class Projection:
    """Projection definition for ClickHouse."""

    def __init__(
        self,
        name: str,
        select: Any,
    ):
        self.name = name
        self.select = select

    def compile(self) -> str:
        """Compile projection definition."""
        return f"PROJECTION {self.name} ({self.select.compile()})"


class Table(ColumnElement):
    """A table definition."""

    def __init__(
        self,
        name: str,
        *columns: Column,
        schema: Optional[str] = None,
        engine: Optional[TableEngine] = None,
        indexes: Optional[Sequence[Index]] = None,
        constraints: Optional[Sequence[Constraint]] = None,
        projections: Optional[Sequence[Projection]] = None,
        comment: Optional[str] = None,
        metadata: Optional[MetaData] = None,
    ):
        self._name = name
        self._schema = schema
        self._columns: Dict[str, Column] = {}
        self._column_order: List[str] = []
        self.engine = engine
        self._indexes = list(indexes) if indexes else []
        self._constraints = list(constraints) if constraints else []
        self._projections = list(projections) if projections else []
        self.comment = comment
        self._metadata = metadata

        for col in columns:
            self._add_column(col)

        if metadata is not None:
            metadata._add_table(self)

    def _add_column(self, column: Column) -> None:
        """Add a column to the table."""
        column._table = self
        self._columns[column.name] = column
        self._column_order.append(column.name)

    @property
    def name(self) -> str:
        return self._name

    @property
    def schema(self) -> Optional[str]:
        return self._schema

    @property
    def columns(self) -> List[Column]:
        """Return columns in definition order."""
        return [self._columns[name] for name in self._column_order]

    @property
    def c(self) -> _ColumnAccessor:
        """Access columns via .c.column_name."""
        return _ColumnAccessor(self)

    @property
    def indexes(self) -> List[Index]:
        return self._indexes

    @property
    def constraints(self) -> List[Constraint]:
        return self._constraints

    @property
    def projections(self) -> List[Projection]:
        return self._projections

    @property
    def metadata(self) -> Optional[MetaData]:
        return self._metadata

    def compile(self) -> str:
        """Compile table reference."""
        if self._schema:
            return f"{self._schema}.{self._name}"
        return self._name

    def add_index(self, index: Index) -> None:
        """Add an index to the table."""
        self._indexes.append(index)

    def add_constraint(self, constraint: Constraint) -> None:
        """Add a constraint to the table."""
        self._constraints.append(constraint)

    def add_projection(self, projection: Projection) -> None:
        """Add a projection to the table."""
        self._projections.append(projection)

    def select(self, *columns: Any) -> "Select":
        """Create a SELECT from this table."""
        from .sql.selectable import select
        if not columns:
            columns = tuple(self.columns)
        return select(*columns).select_from(self)

    def insert(self) -> "Insert":
        """Create an INSERT into this table."""
        from .sql.dml import insert
        return insert(self)

    def create(self, if_not_exists: bool = False) -> "CreateTable":
        """Create a CREATE TABLE statement."""
        from .sql.ddl import create_table
        stmt = create_table(self)
        if if_not_exists:
            stmt = stmt.if_not_exists()
        return stmt

    def drop(self, if_exists: bool = False) -> "DropTable":
        """Create a DROP TABLE statement."""
        from .sql.ddl import drop_table
        stmt = drop_table(self)
        if if_exists:
            stmt = stmt.if_exists()
        return stmt

    def alias(self, name: str) -> "TableAlias":
        """Create a table alias."""
        return TableAlias(self, name)

    def __getattr__(self, name: str) -> Column:
        """Access columns as attributes."""
        if name.startswith('_'):
            raise AttributeError(name)
        if name in self._columns:
            return self._columns[name]
        raise AttributeError(f"Table {self._name} has no column {name}")

    def __iter__(self):
        """Iterate over columns."""
        return iter(self.columns)


class _ColumnAccessor:
    """Provides attribute-style column access for tables."""

    def __init__(self, table: Table):
        self._table = table

    def __getattr__(self, name: str) -> Column:
        if name.startswith('_'):
            raise AttributeError(name)
        if name in self._table._columns:
            return self._table._columns[name]
        raise AttributeError(f"Table {self._table.name} has no column {name}")

    def __iter__(self):
        return iter(self._table.columns)


class TableAlias(ColumnElement):
    """An aliased table reference."""

    def __init__(self, table: Table, name: str):
        self._table = table
        self._name = name
        self._columns: Dict[str, Column] = {}

        # Create aliased column references
        for col in table.columns:
            aliased_col = Column(col.name, col.type)
            aliased_col._table = self  # type: ignore
            self._columns[col.name] = aliased_col

    @property
    def name(self) -> str:
        return self._name

    @property
    def original(self) -> Table:
        return self._table

    @property
    def c(self) -> _AliasColumnAccessor:
        """Access columns via .c.column_name."""
        return _AliasColumnAccessor(self)

    def compile(self) -> str:
        return f"{self._table.compile()} AS {self._name}"

    def __getattr__(self, name: str) -> Column:
        if name.startswith('_'):
            raise AttributeError(name)
        if name in self._columns:
            return self._columns[name]
        raise AttributeError(f"Table alias {self._name} has no column {name}")


class _AliasColumnAccessor:
    """Column accessor for table aliases."""

    def __init__(self, alias: TableAlias):
        self._alias = alias

    def __getattr__(self, name: str) -> Column:
        if name.startswith('_'):
            raise AttributeError(name)
        if name in self._alias._columns:
            return self._alias._columns[name]
        raise AttributeError(f"Table alias {self._alias.name} has no column {name}")


class MetaData:
    """Collection of table definitions."""

    def __init__(self, schema: Optional[str] = None):
        self._schema = schema
        self._tables: Dict[str, Table] = {}

    @property
    def schema(self) -> Optional[str]:
        return self._schema

    @property
    def tables(self) -> Dict[str, Table]:
        """Return all registered tables."""
        return dict(self._tables)

    def _add_table(self, table: Table) -> None:
        """Register a table with this metadata."""
        key = table.name
        if table.schema:
            key = f"{table.schema}.{table.name}"
        self._tables[key] = table

    def create_all(self, engine: Any = None) -> List[str]:
        """Generate CREATE TABLE statements for all tables."""
        statements = []
        for table in self._tables.values():
            statements.append(table.create().compile())
        return statements

    def drop_all(self, engine: Any = None) -> List[str]:
        """Generate DROP TABLE statements for all tables."""
        statements = []
        for table in self._tables.values():
            statements.append(table.drop(if_exists=True).compile())
        return statements

    def reflect(
        self,
        engine: Any,
        only: Optional[Sequence[str]] = None,
        views: bool = False,
    ) -> None:
        """Reflect tables from the database.

        Args:
            engine: Database engine to use for reflection
            only: If provided, only reflect these table names
            views: If True, also reflect views
        """
        from .dialects.clickhouse import ClickHouseDialect

        with engine.connect() as conn:
            # Get table names
            if only:
                table_names = list(only)
            else:
                table_names = ClickHouseDialect.get_table_names(conn, self._schema)
                if views:
                    table_names.extend(ClickHouseDialect.get_view_names(conn, self._schema))

            # Reflect each table
            for table_name in table_names:
                if table_name in self._tables:
                    continue  # Already have this table

                # Get columns
                columns_info = ClickHouseDialect.get_columns(conn, table_name, self._schema)

                # Get table options (engine, order by, etc.)
                table_options = ClickHouseDialect.get_table_options(conn, table_name, self._schema)

                # Get indexes
                indexes_info = ClickHouseDialect.get_indexes(conn, table_name, self._schema)

                # Get comment
                comment = ClickHouseDialect.get_table_comment(conn, table_name, self._schema)

                # Build Column objects
                columns = []
                for col_info in columns_info:
                    col = Column(
                        name=col_info['name'],
                        type_=col_info['type'],
                        nullable=col_info['nullable'],
                        server_default=col_info['default'],
                        comment=col_info['comment'],
                    )
                    # Handle special default kinds
                    if col_info.get('default_kind') == 'MATERIALIZED':
                        col.materialized = col_info['default']
                        col.server_default = None
                    elif col_info.get('default_kind') == 'ALIAS':
                        col._alias = col_info['default']
                        col.server_default = None
                    columns.append(col)

                # Build Index objects
                indexes = []
                for idx_info in indexes_info:
                    idx = Index(
                        name=idx_info['name'],
                        expression=idx_info['expression'],
                        type_=idx_info['type'],
                        granularity=idx_info.get('granularity', 1),
                    )
                    indexes.append(idx)

                # Create table (without engine - we don't reconstruct engine objects)
                table = Table(
                    table_name,
                    *columns,
                    schema=self._schema,
                    indexes=indexes if indexes else None,
                    comment=comment,
                    metadata=self,
                )

                # Store engine info as table attributes for reference
                table._reflected_engine = table_options.get('engine')
                table._reflected_engine_full = table_options.get('engine_full')
                table._reflected_order_by = table_options.get('order_by')
                table._reflected_partition_by = table_options.get('partition_by')
                table._reflected_primary_key = table_options.get('primary_key')
                table._reflected_sample_by = table_options.get('sample_by')

    def clear(self) -> None:
        """Remove all tables from the metadata."""
        self._tables.clear()

    def __contains__(self, table_name: str) -> bool:
        return table_name in self._tables

    def __getitem__(self, table_name: str) -> Table:
        return self._tables[table_name]

    def __iter__(self):
        return iter(self._tables.values())

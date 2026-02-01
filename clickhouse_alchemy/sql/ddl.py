"""DDL statements: CREATE, DROP, etc."""

from __future__ import annotations
from typing import Any, List, Optional, Sequence, Union, TYPE_CHECKING

from .expression import ClauseElement, _ensure_clause

if TYPE_CHECKING:
    from ..schema import Table, Column
    from ..engines import TableEngine


class CreateTable(ClauseElement):
    """CREATE TABLE statement builder."""

    def __init__(self, table: Any):
        self._table = table
        self._if_not_exists: bool = False
        self._engine: Optional[Any] = None
        self._order_by: Optional[Union[str, Sequence[str]]] = None
        self._partition_by: Optional[Union[str, Sequence[str]]] = None
        self._primary_key: Optional[Union[str, Sequence[str]]] = None
        self._sample_by: Optional[str] = None
        self._ttl: Optional[str] = None
        self._settings: dict = {}
        self._as_select: Optional[Any] = None
        self._temporary: bool = False
        self._on_cluster: Optional[str] = None
        self._comment: Optional[str] = None

    def _copy(self) -> CreateTable:
        new = CreateTable(self._table)
        new._if_not_exists = self._if_not_exists
        new._engine = self._engine
        new._order_by = self._order_by
        new._partition_by = self._partition_by
        new._primary_key = self._primary_key
        new._sample_by = self._sample_by
        new._ttl = self._ttl
        new._settings = self._settings.copy()
        new._as_select = self._as_select
        new._temporary = self._temporary
        new._on_cluster = self._on_cluster
        new._comment = self._comment
        return new

    def if_not_exists(self) -> CreateTable:
        """Add IF NOT EXISTS clause."""
        new = self._copy()
        new._if_not_exists = True
        return new

    def temporary(self) -> CreateTable:
        """Create a temporary table."""
        new = self._copy()
        new._temporary = True
        return new

    def on_cluster(self, cluster: str) -> CreateTable:
        """Add ON CLUSTER clause for distributed DDL."""
        new = self._copy()
        new._on_cluster = cluster
        return new

    def engine(self, engine: Any) -> CreateTable:
        """Set the table engine."""
        new = self._copy()
        new._engine = engine
        return new

    def order_by(self, *columns: str) -> CreateTable:
        """Set ORDER BY clause (required for MergeTree)."""
        new = self._copy()
        new._order_by = columns if len(columns) > 1 else columns[0] if columns else None
        return new

    def partition_by(self, *expressions: str) -> CreateTable:
        """Set PARTITION BY clause."""
        new = self._copy()
        new._partition_by = expressions if len(expressions) > 1 else expressions[0] if expressions else None
        return new

    def primary_key(self, *columns: str) -> CreateTable:
        """Set PRIMARY KEY (if different from ORDER BY)."""
        new = self._copy()
        new._primary_key = columns if len(columns) > 1 else columns[0] if columns else None
        return new

    def sample_by(self, expression: str) -> CreateTable:
        """Set SAMPLE BY clause."""
        new = self._copy()
        new._sample_by = expression
        return new

    def ttl(self, expression: str) -> CreateTable:
        """Set TTL clause."""
        new = self._copy()
        new._ttl = expression
        return new

    def settings(self, **kwargs: Any) -> CreateTable:
        """Add table settings."""
        new = self._copy()
        new._settings.update(kwargs)
        return new

    def as_select(self, select: Any) -> CreateTable:
        """Create table from SELECT query."""
        new = self._copy()
        new._as_select = select
        return new

    def comment(self, text: str) -> CreateTable:
        """Add table comment."""
        new = self._copy()
        new._comment = text
        return new

    def compile(self) -> str:
        """Compile the CREATE TABLE statement to SQL."""
        parts = ["CREATE"]

        if self._temporary:
            parts.append("TEMPORARY")

        parts.append("TABLE")

        if self._if_not_exists:
            parts.append("IF NOT EXISTS")

        # Table name
        if hasattr(self._table, 'name'):
            table_name = self._table.name
            if hasattr(self._table, 'schema') and self._table.schema:
                table_name = f"{self._table.schema}.{table_name}"
        else:
            table_name = str(self._table)
        parts.append(table_name)

        # ON CLUSTER
        if self._on_cluster:
            parts.append(f"ON CLUSTER {self._on_cluster}")

        # Columns
        if hasattr(self._table, 'columns') and self._table.columns and not self._as_select:
            col_defs = []
            for col in self._table.columns:
                col_defs.append(col.compile_definition())
            parts.append(f"({', '.join(col_defs)})")
        elif self._as_select:
            parts.append(f"AS {self._as_select.compile()}")

        # ENGINE
        engine = self._engine or (self._table.engine if hasattr(self._table, 'engine') else None)
        if engine:
            engine_sql = engine.compile() if hasattr(engine, 'compile') else str(engine)
            parts.append(f"ENGINE = {engine_sql}")

        # ORDER BY
        order_by = self._order_by
        if order_by is None and engine and hasattr(engine, 'order_by'):
            order_by = engine.order_by
        if order_by:
            if isinstance(order_by, (list, tuple)):
                parts.append(f"ORDER BY ({', '.join(order_by)})")
            else:
                parts.append(f"ORDER BY {order_by}")

        # PARTITION BY
        partition_by = self._partition_by
        if partition_by is None and engine and hasattr(engine, 'partition_by'):
            partition_by = engine.partition_by
        if partition_by:
            if isinstance(partition_by, (list, tuple)):
                parts.append(f"PARTITION BY ({', '.join(partition_by)})")
            else:
                parts.append(f"PARTITION BY {partition_by}")

        # PRIMARY KEY
        primary_key = self._primary_key
        if primary_key is None and engine and hasattr(engine, 'primary_key'):
            primary_key = engine.primary_key
        if primary_key:
            if isinstance(primary_key, (list, tuple)):
                parts.append(f"PRIMARY KEY ({', '.join(primary_key)})")
            else:
                parts.append(f"PRIMARY KEY {primary_key}")

        # SAMPLE BY
        sample_by = self._sample_by
        if sample_by is None and engine and hasattr(engine, 'sample_by'):
            sample_by = engine.sample_by
        if sample_by:
            parts.append(f"SAMPLE BY {sample_by}")

        # TTL
        ttl = self._ttl
        if ttl is None and engine and hasattr(engine, 'ttl'):
            ttl = engine.ttl
        if ttl:
            parts.append(f"TTL {ttl}")

        # SETTINGS
        all_settings = {}
        if engine and hasattr(engine, 'settings'):
            all_settings.update(engine.settings)
        all_settings.update(self._settings)
        if all_settings:
            settings_sql = ", ".join(f"{k} = {v}" for k, v in all_settings.items())
            parts.append(f"SETTINGS {settings_sql}")

        # COMMENT
        if self._comment:
            parts.append(f"COMMENT '{self._comment}'")

        return " ".join(parts)


class DropTable(ClauseElement):
    """DROP TABLE statement builder."""

    def __init__(self, table: Any):
        self._table = table
        self._if_exists: bool = False
        self._on_cluster: Optional[str] = None
        self._sync: bool = False
        self._no_delay: bool = False

    def _copy(self) -> DropTable:
        new = DropTable(self._table)
        new._if_exists = self._if_exists
        new._on_cluster = self._on_cluster
        new._sync = self._sync
        new._no_delay = self._no_delay
        return new

    def if_exists(self) -> DropTable:
        """Add IF EXISTS clause."""
        new = self._copy()
        new._if_exists = True
        return new

    def on_cluster(self, cluster: str) -> DropTable:
        """Add ON CLUSTER clause."""
        new = self._copy()
        new._on_cluster = cluster
        return new

    def sync(self) -> DropTable:
        """Wait for drop to complete synchronously."""
        new = self._copy()
        new._sync = True
        return new

    def no_delay(self) -> DropTable:
        """Don't delay drop (immediate delete)."""
        new = self._copy()
        new._no_delay = True
        return new

    def compile(self) -> str:
        parts = ["DROP TABLE"]

        if self._if_exists:
            parts.append("IF EXISTS")

        if hasattr(self._table, 'name'):
            table_name = self._table.name
            if hasattr(self._table, 'schema') and self._table.schema:
                table_name = f"{self._table.schema}.{table_name}"
        else:
            table_name = str(self._table)
        parts.append(table_name)

        if self._on_cluster:
            parts.append(f"ON CLUSTER {self._on_cluster}")

        if self._sync:
            parts.append("SYNC")

        if self._no_delay:
            parts.append("NO DELAY")

        return " ".join(parts)


class CreateDatabase(ClauseElement):
    """CREATE DATABASE statement builder."""

    def __init__(self, name: str):
        self._name = name
        self._if_not_exists: bool = False
        self._on_cluster: Optional[str] = None
        self._engine: Optional[str] = None
        self._comment: Optional[str] = None

    def _copy(self) -> CreateDatabase:
        new = CreateDatabase(self._name)
        new._if_not_exists = self._if_not_exists
        new._on_cluster = self._on_cluster
        new._engine = self._engine
        new._comment = self._comment
        return new

    def if_not_exists(self) -> CreateDatabase:
        new = self._copy()
        new._if_not_exists = True
        return new

    def on_cluster(self, cluster: str) -> CreateDatabase:
        new = self._copy()
        new._on_cluster = cluster
        return new

    def engine(self, engine: str) -> CreateDatabase:
        new = self._copy()
        new._engine = engine
        return new

    def comment(self, text: str) -> CreateDatabase:
        new = self._copy()
        new._comment = text
        return new

    def compile(self) -> str:
        parts = ["CREATE DATABASE"]

        if self._if_not_exists:
            parts.append("IF NOT EXISTS")

        parts.append(self._name)

        if self._on_cluster:
            parts.append(f"ON CLUSTER {self._on_cluster}")

        if self._engine:
            parts.append(f"ENGINE = {self._engine}")

        if self._comment:
            parts.append(f"COMMENT '{self._comment}'")

        return " ".join(parts)


class DropDatabase(ClauseElement):
    """DROP DATABASE statement builder."""

    def __init__(self, name: str):
        self._name = name
        self._if_exists: bool = False
        self._on_cluster: Optional[str] = None

    def _copy(self) -> DropDatabase:
        new = DropDatabase(self._name)
        new._if_exists = self._if_exists
        new._on_cluster = self._on_cluster
        return new

    def if_exists(self) -> DropDatabase:
        new = self._copy()
        new._if_exists = True
        return new

    def on_cluster(self, cluster: str) -> DropDatabase:
        new = self._copy()
        new._on_cluster = cluster
        return new

    def compile(self) -> str:
        parts = ["DROP DATABASE"]

        if self._if_exists:
            parts.append("IF EXISTS")

        parts.append(self._name)

        if self._on_cluster:
            parts.append(f"ON CLUSTER {self._on_cluster}")

        return " ".join(parts)


class CreateView(ClauseElement):
    """CREATE VIEW statement builder."""

    def __init__(self, name: str, select: Any):
        self._name = name
        self._select = select
        self._if_not_exists: bool = False
        self._on_cluster: Optional[str] = None
        self._materialized: bool = False
        self._to_table: Optional[str] = None
        self._engine: Optional[Any] = None
        self._populate: bool = False

    def _copy(self) -> CreateView:
        new = CreateView(self._name, self._select)
        new._if_not_exists = self._if_not_exists
        new._on_cluster = self._on_cluster
        new._materialized = self._materialized
        new._to_table = self._to_table
        new._engine = self._engine
        new._populate = self._populate
        return new

    def if_not_exists(self) -> CreateView:
        new = self._copy()
        new._if_not_exists = True
        return new

    def on_cluster(self, cluster: str) -> CreateView:
        new = self._copy()
        new._on_cluster = cluster
        return new

    def materialized(self) -> CreateView:
        new = self._copy()
        new._materialized = True
        return new

    def to_table(self, table: str) -> CreateView:
        new = self._copy()
        new._to_table = table
        return new

    def engine(self, engine: Any) -> CreateView:
        new = self._copy()
        new._engine = engine
        return new

    def populate(self) -> CreateView:
        new = self._copy()
        new._populate = True
        return new

    def compile(self) -> str:
        parts = ["CREATE"]

        if self._materialized:
            parts.append("MATERIALIZED")

        parts.append("VIEW")

        if self._if_not_exists:
            parts.append("IF NOT EXISTS")

        parts.append(self._name)

        if self._on_cluster:
            parts.append(f"ON CLUSTER {self._on_cluster}")

        if self._to_table:
            parts.append(f"TO {self._to_table}")

        if self._engine:
            engine_sql = self._engine.compile() if hasattr(self._engine, 'compile') else str(self._engine)
            parts.append(f"ENGINE = {engine_sql}")

        if self._populate:
            parts.append("POPULATE")

        parts.append(f"AS {self._select.compile()}")

        return " ".join(parts)


class DropView(ClauseElement):
    """DROP VIEW statement builder."""

    def __init__(self, name: str):
        self._name = name
        self._if_exists: bool = False
        self._on_cluster: Optional[str] = None

    def _copy(self) -> DropView:
        new = DropView(self._name)
        new._if_exists = self._if_exists
        new._on_cluster = self._on_cluster
        return new

    def if_exists(self) -> DropView:
        new = self._copy()
        new._if_exists = True
        return new

    def on_cluster(self, cluster: str) -> DropView:
        new = self._copy()
        new._on_cluster = cluster
        return new

    def compile(self) -> str:
        parts = ["DROP VIEW"]

        if self._if_exists:
            parts.append("IF EXISTS")

        parts.append(self._name)

        if self._on_cluster:
            parts.append(f"ON CLUSTER {self._on_cluster}")

        return " ".join(parts)


# Factory functions
def create_table(table: Any) -> CreateTable:
    """Create a CREATE TABLE statement."""
    return CreateTable(table)


def drop_table(table: Any) -> DropTable:
    """Create a DROP TABLE statement."""
    return DropTable(table)


def create_database(name: str) -> CreateDatabase:
    """Create a CREATE DATABASE statement."""
    return CreateDatabase(name)


def drop_database(name: str) -> DropDatabase:
    """Create a DROP DATABASE statement."""
    return DropDatabase(name)


def create_view(name: str, select: Any) -> CreateView:
    """Create a CREATE VIEW statement."""
    return CreateView(name, select)


def create_materialized_view(name: str, select: Any) -> CreateView:
    """Create a CREATE MATERIALIZED VIEW statement."""
    return CreateView(name, select).materialized()


def drop_view(name: str) -> DropView:
    """Create a DROP VIEW statement."""
    return DropView(name)

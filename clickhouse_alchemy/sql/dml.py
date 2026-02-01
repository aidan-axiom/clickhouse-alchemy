"""DML statements: INSERT and ALTER for mutations."""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Sequence, Union, TYPE_CHECKING

from .expression import ClauseElement, _ensure_clause, Literal

if TYPE_CHECKING:
    from ..schema import Table
    from .selectable import Select


class Insert(ClauseElement):
    """INSERT statement builder."""

    def __init__(self, table: Any):
        self._table = table
        self._columns: List[str] = []
        self._values: List[Sequence[Any]] = []
        self._select: Optional[Select] = None
        self._settings: dict = {}

    def _copy(self) -> Insert:
        """Create a copy of this Insert."""
        new = Insert(self._table)
        new._columns = self._columns.copy()
        new._values = [list(v) for v in self._values]
        new._select = self._select
        new._settings = self._settings.copy()
        return new

    def columns(self, *cols: str) -> Insert:
        """Specify columns for insertion."""
        new = self._copy()
        new._columns = list(cols)
        return new

    def values(self, *rows: Union[Sequence[Any], Dict[str, Any]]) -> Insert:
        """Add values to insert."""
        new = self._copy()
        for row in rows:
            if isinstance(row, dict):
                if not new._columns:
                    new._columns = list(row.keys())
                new._values.append([row.get(c) for c in new._columns])
            else:
                new._values.append(list(row))
        return new

    def from_select(self, columns: Sequence[str], select: Select) -> Insert:
        """Insert from a SELECT statement."""
        new = self._copy()
        new._columns = list(columns)
        new._select = select
        return new

    def settings(self, **kwargs: Any) -> Insert:
        """Add query settings (ClickHouse-specific)."""
        new = self._copy()
        new._settings.update(kwargs)
        return new

    def compile(self) -> str:
        """Compile the INSERT statement to SQL."""
        table_name = self._table.name if hasattr(self._table, 'name') else str(self._table)

        parts = [f"INSERT INTO {table_name}"]

        if self._columns:
            cols = ", ".join(self._columns)
            parts.append(f"({cols})")

        if self._select is not None:
            parts.append(self._select.compile())
        elif self._values:
            rows_sql = []
            for row in self._values:
                values_sql = ", ".join(Literal(v).compile() for v in row)
                rows_sql.append(f"({values_sql})")
            parts.append("VALUES " + ", ".join(rows_sql))

        if self._settings:
            settings_sql = ", ".join(f"{k}={v}" for k, v in self._settings.items())
            parts.append(f"SETTINGS {settings_sql}")

        return " ".join(parts)


class AlterTable(ClauseElement):
    """ALTER TABLE statement builder for mutations and schema changes."""

    def __init__(self, table: Any):
        self._table = table
        self._operations: List[str] = []
        self._settings: dict = {}

    def _copy(self) -> AlterTable:
        """Create a copy of this AlterTable."""
        new = AlterTable(self._table)
        new._operations = self._operations.copy()
        new._settings = self._settings.copy()
        return new

    def add_column(
        self,
        name: str,
        type_: Any,
        after: Optional[str] = None,
        default: Optional[Any] = None,
    ) -> AlterTable:
        """Add a column."""
        new = self._copy()
        type_sql = type_.compile() if hasattr(type_, 'compile') else str(type_)
        op = f"ADD COLUMN {name} {type_sql}"
        if default is not None:
            op += f" DEFAULT {Literal(default).compile()}"
        if after:
            op += f" AFTER {after}"
        new._operations.append(op)
        return new

    def drop_column(self, name: str) -> AlterTable:
        """Drop a column."""
        new = self._copy()
        new._operations.append(f"DROP COLUMN {name}")
        return new

    def modify_column(self, name: str, type_: Any) -> AlterTable:
        """Modify a column's type."""
        new = self._copy()
        type_sql = type_.compile() if hasattr(type_, 'compile') else str(type_)
        new._operations.append(f"MODIFY COLUMN {name} {type_sql}")
        return new

    def rename_column(self, old_name: str, new_name: str) -> AlterTable:
        """Rename a column."""
        new = self._copy()
        new._operations.append(f"RENAME COLUMN {old_name} TO {new_name}")
        return new

    def clear_column(self, name: str, partition: Optional[str] = None) -> AlterTable:
        """Clear a column's data."""
        new = self._copy()
        op = f"CLEAR COLUMN {name}"
        if partition:
            op += f" IN PARTITION {partition}"
        new._operations.append(op)
        return new

    def comment_column(self, name: str, comment: str) -> AlterTable:
        """Add a comment to a column."""
        new = self._copy()
        new._operations.append(f"COMMENT COLUMN {name} '{comment}'")
        return new

    # Mutations (ClickHouse-specific UPDATE/DELETE alternatives)
    def delete(self, where: Any) -> AlterTable:
        """Delete rows matching condition (mutation)."""
        new = self._copy()
        where_sql = _ensure_clause(where).compile()
        new._operations.append(f"DELETE WHERE {where_sql}")
        return new

    def update(self, assignments: Dict[str, Any], where: Any) -> AlterTable:
        """Update rows matching condition (mutation)."""
        new = self._copy()
        set_parts = []
        for col, val in assignments.items():
            val_sql = _ensure_clause(val).compile()
            set_parts.append(f"{col} = {val_sql}")
        where_sql = _ensure_clause(where).compile()
        new._operations.append(f"UPDATE {', '.join(set_parts)} WHERE {where_sql}")
        return new

    # Partition operations
    def drop_partition(self, partition: str) -> AlterTable:
        """Drop a partition."""
        new = self._copy()
        new._operations.append(f"DROP PARTITION {partition}")
        return new

    def detach_partition(self, partition: str) -> AlterTable:
        """Detach a partition."""
        new = self._copy()
        new._operations.append(f"DETACH PARTITION {partition}")
        return new

    def attach_partition(self, partition: str) -> AlterTable:
        """Attach a partition."""
        new = self._copy()
        new._operations.append(f"ATTACH PARTITION {partition}")
        return new

    def replace_partition(self, partition: str, from_table: str) -> AlterTable:
        """Replace partition from another table."""
        new = self._copy()
        new._operations.append(f"REPLACE PARTITION {partition} FROM {from_table}")
        return new

    def move_partition(self, partition: str, to_table: str) -> AlterTable:
        """Move partition to another table."""
        new = self._copy()
        new._operations.append(f"MOVE PARTITION {partition} TO TABLE {to_table}")
        return new

    def clear_index(self, index_name: str, partition: Optional[str] = None) -> AlterTable:
        """Clear an index."""
        new = self._copy()
        op = f"CLEAR INDEX {index_name}"
        if partition:
            op += f" IN PARTITION {partition}"
        new._operations.append(op)
        return new

    def freeze_partition(self, partition: Optional[str] = None) -> AlterTable:
        """Freeze partition for backup."""
        new = self._copy()
        if partition:
            new._operations.append(f"FREEZE PARTITION {partition}")
        else:
            new._operations.append("FREEZE")
        return new

    def unfreeze_partition(self, partition: str) -> AlterTable:
        """Unfreeze a partition."""
        new = self._copy()
        new._operations.append(f"UNFREEZE PARTITION {partition}")
        return new

    # Index operations
    def add_index(
        self,
        name: str,
        expression: Any,
        type_: str,
        granularity: int = 1
    ) -> AlterTable:
        """Add a secondary index."""
        new = self._copy()
        expr_sql = _ensure_clause(expression).compile()
        new._operations.append(
            f"ADD INDEX {name} {expr_sql} TYPE {type_} GRANULARITY {granularity}"
        )
        return new

    def drop_index(self, name: str) -> AlterTable:
        """Drop a secondary index."""
        new = self._copy()
        new._operations.append(f"DROP INDEX {name}")
        return new

    def materialize_index(self, name: str, partition: Optional[str] = None) -> AlterTable:
        """Materialize an index."""
        new = self._copy()
        op = f"MATERIALIZE INDEX {name}"
        if partition:
            op += f" IN PARTITION {partition}"
        new._operations.append(op)
        return new

    # TTL operations
    def modify_ttl(self, ttl_expression: str) -> AlterTable:
        """Modify table TTL."""
        new = self._copy()
        new._operations.append(f"MODIFY TTL {ttl_expression}")
        return new

    def remove_ttl(self) -> AlterTable:
        """Remove table TTL."""
        new = self._copy()
        new._operations.append("REMOVE TTL")
        return new

    # Settings
    def settings(self, **kwargs: Any) -> AlterTable:
        """Add query settings."""
        new = self._copy()
        new._settings.update(kwargs)
        return new

    def modify_setting(self, **kwargs: Any) -> AlterTable:
        """Modify table settings."""
        new = self._copy()
        for k, v in kwargs.items():
            new._operations.append(f"MODIFY SETTING {k} = {v}")
        return new

    def compile(self) -> str:
        """Compile the ALTER TABLE statement to SQL."""
        table_name = self._table.name if hasattr(self._table, 'name') else str(self._table)

        parts = [f"ALTER TABLE {table_name}"]
        parts.append(", ".join(self._operations))

        if self._settings:
            settings_sql = ", ".join(f"{k}={v}" for k, v in self._settings.items())
            parts.append(f"SETTINGS {settings_sql}")

        return " ".join(parts)


class Optimize(ClauseElement):
    """OPTIMIZE TABLE statement."""

    def __init__(self, table: Any):
        self._table = table
        self._partition: Optional[str] = None
        self._final: bool = False
        self._deduplicate: bool = False
        self._deduplicate_by: List[str] = []

    def _copy(self) -> Optimize:
        new = Optimize(self._table)
        new._partition = self._partition
        new._final = self._final
        new._deduplicate = self._deduplicate
        new._deduplicate_by = self._deduplicate_by.copy()
        return new

    def partition(self, partition: str) -> Optimize:
        """Optimize specific partition."""
        new = self._copy()
        new._partition = partition
        return new

    def final(self) -> Optimize:
        """Add FINAL to merge all parts."""
        new = self._copy()
        new._final = True
        return new

    def deduplicate(self, *columns: str) -> Optimize:
        """Deduplicate data, optionally by specific columns."""
        new = self._copy()
        new._deduplicate = True
        new._deduplicate_by = list(columns)
        return new

    def compile(self) -> str:
        table_name = self._table.name if hasattr(self._table, 'name') else str(self._table)

        parts = [f"OPTIMIZE TABLE {table_name}"]

        if self._partition:
            parts.append(f"PARTITION {self._partition}")

        if self._final:
            parts.append("FINAL")

        if self._deduplicate:
            if self._deduplicate_by:
                cols = ", ".join(self._deduplicate_by)
                parts.append(f"DEDUPLICATE BY {cols}")
            else:
                parts.append("DEDUPLICATE")

        return " ".join(parts)


class Truncate(ClauseElement):
    """TRUNCATE TABLE statement."""

    def __init__(self, table: Any):
        self._table = table
        self._if_exists: bool = False

    def if_exists(self) -> Truncate:
        """Add IF EXISTS clause."""
        new = Truncate(self._table)
        new._if_exists = True
        return new

    def compile(self) -> str:
        table_name = self._table.name if hasattr(self._table, 'name') else str(self._table)

        if self._if_exists:
            return f"TRUNCATE TABLE IF EXISTS {table_name}"
        return f"TRUNCATE TABLE {table_name}"


# Factory functions
def insert(table: Any) -> Insert:
    """Create an INSERT statement."""
    return Insert(table)


def alter_table(table: Any) -> AlterTable:
    """Create an ALTER TABLE statement."""
    return AlterTable(table)


def optimize(table: Any) -> Optimize:
    """Create an OPTIMIZE TABLE statement."""
    return Optimize(table)


def truncate(table: Any) -> Truncate:
    """Create a TRUNCATE TABLE statement."""
    return Truncate(table)

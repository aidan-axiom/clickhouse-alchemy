"""SELECT statement and related constructs."""

from __future__ import annotations
from typing import Any, List, Optional, Sequence, Tuple, Union, TYPE_CHECKING

from .expression import (
    ClauseElement, ColumnElement, ColumnClause, _ensure_clause,
    Literal, FunctionCall, Subquery
)

if TYPE_CHECKING:
    from ..schema import Table


class FromClause(ClauseElement):
    """Base class for things that can appear in FROM."""
    pass


class Select(ColumnElement):
    """SELECT statement builder."""

    def __init__(self, *columns: Any):
        self._columns: List[ClauseElement] = [_ensure_clause(c) for c in columns]
        self._from: Optional[ClauseElement] = None
        self._where: Optional[ClauseElement] = None
        self._prewhere: Optional[ClauseElement] = None
        self._group_by: List[ClauseElement] = []
        self._having: Optional[ClauseElement] = None
        self._order_by: List[ClauseElement] = []
        self._limit: Optional[int] = None
        self._offset: Optional[int] = None
        self._distinct: bool = False
        self._distinct_on: List[ClauseElement] = []
        self._final: bool = False
        self._sample: Optional[Union[float, Tuple[int, int]]] = None
        self._array_join: Optional[Tuple[ClauseElement, bool]] = None  # (expr, is_left)
        self._joins: List[Join] = []
        self._ctes: List[Tuple[str, Select]] = []
        self._settings: dict = {}
        self._union: Optional[Tuple[Select, bool]] = None  # (select, is_all)
        self._for_update: bool = False

    def _copy(self) -> Select:
        """Create a copy of this Select."""
        new = Select()
        new._columns = self._columns.copy()
        new._from = self._from
        new._where = self._where
        new._prewhere = self._prewhere
        new._group_by = self._group_by.copy()
        new._having = self._having
        new._order_by = self._order_by.copy()
        new._limit = self._limit
        new._offset = self._offset
        new._distinct = self._distinct
        new._distinct_on = self._distinct_on.copy()
        new._final = self._final
        new._sample = self._sample
        new._array_join = self._array_join
        new._joins = self._joins.copy()
        new._ctes = self._ctes.copy()
        new._settings = self._settings.copy()
        new._union = self._union
        new._for_update = self._for_update
        return new

    def select_from(self, from_clause: Any) -> Select:
        """Set the FROM clause."""
        new = self._copy()
        new._from = _ensure_clause(from_clause) if not isinstance(from_clause, ClauseElement) else from_clause
        return new

    def where(self, *conditions: Any) -> Select:
        """Add WHERE conditions (ANDed together)."""
        new = self._copy()
        for condition in conditions:
            condition = _ensure_clause(condition)
            if new._where is None:
                new._where = condition
            else:
                from .expression import BinaryExpression
                new._where = BinaryExpression(new._where, condition, "AND")
        return new

    def prewhere(self, *conditions: Any) -> Select:
        """Add PREWHERE conditions (ClickHouse-specific, ANDed together)."""
        new = self._copy()
        for condition in conditions:
            condition = _ensure_clause(condition)
            if new._prewhere is None:
                new._prewhere = condition
            else:
                from .expression import BinaryExpression
                new._prewhere = BinaryExpression(new._prewhere, condition, "AND")
        return new

    def group_by(self, *columns: Any) -> Select:
        """Add GROUP BY columns."""
        new = self._copy()
        new._group_by = new._group_by + [_ensure_clause(c) for c in columns]
        return new

    def having(self, *conditions: Any) -> Select:
        """Add HAVING conditions (ANDed together)."""
        new = self._copy()
        for condition in conditions:
            condition = _ensure_clause(condition)
            if new._having is None:
                new._having = condition
            else:
                from .expression import BinaryExpression
                new._having = BinaryExpression(new._having, condition, "AND")
        return new

    def order_by(self, *columns: Any) -> Select:
        """Add ORDER BY columns."""
        new = self._copy()
        new._order_by = new._order_by + [_ensure_clause(c) for c in columns]
        return new

    def limit(self, limit: int) -> Select:
        """Set LIMIT."""
        new = self._copy()
        new._limit = limit
        return new

    def offset(self, offset: int) -> Select:
        """Set OFFSET."""
        new = self._copy()
        new._offset = offset
        return new

    def distinct(self, *on_columns: Any) -> Select:
        """Add DISTINCT or DISTINCT ON."""
        new = self._copy()
        new._distinct = True
        if on_columns:
            new._distinct_on = [_ensure_clause(c) for c in on_columns]
        return new

    def final(self) -> Select:
        """Add FINAL keyword (ClickHouse-specific for ReplacingMergeTree, etc.)."""
        new = self._copy()
        new._final = True
        return new

    def sample(self, ratio: Union[float, int], offset: Optional[int] = None) -> Select:
        """Add SAMPLE clause (ClickHouse-specific)."""
        new = self._copy()
        if offset is not None:
            new._sample = (ratio, offset)
        else:
            new._sample = ratio
        return new

    def array_join(self, expression: Any, left: bool = False) -> Select:
        """Add ARRAY JOIN clause (ClickHouse-specific)."""
        new = self._copy()
        new._array_join = (_ensure_clause(expression), left)
        return new

    def left_array_join(self, expression: Any) -> Select:
        """Add LEFT ARRAY JOIN clause."""
        return self.array_join(expression, left=True)

    def join(
        self,
        right: Any,
        on: Optional[Any] = None,
        type_: str = "INNER"
    ) -> Select:
        """Add a JOIN clause."""
        new = self._copy()
        join = Join(
            left=new._from,
            right=_ensure_clause(right) if not isinstance(right, ClauseElement) else right,
            on=_ensure_clause(on) if on else None,
            type_=type_,
        )
        new._joins.append(join)
        return new

    def inner_join(self, right: Any, on: Any) -> Select:
        """Add an INNER JOIN."""
        return self.join(right, on, "INNER")

    def left_join(self, right: Any, on: Any) -> Select:
        """Add a LEFT JOIN."""
        return self.join(right, on, "LEFT")

    def right_join(self, right: Any, on: Any) -> Select:
        """Add a RIGHT JOIN."""
        return self.join(right, on, "RIGHT")

    def outer_join(self, right: Any, on: Any) -> Select:
        """Add a FULL OUTER JOIN."""
        return self.join(right, on, "FULL OUTER")

    def cross_join(self, right: Any) -> Select:
        """Add a CROSS JOIN."""
        return self.join(right, type_="CROSS")

    # ClickHouse-specific join types
    def any_left_join(self, right: Any, on: Any) -> Select:
        """Add an ANY LEFT JOIN (ClickHouse-specific)."""
        return self.join(right, on, "ANY LEFT")

    def any_inner_join(self, right: Any, on: Any) -> Select:
        """Add an ANY INNER JOIN (ClickHouse-specific)."""
        return self.join(right, on, "ANY INNER")

    def all_left_join(self, right: Any, on: Any) -> Select:
        """Add an ALL LEFT JOIN (ClickHouse-specific)."""
        return self.join(right, on, "ALL LEFT")

    def all_inner_join(self, right: Any, on: Any) -> Select:
        """Add an ALL INNER JOIN (ClickHouse-specific)."""
        return self.join(right, on, "ALL INNER")

    def asof_join(self, right: Any, on: Any) -> Select:
        """Add an ASOF JOIN (ClickHouse-specific for time-series)."""
        return self.join(right, on, "ASOF")

    def asof_left_join(self, right: Any, on: Any) -> Select:
        """Add an ASOF LEFT JOIN."""
        return self.join(right, on, "ASOF LEFT")

    def with_cte(self, name: str, query: Select) -> Select:
        """Add a CTE (WITH clause)."""
        new = self._copy()
        new._ctes.append((name, query))
        return new

    def settings(self, **kwargs: Any) -> Select:
        """Add query settings (ClickHouse-specific)."""
        new = self._copy()
        new._settings.update(kwargs)
        return new

    def union(self, other: Select) -> Select:
        """UNION with another SELECT (removes duplicates)."""
        new = self._copy()
        new._union = (other, "UNION")
        return new

    def union_all(self, other: Select) -> Select:
        """UNION ALL with another SELECT (keeps duplicates)."""
        new = self._copy()
        new._union = (other, "UNION ALL")
        return new

    def intersect(self, other: Select) -> Select:
        """INTERSECT with another SELECT."""
        new = self._copy()
        new._union = (other, "INTERSECT")
        return new

    def except_(self, other: Select) -> Select:
        """EXCEPT with another SELECT."""
        new = self._copy()
        new._union = (other, "EXCEPT")
        return new

    def subquery(self, alias: Optional[str] = None) -> Subquery:
        """Convert this SELECT to a subquery."""
        return Subquery(self, alias)

    def alias(self, name: str) -> Subquery:
        """Alias this SELECT as a subquery."""
        return Subquery(self, name)

    def scalar_subquery(self) -> Subquery:
        """Use this SELECT as a scalar subquery."""
        return Subquery(self)

    @property
    def c(self) -> _SelectColumnAccessor:
        """Access columns from this select for use in outer queries."""
        return _SelectColumnAccessor(self)

    def compile(self) -> str:
        """Compile the SELECT statement to SQL."""
        parts = []

        # WITH clause (CTEs)
        if self._ctes:
            cte_parts = []
            for name, query in self._ctes:
                cte_parts.append(f"{name} AS ({query.compile()})")
            parts.append("WITH " + ", ".join(cte_parts))

        # SELECT
        select_clause = "SELECT"
        if self._distinct:
            if self._distinct_on:
                on_cols = ", ".join(c.compile() for c in self._distinct_on)
                select_clause = f"SELECT DISTINCT ON ({on_cols})"
            else:
                select_clause = "SELECT DISTINCT"

        if self._columns:
            cols = ", ".join(c.compile() for c in self._columns)
            parts.append(f"{select_clause} {cols}")
        else:
            parts.append(f"{select_clause} *")

        # FROM
        if self._from is not None:
            from_sql = self._from.compile() if hasattr(self._from, 'compile') else str(self._from)
            parts.append(f"FROM {from_sql}")

        # FINAL
        if self._final:
            parts.append("FINAL")

        # SAMPLE
        if self._sample is not None:
            if isinstance(self._sample, tuple):
                parts.append(f"SAMPLE {self._sample[0]} OFFSET {self._sample[1]}")
            else:
                parts.append(f"SAMPLE {self._sample}")

        # ARRAY JOIN
        if self._array_join is not None:
            expr, is_left = self._array_join
            join_type = "LEFT ARRAY JOIN" if is_left else "ARRAY JOIN"
            parts.append(f"{join_type} {expr.compile()}")

        # JOINs
        for join in self._joins:
            parts.append(join.compile())

        # PREWHERE (ClickHouse-specific, before WHERE)
        if self._prewhere is not None:
            parts.append(f"PREWHERE {self._prewhere.compile()}")

        # WHERE
        if self._where is not None:
            parts.append(f"WHERE {self._where.compile()}")

        # GROUP BY
        if self._group_by:
            group_cols = ", ".join(c.compile() for c in self._group_by)
            parts.append(f"GROUP BY {group_cols}")

        # HAVING
        if self._having is not None:
            parts.append(f"HAVING {self._having.compile()}")

        # ORDER BY
        if self._order_by:
            order_cols = ", ".join(c.compile() for c in self._order_by)
            parts.append(f"ORDER BY {order_cols}")

        # LIMIT / OFFSET
        if self._limit is not None:
            parts.append(f"LIMIT {self._limit}")
        if self._offset is not None:
            parts.append(f"OFFSET {self._offset}")

        # SETTINGS (ClickHouse-specific)
        if self._settings:
            settings_sql = ", ".join(f"{k}={v}" for k, v in self._settings.items())
            parts.append(f"SETTINGS {settings_sql}")

        result = " ".join(parts)

        # UNION / INTERSECT / EXCEPT
        if self._union is not None:
            other, set_op = self._union
            result = f"{result} {set_op} {other.compile()}"

        return result


class _SelectColumnAccessor:
    """Access columns from a select statement."""

    def __init__(self, select: Select):
        self._select = select

    def __getattr__(self, name: str) -> ColumnClause:
        return ColumnClause(name)


class Join(ClauseElement):
    """JOIN clause."""

    def __init__(
        self,
        left: Optional[ClauseElement],
        right: ClauseElement,
        on: Optional[ClauseElement] = None,
        type_: str = "INNER",
    ):
        self.left = left
        self.right = right
        self.on = on
        self.type_ = type_

    def compile(self) -> str:
        right_sql = self.right.compile() if hasattr(self.right, 'compile') else str(self.right)

        if self.type_ == "CROSS":
            return f"CROSS JOIN {right_sql}"

        if self.on is not None:
            return f"{self.type_} JOIN {right_sql} ON {self.on.compile()}"
        return f"{self.type_} JOIN {right_sql}"


class CTE(ClauseElement):
    """Common Table Expression."""

    def __init__(self, name: str, query: Select):
        self.name = name
        self.query = query

    @property
    def c(self) -> _SelectColumnAccessor:
        """Access columns from this CTE."""
        return _SelectColumnAccessor(self.query)

    def compile(self) -> str:
        return self.name


class Alias(ColumnElement):
    """Table alias for subqueries."""

    def __init__(self, element: ClauseElement, name: str):
        self.element = element
        self.name = name

    @property
    def c(self) -> _AliasColumnAccessor:
        """Access columns via alias."""
        return _AliasColumnAccessor(self.name)

    def compile(self) -> str:
        if isinstance(self.element, Select):
            return f"({self.element.compile()}) AS {self.name}"
        return f"{self.element.compile()} AS {self.name}"


class _AliasColumnAccessor:
    """Access columns from an aliased table."""

    def __init__(self, alias_name: str):
        self._alias_name = alias_name

    def __getattr__(self, name: str) -> ColumnClause:
        return ColumnClause(name, self._alias_name)


class Values(FromClause):
    """VALUES clause for inline data."""

    def __init__(self, *rows: Sequence[Any]):
        self.rows = rows

    def compile(self) -> str:
        rows_sql = []
        for row in self.rows:
            values = ", ".join(Literal(v).compile() for v in row)
            rows_sql.append(f"({values})")
        return "VALUES " + ", ".join(rows_sql)


# Factory functions
def select(*columns: Any) -> Select:
    """Create a SELECT statement."""
    return Select(*columns)


def cte(name: str, query: Select) -> CTE:
    """Create a CTE reference."""
    return CTE(name, query)


def alias(element: ClauseElement, name: str) -> Alias:
    """Create a table alias."""
    return Alias(element, name)


def values(*rows: Sequence[Any]) -> Values:
    """Create a VALUES clause."""
    return Values(*rows)


def union(*selects: Select) -> Select:
    """Create a UNION of multiple SELECTs."""
    if not selects:
        raise ValueError("union() requires at least one SELECT")
    result = selects[0]
    for sel in selects[1:]:
        result = result.union(sel)
    return result


def union_all(*selects: Select) -> Select:
    """Create a UNION ALL of multiple SELECTs."""
    if not selects:
        raise ValueError("union_all() requires at least one SELECT")
    result = selects[0]
    for sel in selects[1:]:
        result = result.union_all(sel)
    return result


def intersect(*selects: Select) -> Select:
    """Create an INTERSECT of multiple SELECTs."""
    if not selects:
        raise ValueError("intersect() requires at least one SELECT")
    result = selects[0]
    for sel in selects[1:]:
        result = result.intersect(sel)
    return result


def except_(*selects: Select) -> Select:
    """Create an EXCEPT of multiple SELECTs."""
    if not selects:
        raise ValueError("except_() requires at least one SELECT")
    result = selects[0]
    for sel in selects[1:]:
        result = result.except_(sel)
    return result

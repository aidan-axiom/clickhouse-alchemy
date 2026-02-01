"""Base expression classes and operators."""

from __future__ import annotations
from typing import Any, List, Optional, Tuple, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from .selectable import Select


class ClauseElement:
    """Base class for all SQL clause elements."""

    def compile(self) -> str:
        """Render this element as SQL."""
        raise NotImplementedError

    def __str__(self) -> str:
        return self.compile()


class ColumnElement(ClauseElement):
    """Base class for column-like expressions."""

    # Comparison operators
    def __eq__(self, other: Any) -> BinaryExpression:
        return BinaryExpression(self, _ensure_clause(other), "=")

    def __ne__(self, other: Any) -> BinaryExpression:
        return BinaryExpression(self, _ensure_clause(other), "!=")

    def __lt__(self, other: Any) -> BinaryExpression:
        return BinaryExpression(self, _ensure_clause(other), "<")

    def __le__(self, other: Any) -> BinaryExpression:
        return BinaryExpression(self, _ensure_clause(other), "<=")

    def __gt__(self, other: Any) -> BinaryExpression:
        return BinaryExpression(self, _ensure_clause(other), ">")

    def __ge__(self, other: Any) -> BinaryExpression:
        return BinaryExpression(self, _ensure_clause(other), ">=")

    # Arithmetic operators
    def __add__(self, other: Any) -> BinaryExpression:
        return BinaryExpression(self, _ensure_clause(other), "+")

    def __radd__(self, other: Any) -> BinaryExpression:
        return BinaryExpression(_ensure_clause(other), self, "+")

    def __sub__(self, other: Any) -> BinaryExpression:
        return BinaryExpression(self, _ensure_clause(other), "-")

    def __rsub__(self, other: Any) -> BinaryExpression:
        return BinaryExpression(_ensure_clause(other), self, "-")

    def __mul__(self, other: Any) -> BinaryExpression:
        return BinaryExpression(self, _ensure_clause(other), "*")

    def __rmul__(self, other: Any) -> BinaryExpression:
        return BinaryExpression(_ensure_clause(other), self, "*")

    def __truediv__(self, other: Any) -> BinaryExpression:
        return BinaryExpression(self, _ensure_clause(other), "/")

    def __rtruediv__(self, other: Any) -> BinaryExpression:
        return BinaryExpression(_ensure_clause(other), self, "/")

    def __mod__(self, other: Any) -> BinaryExpression:
        return BinaryExpression(self, _ensure_clause(other), "%")

    def __neg__(self) -> UnaryExpression:
        return UnaryExpression(self, "-", is_prefix=True)

    # Boolean operators
    def __and__(self, other: Any) -> BinaryExpression:
        return BinaryExpression(self, _ensure_clause(other), "AND")

    def __or__(self, other: Any) -> BinaryExpression:
        return BinaryExpression(self, _ensure_clause(other), "OR")

    def __invert__(self) -> UnaryExpression:
        return UnaryExpression(self, "NOT", is_prefix=True)

    # SQL methods
    def in_(self, values: Union[List[Any], Select]) -> InExpression:
        """IN operator."""
        return InExpression(self, values, negated=False)

    def not_in(self, values: Union[List[Any], Select]) -> InExpression:
        """NOT IN operator."""
        return InExpression(self, values, negated=True)

    def like(self, pattern: str) -> BinaryExpression:
        """LIKE operator."""
        return BinaryExpression(self, literal(pattern), "LIKE")

    def ilike(self, pattern: str) -> BinaryExpression:
        """ILIKE (case-insensitive LIKE)."""
        return BinaryExpression(self, literal(pattern), "ILIKE")

    def not_like(self, pattern: str) -> BinaryExpression:
        """NOT LIKE operator."""
        return BinaryExpression(self, literal(pattern), "NOT LIKE")

    def between(self, lower: Any, upper: Any) -> BetweenExpression:
        """BETWEEN operator."""
        return BetweenExpression(self, _ensure_clause(lower), _ensure_clause(upper))

    def is_null(self) -> UnaryExpression:
        """IS NULL."""
        return UnaryExpression(self, "IS NULL", is_prefix=False)

    def is_not_null(self) -> UnaryExpression:
        """IS NOT NULL."""
        return UnaryExpression(self, "IS NOT NULL", is_prefix=False)

    def asc(self) -> OrderByElement:
        """ASC ordering."""
        return OrderByElement(self, ascending=True)

    def desc(self) -> OrderByElement:
        """DESC ordering."""
        return OrderByElement(self, ascending=False)

    def nulls_first(self) -> OrderByElement:
        """NULLS FIRST."""
        return OrderByElement(self, nulls_first=True)

    def nulls_last(self) -> OrderByElement:
        """NULLS LAST."""
        return OrderByElement(self, nulls_last=True)

    def label(self, name: str) -> Label:
        """Create an alias for this expression."""
        return Label(self, name)

    # Array operations (ClickHouse specific)
    def __getitem__(self, index: Any) -> ArrayAccess:
        """Array indexing or Map key access."""
        return ArrayAccess(self, _ensure_clause(index))

    def contains(self, value: Any) -> FunctionCall:
        """Check if array contains value (has)."""
        from .functions import has
        return has(self, value)


class BinaryExpression(ColumnElement):
    """Binary operation expression (a op b)."""

    def __init__(self, left: ClauseElement, right: ClauseElement, operator: str):
        self.left = left
        self.right = right
        self.operator = operator

    def compile(self) -> str:
        left_sql = self.left.compile()
        right_sql = self.right.compile()

        # Add parentheses for nested boolean expressions
        if isinstance(self.left, BinaryExpression) and self.left.operator in ("AND", "OR"):
            if self.operator in ("AND", "OR") and self.left.operator != self.operator:
                left_sql = f"({left_sql})"
        if isinstance(self.right, BinaryExpression) and self.right.operator in ("AND", "OR"):
            if self.operator in ("AND", "OR") and self.right.operator != self.operator:
                right_sql = f"({right_sql})"

        return f"{left_sql} {self.operator} {right_sql}"


class UnaryExpression(ColumnElement):
    """Unary operation expression."""

    def __init__(self, element: ClauseElement, operator: str, is_prefix: bool = True):
        self.element = element
        self.operator = operator
        self.is_prefix = is_prefix

    def compile(self) -> str:
        elem_sql = self.element.compile()
        if self.is_prefix:
            if self.operator == "NOT":
                return f"NOT ({elem_sql})"
            return f"{self.operator}{elem_sql}"
        return f"{elem_sql} {self.operator}"


class InExpression(ColumnElement):
    """IN / NOT IN expression."""

    def __init__(self, left: ClauseElement, values: Union[List[Any], Select], negated: bool = False):
        self.left = left
        self.values = values
        self.negated = negated

    def compile(self) -> str:
        left_sql = self.left.compile()
        op = "NOT IN" if self.negated else "IN"

        # Check if it's a subquery
        if hasattr(self.values, 'compile'):
            return f"{left_sql} {op} ({self.values.compile()})"

        # It's a list of values
        values_sql = ", ".join(_ensure_clause(v).compile() for v in self.values)
        return f"{left_sql} {op} ({values_sql})"


class BetweenExpression(ColumnElement):
    """BETWEEN expression."""

    def __init__(self, element: ClauseElement, lower: ClauseElement, upper: ClauseElement):
        self.element = element
        self.lower = lower
        self.upper = upper

    def compile(self) -> str:
        return f"{self.element.compile()} BETWEEN {self.lower.compile()} AND {self.upper.compile()}"


class OrderByElement(ColumnElement):
    """ORDER BY element with direction and nulls handling."""

    def __init__(
        self,
        element: ClauseElement,
        ascending: bool = True,
        nulls_first: bool = False,
        nulls_last: bool = False,
    ):
        self.element = element
        self.ascending = ascending
        self._nulls_first = nulls_first
        self._nulls_last = nulls_last

    def asc(self) -> OrderByElement:
        return OrderByElement(self.element, ascending=True,
                             nulls_first=self._nulls_first, nulls_last=self._nulls_last)

    def desc(self) -> OrderByElement:
        return OrderByElement(self.element, ascending=False,
                             nulls_first=self._nulls_first, nulls_last=self._nulls_last)

    def nulls_first(self) -> OrderByElement:
        return OrderByElement(self.element, ascending=self.ascending,
                             nulls_first=True, nulls_last=False)

    def nulls_last(self) -> OrderByElement:
        return OrderByElement(self.element, ascending=self.ascending,
                             nulls_first=False, nulls_last=True)

    def compile(self) -> str:
        result = self.element.compile()
        result += " ASC" if self.ascending else " DESC"
        if self._nulls_first:
            result += " NULLS FIRST"
        elif self._nulls_last:
            result += " NULLS LAST"
        return result


class Label(ColumnElement):
    """Labeled expression (AS alias)."""

    def __init__(self, element: ClauseElement, name: str):
        self.element = element
        self.name = name

    def compile(self) -> str:
        return f"{self.element.compile()} AS {self.name}"


class Literal(ColumnElement):
    """Literal value."""

    def __init__(self, value: Any):
        self.value = value

    def compile(self) -> str:
        if self.value is None:
            return "NULL"
        elif isinstance(self.value, bool):
            return "1" if self.value else "0"
        elif isinstance(self.value, str):
            escaped = self.value.replace("\\", "\\\\").replace("'", "\\'")
            return f"'{escaped}'"
        elif isinstance(self.value, (int, float)):
            return str(self.value)
        elif isinstance(self.value, (list, tuple)):
            items = ", ".join(Literal(v).compile() for v in self.value)
            return f"[{items}]"
        elif isinstance(self.value, dict):
            items = ", ".join(
                f"{Literal(k).compile()}: {Literal(v).compile()}"
                for k, v in self.value.items()
            )
            return f"{{{items}}}"
        else:
            return str(self.value)


class ColumnClause(ColumnElement):
    """A column reference."""

    def __init__(self, name: str, table: Optional[str] = None):
        self._name = name
        self._table = table

    @property
    def name(self) -> str:
        return self._name

    def compile(self) -> str:
        if self._table:
            return f"{self._table}.{self._name}"
        return self._name


class TableClause(ClauseElement):
    """A table reference."""

    def __init__(self, name: str, schema: Optional[str] = None):
        self._name = name
        self._schema = schema

    @property
    def name(self) -> str:
        return self._name

    @property
    def c(self) -> ColumnAccessor:
        """Access columns via .c.column_name."""
        return ColumnAccessor(self._name)

    def compile(self) -> str:
        if self._schema:
            return f"{self._schema}.{self._name}"
        return self._name


class ColumnAccessor:
    """Provides attribute-style column access."""

    def __init__(self, table_name: str):
        self._table_name = table_name

    def __getattr__(self, name: str) -> ColumnClause:
        return ColumnClause(name, self._table_name)


class ArrayAccess(ColumnElement):
    """Array indexing or map key access."""

    def __init__(self, array: ClauseElement, index: ClauseElement):
        self.array = array
        self.index = index

    def compile(self) -> str:
        return f"{self.array.compile()}[{self.index.compile()}]"


class FunctionCall(ColumnElement):
    """SQL function call."""

    def __init__(self, name: str, *args: Any, distinct: bool = False):
        self.name = name
        self.args = tuple(_ensure_clause(arg) for arg in args)
        self.distinct = distinct

    def compile(self) -> str:
        args_sql = ", ".join(arg.compile() for arg in self.args)
        if self.distinct:
            return f"{self.name}(DISTINCT {args_sql})"
        return f"{self.name}({args_sql})"


class Cast(ColumnElement):
    """CAST expression."""

    def __init__(self, element: Any, type_: Any):
        self.element = _ensure_clause(element)
        self.type_ = type_

    def compile(self) -> str:
        if hasattr(self.type_, 'compile'):
            type_sql = self.type_.compile()
        else:
            type_sql = str(self.type_)
        return f"CAST({self.element.compile()} AS {type_sql})"


class Case(ColumnElement):
    """CASE WHEN expression."""

    def __init__(self):
        self._whens: List[Tuple[ClauseElement, ClauseElement]] = []
        self._else: Optional[ClauseElement] = None

    def when(self, condition: Any, then: Any) -> Case:
        """Add a WHEN clause."""
        new_case = Case()
        new_case._whens = self._whens + [(_ensure_clause(condition), _ensure_clause(then))]
        new_case._else = self._else
        return new_case

    def else_(self, value: Any) -> Case:
        """Add an ELSE clause."""
        new_case = Case()
        new_case._whens = self._whens
        new_case._else = _ensure_clause(value)
        return new_case

    def compile(self) -> str:
        parts = ["CASE"]
        for condition, then in self._whens:
            parts.append(f"WHEN {condition.compile()} THEN {then.compile()}")
        if self._else is not None:
            parts.append(f"ELSE {self._else.compile()}")
        parts.append("END")
        return " ".join(parts)


class Tuple_(ColumnElement):
    """Tuple expression."""

    def __init__(self, *elements: Any):
        self.elements = tuple(_ensure_clause(e) for e in elements)

    def compile(self) -> str:
        elems_sql = ", ".join(e.compile() for e in self.elements)
        return f"({elems_sql})"


class Subquery(ColumnElement):
    """A subquery that can be used as a value."""

    def __init__(self, select: Select, alias: Optional[str] = None):
        self._select = select
        self._alias = alias

    def compile(self) -> str:
        sql = f"({self._select.compile()})"
        if self._alias:
            sql += f" AS {self._alias}"
        return sql


class Exists(ColumnElement):
    """EXISTS subquery."""

    def __init__(self, select: Select):
        self._select = select

    def compile(self) -> str:
        return f"EXISTS ({self._select.compile()})"


class All(ColumnElement):
    """ALL subquery modifier."""

    def __init__(self, select: Select):
        self._select = select

    def compile(self) -> str:
        return f"ALL ({self._select.compile()})"


class Any(ColumnElement):
    """ANY subquery modifier."""

    def __init__(self, select: Select):
        self._select = select

    def compile(self) -> str:
        return f"ANY ({self._select.compile()})"


# Helper functions
def _ensure_clause(value: Any) -> ClauseElement:
    """Convert a value to a ClauseElement if needed."""
    if isinstance(value, ClauseElement):
        return value
    return Literal(value)


def literal(value: Any) -> Literal:
    """Create a literal value."""
    return Literal(value)


def column(name: str, table: Optional[str] = None) -> ColumnClause:
    """Create a column reference."""
    return ColumnClause(name, table)


def table(name: str, schema: Optional[str] = None) -> TableClause:
    """Create a table reference."""
    return TableClause(name, schema)


def cast(element: Any, type_: Any) -> Cast:
    """Create a CAST expression."""
    return Cast(element, type_)


def case() -> Case:
    """Start building a CASE expression."""
    return Case()


def tuple_(*elements: Any) -> Tuple_:
    """Create a tuple expression."""
    return Tuple_(*elements)


def exists(select: Select) -> Exists:
    """Create an EXISTS subquery."""
    return Exists(select)


def all_(select: Select) -> All:
    """Create an ALL subquery modifier."""
    return All(select)


def any_(select: Select) -> Any:
    """Create an ANY subquery modifier."""
    return Any(select)


# Boolean combinators
def and_(*clauses: Any) -> ClauseElement:
    """Combine clauses with AND."""
    if not clauses:
        raise ValueError("and_() requires at least one argument")
    clauses = [_ensure_clause(c) for c in clauses]
    if len(clauses) == 1:
        return clauses[0]
    result = clauses[0]
    for clause in clauses[1:]:
        result = BinaryExpression(result, clause, "AND")
    return result


def or_(*clauses: Any) -> ClauseElement:
    """Combine clauses with OR."""
    if not clauses:
        raise ValueError("or_() requires at least one argument")
    clauses = [_ensure_clause(c) for c in clauses]
    if len(clauses) == 1:
        return clauses[0]
    result = clauses[0]
    for clause in clauses[1:]:
        result = BinaryExpression(result, clause, "OR")
    return result


def not_(clause: Any) -> UnaryExpression:
    """Negate a clause."""
    return UnaryExpression(_ensure_clause(clause), "NOT", is_prefix=True)


def asc(element: Any) -> OrderByElement:
    """Create ASC ordering."""
    return OrderByElement(_ensure_clause(element), ascending=True)


def desc(element: Any) -> OrderByElement:
    """Create DESC ordering."""
    return OrderByElement(_ensure_clause(element), ascending=False)


def nulls_first(element: Any) -> OrderByElement:
    """Create NULLS FIRST ordering."""
    return OrderByElement(_ensure_clause(element), nulls_first=True)


def nulls_last(element: Any) -> OrderByElement:
    """Create NULLS LAST ordering."""
    return OrderByElement(_ensure_clause(element), nulls_last=True)

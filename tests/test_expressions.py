"""Tests for SQL expressions and operators."""

import pytest

from clickhouse_alchemy import (
    literal,
    column,
    table,
    and_,
    or_,
    not_,
    cast,
    case,
    tuple_,
    exists,
    asc,
    desc,
    select,
    Column,
    Table,
    UInt64,
    String,
    Int32,
)


class TestLiteral:
    """Tests for literal values."""

    def test_literal_none(self):
        lit = literal(None)
        assert lit.compile() == 'NULL'

    def test_literal_bool_true(self):
        lit = literal(True)
        assert lit.compile() == '1'

    def test_literal_bool_false(self):
        lit = literal(False)
        assert lit.compile() == '0'

    def test_literal_int(self):
        lit = literal(42)
        assert lit.compile() == '42'

    def test_literal_float(self):
        lit = literal(3.14)
        assert lit.compile() == '3.14'

    def test_literal_string(self):
        lit = literal('hello')
        assert lit.compile() == "'hello'"

    def test_literal_string_with_quotes(self):
        lit = literal("it's")
        assert lit.compile() == "'it\\'s'"

    def test_literal_list(self):
        lit = literal([1, 2, 3])
        assert lit.compile() == '[1, 2, 3]'

    def test_literal_dict(self):
        lit = literal({'a': 1, 'b': 2})
        sql = lit.compile()
        assert "'a': 1" in sql
        assert "'b': 2" in sql


class TestComparisonOperators:
    """Tests for comparison operators."""

    def test_eq(self):
        col = column('id')
        expr = col == 5
        assert expr.compile() == 'id = 5'

    def test_ne(self):
        col = column('id')
        expr = col != 5
        assert expr.compile() == 'id != 5'

    def test_lt(self):
        col = column('id')
        expr = col < 5
        assert expr.compile() == 'id < 5'

    def test_le(self):
        col = column('id')
        expr = col <= 5
        assert expr.compile() == 'id <= 5'

    def test_gt(self):
        col = column('id')
        expr = col > 5
        assert expr.compile() == 'id > 5'

    def test_ge(self):
        col = column('id')
        expr = col >= 5
        assert expr.compile() == 'id >= 5'


class TestArithmeticOperators:
    """Tests for arithmetic operators."""

    def test_add(self):
        col = column('value')
        expr = col + 10
        assert expr.compile() == 'value + 10'

    def test_radd(self):
        col = column('value')
        expr = 10 + col
        assert expr.compile() == '10 + value'

    def test_sub(self):
        col = column('value')
        expr = col - 10
        assert expr.compile() == 'value - 10'

    def test_mul(self):
        col = column('value')
        expr = col * 2
        assert expr.compile() == 'value * 2'

    def test_div(self):
        col = column('value')
        expr = col / 2
        assert expr.compile() == 'value / 2'

    def test_mod(self):
        col = column('value')
        expr = col % 2
        assert expr.compile() == 'value % 2'

    def test_neg(self):
        col = column('value')
        expr = -col
        assert expr.compile() == '-value'


class TestBooleanOperators:
    """Tests for boolean operators."""

    def test_and_operator(self):
        expr = (column('a') > 1) & (column('b') < 10)
        assert 'AND' in expr.compile()

    def test_or_operator(self):
        expr = (column('a') > 1) | (column('b') < 10)
        assert 'OR' in expr.compile()

    def test_not_operator(self):
        expr = ~(column('active'))
        assert 'NOT' in expr.compile()

    def test_and_function(self):
        expr = and_(column('a') > 1, column('b') < 10, column('c') == 5)
        sql = expr.compile()
        assert sql.count('AND') == 2

    def test_or_function(self):
        expr = or_(column('a') > 1, column('b') < 10)
        assert 'OR' in expr.compile()

    def test_not_function(self):
        expr = not_(column('active'))
        assert 'NOT' in expr.compile()


class TestInOperator:
    """Tests for IN operator."""

    def test_in_list(self):
        col = column('status')
        expr = col.in_(['a', 'b', 'c'])
        assert expr.compile() == "status IN ('a', 'b', 'c')"

    def test_not_in_list(self):
        col = column('status')
        expr = col.not_in(['x', 'y'])
        assert expr.compile() == "status NOT IN ('x', 'y')"

    def test_in_subquery(self):
        col = column('id')
        subq = select(column('user_id')).select_from(table('orders'))
        expr = col.in_(subq)
        sql = expr.compile()
        assert 'IN' in sql
        assert 'SELECT user_id' in sql


class TestLikeOperator:
    """Tests for LIKE operator."""

    def test_like(self):
        col = column('name')
        expr = col.like('%test%')
        assert expr.compile() == "name LIKE '%test%'"

    def test_ilike(self):
        col = column('name')
        expr = col.ilike('%TEST%')
        assert expr.compile() == "name ILIKE '%TEST%'"

    def test_not_like(self):
        col = column('name')
        expr = col.not_like('%test%')
        assert expr.compile() == "name NOT LIKE '%test%'"


class TestBetweenOperator:
    """Tests for BETWEEN operator."""

    def test_between(self):
        col = column('value')
        expr = col.between(10, 20)
        assert expr.compile() == 'value BETWEEN 10 AND 20'


class TestNullOperators:
    """Tests for NULL operators."""

    def test_is_null(self):
        col = column('value')
        expr = col.is_null()
        assert expr.compile() == 'value IS NULL'

    def test_is_not_null(self):
        col = column('value')
        expr = col.is_not_null()
        assert expr.compile() == 'value IS NOT NULL'


class TestOrderingOperators:
    """Tests for ordering operators."""

    def test_asc(self):
        col = column('name')
        expr = col.asc()
        assert expr.compile() == 'name ASC'

    def test_desc(self):
        col = column('name')
        expr = col.desc()
        assert expr.compile() == 'name DESC'

    def test_asc_function(self):
        expr = asc(column('name'))
        assert expr.compile() == 'name ASC'

    def test_desc_function(self):
        expr = desc(column('name'))
        assert expr.compile() == 'name DESC'

    def test_nulls_first(self):
        col = column('name')
        expr = col.nulls_first()
        assert 'NULLS FIRST' in expr.compile()

    def test_nulls_last(self):
        col = column('name')
        expr = col.desc().nulls_last()
        sql = expr.compile()
        assert 'DESC' in sql
        assert 'NULLS LAST' in sql


class TestLabel:
    """Tests for labels/aliases."""

    def test_label(self):
        col = column('first_name')
        expr = col.label('name')
        assert expr.compile() == 'first_name AS name'


class TestCast:
    """Tests for CAST expression."""

    def test_cast_with_type_instance(self):
        expr = cast(column('value'), String())
        assert expr.compile() == 'CAST(value AS String)'

    def test_cast_function(self):
        expr = cast('123', Int32())
        assert expr.compile() == "CAST('123' AS Int32)"


class TestCase:
    """Tests for CASE expression."""

    def test_case_simple(self):
        expr = case().when(column('status') == 1, 'active').else_('inactive')
        sql = expr.compile()
        assert 'CASE' in sql
        assert 'WHEN' in sql
        assert 'THEN' in sql
        assert 'ELSE' in sql
        assert 'END' in sql

    def test_case_multiple_when(self):
        expr = (case()
                .when(column('value') < 10, 'low')
                .when(column('value') < 100, 'medium')
                .else_('high'))
        sql = expr.compile()
        assert sql.count('WHEN') == 2


class TestTuple:
    """Tests for tuple expression."""

    def test_tuple(self):
        expr = tuple_(1, 'a', 3.14)
        assert expr.compile() == "(1, 'a', 3.14)"

    def test_tuple_function(self):
        expr = tuple_(column('a'), column('b'))
        assert expr.compile() == '(a, b)'


class TestArrayAccess:
    """Tests for array access."""

    def test_array_index(self):
        col = column('arr')
        expr = col[1]
        assert expr.compile() == 'arr[1]'

    def test_array_index_expression(self):
        col = column('arr')
        expr = col[column('idx')]
        assert expr.compile() == 'arr[idx]'


class TestExists:
    """Tests for EXISTS subquery."""

    def test_exists(self):
        subq = select(literal(1)).select_from(table('users'))
        expr = exists(subq)
        sql = expr.compile()
        assert 'EXISTS' in sql
        assert 'SELECT 1' in sql

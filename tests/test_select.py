"""Tests for SELECT statement building."""

import pytest

from clickhouse_alchemy import (
    select,
    column,
    table,
    literal,
    and_,
    or_,
    func,
    union,
    union_all,
    intersect,
    except_,
    cte,
    alias,
    values,
)


class TestSelectBasic:
    """Tests for basic SELECT functionality."""

    def test_select_all(self):
        stmt = select().select_from(table('users'))
        assert stmt.compile() == 'SELECT * FROM users'

    def test_select_columns(self):
        stmt = select(column('id'), column('name')).select_from(table('users'))
        assert stmt.compile() == 'SELECT id, name FROM users'

    def test_select_with_table(self, users_table):
        stmt = select(users_table.c.id, users_table.c.name).select_from(users_table)
        assert 'SELECT users.id, users.name FROM users' == stmt.compile()

    def test_select_distinct(self):
        stmt = select(column('name')).distinct().select_from(table('users'))
        assert 'SELECT DISTINCT name' in stmt.compile()

    def test_select_distinct_on(self):
        stmt = select(column('name'), column('value')).distinct(column('name')).select_from(table('data'))
        sql = stmt.compile()
        assert 'DISTINCT ON' in sql


class TestSelectWhere:
    """Tests for SELECT WHERE clause."""

    def test_where_simple(self):
        stmt = select(column('id')).select_from(table('users')).where(column('id') > 10)
        assert 'WHERE id > 10' in stmt.compile()

    def test_where_multiple(self):
        stmt = (select(column('id'))
                .select_from(table('users'))
                .where(column('id') > 10)
                .where(column('active') == 1))
        sql = stmt.compile()
        assert 'WHERE' in sql
        assert 'AND' in sql

    def test_where_and(self):
        stmt = select(column('id')).select_from(table('users')).where(
            and_(column('id') > 10, column('active') == 1)
        )
        assert 'AND' in stmt.compile()

    def test_where_or(self):
        stmt = select(column('id')).select_from(table('users')).where(
            or_(column('status') == 'a', column('status') == 'b')
        )
        assert 'OR' in stmt.compile()


class TestSelectGroupBy:
    """Tests for SELECT GROUP BY clause."""

    def test_group_by_single(self):
        stmt = (select(column('status'), func.count())
                .select_from(table('users'))
                .group_by(column('status')))
        sql = stmt.compile()
        assert 'GROUP BY status' in sql

    def test_group_by_multiple(self):
        stmt = (select(column('a'), column('b'), func.count())
                .select_from(table('data'))
                .group_by(column('a'), column('b')))
        sql = stmt.compile()
        assert 'GROUP BY a, b' in sql

    def test_having(self):
        stmt = (select(column('status'), func.count().label('cnt'))
                .select_from(table('users'))
                .group_by(column('status'))
                .having(func.count() > 10))
        sql = stmt.compile()
        assert 'HAVING count() > 10' in sql


class TestSelectOrderBy:
    """Tests for SELECT ORDER BY clause."""

    def test_order_by_single(self):
        stmt = select(column('id')).select_from(table('users')).order_by(column('id'))
        assert 'ORDER BY id' in stmt.compile()

    def test_order_by_desc(self):
        stmt = select(column('id')).select_from(table('users')).order_by(column('id').desc())
        assert 'ORDER BY id DESC' in stmt.compile()

    def test_order_by_multiple(self):
        stmt = (select(column('id'))
                .select_from(table('users'))
                .order_by(column('name').asc(), column('id').desc()))
        sql = stmt.compile()
        assert 'ORDER BY name ASC, id DESC' in sql


class TestSelectLimitOffset:
    """Tests for SELECT LIMIT/OFFSET clause."""

    def test_limit(self):
        stmt = select(column('id')).select_from(table('users')).limit(10)
        assert 'LIMIT 10' in stmt.compile()

    def test_offset(self):
        stmt = select(column('id')).select_from(table('users')).limit(10).offset(20)
        sql = stmt.compile()
        assert 'LIMIT 10' in sql
        assert 'OFFSET 20' in sql


class TestSelectJoin:
    """Tests for SELECT JOIN clause."""

    def test_inner_join(self):
        stmt = (select(column('u.id'), column('o.amount'))
                .select_from(table('users'))
                .inner_join(table('orders'), column('orders.user_id') == column('users.id')))
        sql = stmt.compile()
        assert 'INNER JOIN orders' in sql
        assert 'ON' in sql

    def test_left_join(self):
        stmt = (select(column('id'))
                .select_from(table('users'))
                .left_join(table('orders'), column('orders.user_id') == column('users.id')))
        assert 'LEFT JOIN orders' in stmt.compile()

    def test_right_join(self):
        stmt = (select(column('id'))
                .select_from(table('users'))
                .right_join(table('orders'), column('orders.user_id') == column('users.id')))
        assert 'RIGHT JOIN orders' in stmt.compile()

    def test_cross_join(self):
        stmt = (select(column('id'))
                .select_from(table('a'))
                .cross_join(table('b')))
        assert 'CROSS JOIN b' in stmt.compile()


class TestClickHouseJoins:
    """Tests for ClickHouse-specific JOIN types."""

    def test_any_left_join(self):
        stmt = (select(column('id'))
                .select_from(table('a'))
                .any_left_join(table('b'), column('a.id') == column('b.id')))
        assert 'ANY LEFT JOIN' in stmt.compile()

    def test_any_inner_join(self):
        stmt = (select(column('id'))
                .select_from(table('a'))
                .any_inner_join(table('b'), column('a.id') == column('b.id')))
        assert 'ANY INNER JOIN' in stmt.compile()

    def test_all_left_join(self):
        stmt = (select(column('id'))
                .select_from(table('a'))
                .all_left_join(table('b'), column('a.id') == column('b.id')))
        assert 'ALL LEFT JOIN' in stmt.compile()

    def test_asof_join(self):
        stmt = (select(column('id'))
                .select_from(table('a'))
                .asof_join(table('b'), column('a.id') == column('b.id')))
        assert 'ASOF JOIN' in stmt.compile()


class TestClickHouseFeatures:
    """Tests for ClickHouse-specific SELECT features."""

    def test_final(self):
        stmt = select(column('id')).select_from(table('users')).final()
        assert 'FROM users FINAL' in stmt.compile()

    def test_sample_ratio(self):
        stmt = select(column('id')).select_from(table('users')).sample(0.1)
        assert 'SAMPLE 0.1' in stmt.compile()

    def test_sample_with_offset(self):
        stmt = select(column('id')).select_from(table('users')).sample(10, offset=5)
        sql = stmt.compile()
        assert 'SAMPLE 10' in sql
        assert 'OFFSET 5' in sql

    def test_prewhere(self):
        stmt = (select(column('id'))
                .select_from(table('users'))
                .prewhere(column('active') == 1)
                .where(column('id') > 10))
        sql = stmt.compile()
        assert 'PREWHERE active = 1' in sql
        assert 'WHERE id > 10' in sql
        # PREWHERE should come before WHERE
        assert sql.index('PREWHERE') < sql.index('WHERE')

    def test_array_join(self):
        stmt = (select(column('id'), column('tag'))
                .select_from(table('events'))
                .array_join(column('tags')))
        assert 'ARRAY JOIN tags' in stmt.compile()

    def test_left_array_join(self):
        stmt = (select(column('id'), column('tag'))
                .select_from(table('events'))
                .left_array_join(column('tags')))
        assert 'LEFT ARRAY JOIN tags' in stmt.compile()

    def test_settings(self):
        stmt = (select(column('id'))
                .select_from(table('users'))
                .settings(max_threads=4, max_memory_usage=1000000))
        sql = stmt.compile()
        assert 'SETTINGS' in sql
        assert 'max_threads=4' in sql


class TestCTE:
    """Tests for Common Table Expressions."""

    def test_with_cte(self):
        cte_query = select(column('id'), column('name')).select_from(table('users')).where(column('active') == 1)
        main_query = (select(column('id'), column('name'))
                      .with_cte('active_users', cte_query)
                      .select_from(table('active_users')))
        sql = main_query.compile()
        assert 'WITH active_users AS' in sql
        assert 'FROM active_users' in sql

    def test_multiple_ctes(self):
        cte1 = select(column('id')).select_from(table('a'))
        cte2 = select(column('id')).select_from(table('b'))
        main = (select(column('id'))
                .with_cte('cte_a', cte1)
                .with_cte('cte_b', cte2)
                .select_from(table('cte_a')))
        sql = main.compile()
        assert 'cte_a AS' in sql
        assert 'cte_b AS' in sql


class TestSetOperations:
    """Tests for UNION, INTERSECT, EXCEPT."""

    def test_union(self):
        stmt1 = select(column('id')).select_from(table('a'))
        stmt2 = select(column('id')).select_from(table('b'))
        result = stmt1.union(stmt2)
        sql = result.compile()
        assert 'UNION' in sql
        assert sql.count('SELECT') == 2

    def test_union_all(self):
        stmt1 = select(column('id')).select_from(table('a'))
        stmt2 = select(column('id')).select_from(table('b'))
        result = stmt1.union_all(stmt2)
        assert 'UNION ALL' in result.compile()

    def test_intersect(self):
        stmt1 = select(column('id')).select_from(table('a'))
        stmt2 = select(column('id')).select_from(table('b'))
        result = stmt1.intersect(stmt2)
        assert 'INTERSECT' in result.compile()

    def test_except(self):
        stmt1 = select(column('id')).select_from(table('a'))
        stmt2 = select(column('id')).select_from(table('b'))
        result = stmt1.except_(stmt2)
        assert 'EXCEPT' in result.compile()

    def test_union_function(self):
        stmt1 = select(column('id')).select_from(table('a'))
        stmt2 = select(column('id')).select_from(table('b'))
        result = union(stmt1, stmt2)
        sql = result.compile()
        assert 'UNION' in sql
        assert 'FROM a' in sql
        assert 'FROM b' in sql

    def test_union_all_function(self):
        stmt1 = select(column('id')).select_from(table('a'))
        stmt2 = select(column('id')).select_from(table('b'))
        result = union_all(stmt1, stmt2)
        assert 'UNION ALL' in result.compile()

    def test_intersect_function(self):
        stmt1 = select(column('id')).select_from(table('a'))
        stmt2 = select(column('id')).select_from(table('b'))
        result = intersect(stmt1, stmt2)
        assert 'INTERSECT' in result.compile()

    def test_except_function(self):
        stmt1 = select(column('id')).select_from(table('a'))
        stmt2 = select(column('id')).select_from(table('b'))
        result = except_(stmt1, stmt2)
        assert 'EXCEPT' in result.compile()


class TestSubquery:
    """Tests for subqueries."""

    def test_subquery(self):
        subq = select(column('user_id')).select_from(table('orders')).where(column('amount') > 100)
        stmt = select(column('name')).select_from(table('users')).where(column('id').in_(subq))
        sql = stmt.compile()
        assert 'IN (SELECT user_id' in sql

    def test_scalar_subquery(self):
        subq = select(func.max(column('amount'))).select_from(table('orders'))
        stmt = select(column('id')).select_from(table('orders')).where(column('amount') == subq.scalar_subquery())
        sql = stmt.compile()
        assert 'SELECT max(amount)' in sql

    def test_aliased_subquery(self):
        subq = select(column('id'), column('name')).select_from(table('users'))
        aliased = subq.alias('u')
        sql = aliased.compile()
        assert 'AS u' in sql


class TestSelectImmutability:
    """Tests to verify SELECT statements are immutable."""

    def test_where_creates_new_instance(self):
        stmt1 = select(column('id')).select_from(table('users'))
        stmt2 = stmt1.where(column('id') > 10)
        assert stmt1 is not stmt2
        assert 'WHERE' not in stmt1.compile()
        assert 'WHERE' in stmt2.compile()

    def test_chained_methods_independent(self):
        base = select(column('id')).select_from(table('users'))
        with_limit = base.limit(10)
        with_offset = base.offset(20)

        assert 'LIMIT' in with_limit.compile()
        assert 'LIMIT' not in with_offset.compile()
        assert 'OFFSET' in with_offset.compile()
        assert 'OFFSET' not in with_limit.compile()

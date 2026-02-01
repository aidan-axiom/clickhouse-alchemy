"""Tests for DDL statements (CREATE, DROP, etc.)."""

import pytest

from clickhouse_alchemy import (
    create_table,
    drop_table,
    Table,
    Column,
    UInt64,
    String,
    DateTime,
    Nullable,
    MergeTree,
    ReplacingMergeTree,
    Memory,
    select,
    column,
    table,
)
from clickhouse_alchemy.sql.ddl import (
    create_database,
    drop_database,
    create_view,
    create_materialized_view,
    drop_view,
)


class TestCreateTable:
    """Tests for CREATE TABLE statement."""

    def test_create_table_basic(self, users_table):
        stmt = create_table(users_table)
        sql = stmt.compile()
        assert 'CREATE TABLE users' in sql
        assert 'id UInt64' in sql
        assert 'name String' in sql

    def test_create_table_if_not_exists(self, users_table):
        stmt = create_table(users_table).if_not_exists()
        sql = stmt.compile()
        assert 'CREATE TABLE IF NOT EXISTS users' in sql

    def test_create_table_with_engine(self, users_table):
        stmt = create_table(users_table)
        sql = stmt.compile()
        assert 'ENGINE = MergeTree()' in sql

    def test_create_table_with_order_by(self, users_table):
        stmt = create_table(users_table).order_by('id')
        sql = stmt.compile()
        assert 'ORDER BY id' in sql

    def test_create_table_with_multiple_order_by(self):
        t = Table('events', Column('date', DateTime), Column('id', UInt64))
        stmt = create_table(t).engine(MergeTree()).order_by('date', 'id')
        sql = stmt.compile()
        assert 'ORDER BY (date, id)' in sql

    def test_create_table_with_partition_by(self, users_table):
        stmt = create_table(users_table).partition_by('toYYYYMM(created_at)')
        sql = stmt.compile()
        assert 'PARTITION BY toYYYYMM(created_at)' in sql

    def test_create_table_with_primary_key(self):
        t = Table('events', Column('id', UInt64), Column('ts', DateTime))
        stmt = create_table(t).engine(MergeTree()).order_by('id', 'ts').primary_key('id')
        sql = stmt.compile()
        assert 'PRIMARY KEY id' in sql

    def test_create_table_with_sample_by(self):
        t = Table('events', Column('id', UInt64))
        stmt = create_table(t).engine(MergeTree()).order_by('id').sample_by('id')
        sql = stmt.compile()
        assert 'SAMPLE BY id' in sql

    def test_create_table_with_ttl(self):
        t = Table('logs', Column('id', UInt64), Column('ts', DateTime))
        stmt = create_table(t).engine(MergeTree()).order_by('id').ttl('ts + INTERVAL 30 DAY')
        sql = stmt.compile()
        assert 'TTL ts + INTERVAL 30 DAY' in sql

    def test_create_table_with_settings(self):
        t = Table('data', Column('id', UInt64))
        stmt = create_table(t).engine(MergeTree()).order_by('id').settings(index_granularity=4096)
        sql = stmt.compile()
        assert 'SETTINGS' in sql
        assert 'index_granularity = 4096' in sql

    def test_create_table_on_cluster(self, users_table):
        stmt = create_table(users_table).on_cluster('my_cluster')
        sql = stmt.compile()
        assert 'ON CLUSTER my_cluster' in sql

    def test_create_table_temporary(self):
        t = Table('temp_data', Column('id', UInt64))
        stmt = create_table(t).temporary().engine(Memory())
        sql = stmt.compile()
        assert 'CREATE TEMPORARY TABLE temp_data' in sql

    def test_create_table_with_comment(self, users_table):
        stmt = create_table(users_table).comment('User accounts table')
        sql = stmt.compile()
        assert "COMMENT 'User accounts table'" in sql

    def test_create_table_as_select(self):
        t = Table('new_table', Column('id', UInt64))
        sel = select(column('id')).select_from(table('old_table'))
        stmt = create_table(t).engine(MergeTree()).as_select(sel)
        sql = stmt.compile()
        assert 'AS SELECT id FROM old_table' in sql

    def test_create_table_with_nullable_columns(self):
        t = Table(
            'data',
            Column('id', UInt64),
            Column('optional', Nullable(String)),
        )
        stmt = create_table(t).engine(Memory())
        sql = stmt.compile()
        assert 'Nullable(String)' in sql


class TestDropTable:
    """Tests for DROP TABLE statement."""

    def test_drop_table_basic(self, users_table):
        stmt = drop_table(users_table)
        sql = stmt.compile()
        assert 'DROP TABLE users' in sql

    def test_drop_table_if_exists(self, users_table):
        stmt = drop_table(users_table).if_exists()
        sql = stmt.compile()
        assert 'DROP TABLE IF EXISTS users' in sql

    def test_drop_table_on_cluster(self, users_table):
        stmt = drop_table(users_table).on_cluster('my_cluster')
        sql = stmt.compile()
        assert 'ON CLUSTER my_cluster' in sql

    def test_drop_table_sync(self, users_table):
        stmt = drop_table(users_table).sync()
        sql = stmt.compile()
        assert 'SYNC' in sql

    def test_drop_table_no_delay(self, users_table):
        stmt = drop_table(users_table).no_delay()
        sql = stmt.compile()
        assert 'NO DELAY' in sql

    def test_drop_table_with_schema(self):
        t = Table('users', Column('id', UInt64), schema='mydb')
        stmt = drop_table(t)
        sql = stmt.compile()
        assert 'DROP TABLE mydb.users' in sql


class TestCreateDatabase:
    """Tests for CREATE DATABASE statement."""

    def test_create_database_basic(self):
        stmt = create_database('mydb')
        sql = stmt.compile()
        assert 'CREATE DATABASE mydb' in sql

    def test_create_database_if_not_exists(self):
        stmt = create_database('mydb').if_not_exists()
        sql = stmt.compile()
        assert 'CREATE DATABASE IF NOT EXISTS mydb' in sql

    def test_create_database_on_cluster(self):
        stmt = create_database('mydb').on_cluster('my_cluster')
        sql = stmt.compile()
        assert 'ON CLUSTER my_cluster' in sql

    def test_create_database_with_engine(self):
        stmt = create_database('mydb').engine('Atomic')
        sql = stmt.compile()
        assert 'ENGINE = Atomic' in sql

    def test_create_database_with_comment(self):
        stmt = create_database('mydb').comment('Test database')
        sql = stmt.compile()
        assert "COMMENT 'Test database'" in sql


class TestDropDatabase:
    """Tests for DROP DATABASE statement."""

    def test_drop_database_basic(self):
        stmt = drop_database('mydb')
        sql = stmt.compile()
        assert 'DROP DATABASE mydb' in sql

    def test_drop_database_if_exists(self):
        stmt = drop_database('mydb').if_exists()
        sql = stmt.compile()
        assert 'DROP DATABASE IF EXISTS mydb' in sql

    def test_drop_database_on_cluster(self):
        stmt = drop_database('mydb').on_cluster('my_cluster')
        sql = stmt.compile()
        assert 'ON CLUSTER my_cluster' in sql


class TestCreateView:
    """Tests for CREATE VIEW statement."""

    def test_create_view_basic(self):
        sel = select(column('id'), column('name')).select_from(table('users'))
        stmt = create_view('active_users', sel)
        sql = stmt.compile()
        assert 'CREATE VIEW active_users' in sql
        assert 'AS SELECT' in sql

    def test_create_view_if_not_exists(self):
        sel = select(column('id')).select_from(table('users'))
        stmt = create_view('my_view', sel).if_not_exists()
        sql = stmt.compile()
        assert 'CREATE VIEW IF NOT EXISTS my_view' in sql

    def test_create_view_on_cluster(self):
        sel = select(column('id')).select_from(table('users'))
        stmt = create_view('my_view', sel).on_cluster('my_cluster')
        sql = stmt.compile()
        assert 'ON CLUSTER my_cluster' in sql


class TestCreateMaterializedView:
    """Tests for CREATE MATERIALIZED VIEW statement."""

    def test_create_materialized_view_basic(self):
        sel = select(column('id'), column('name')).select_from(table('users'))
        stmt = create_materialized_view('user_summary', sel)
        sql = stmt.compile()
        assert 'CREATE MATERIALIZED VIEW user_summary' in sql
        assert 'AS SELECT' in sql

    def test_create_materialized_view_to_table(self):
        sel = select(column('id')).select_from(table('users'))
        stmt = create_materialized_view('mv', sel).to_table('target_table')
        sql = stmt.compile()
        assert 'TO target_table' in sql

    def test_create_materialized_view_with_engine(self):
        sel = select(column('id')).select_from(table('users'))
        stmt = create_materialized_view('mv', sel).engine(MergeTree())
        sql = stmt.compile()
        assert 'ENGINE = MergeTree()' in sql

    def test_create_materialized_view_populate(self):
        sel = select(column('id')).select_from(table('users'))
        stmt = create_materialized_view('mv', sel).populate()
        sql = stmt.compile()
        assert 'POPULATE' in sql


class TestDropView:
    """Tests for DROP VIEW statement."""

    def test_drop_view_basic(self):
        stmt = drop_view('my_view')
        sql = stmt.compile()
        assert 'DROP VIEW my_view' in sql

    def test_drop_view_if_exists(self):
        stmt = drop_view('my_view').if_exists()
        sql = stmt.compile()
        assert 'DROP VIEW IF EXISTS my_view' in sql

    def test_drop_view_on_cluster(self):
        stmt = drop_view('my_view').on_cluster('my_cluster')
        sql = stmt.compile()
        assert 'ON CLUSTER my_cluster' in sql

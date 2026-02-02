"""Tests for schema definitions."""

import pytest

from clickhouse_alchemy import (
    MetaData,
    Table,
    Column,
    Index,
    UInt64,
    String,
    DateTime,
    Nullable,
    Array,
    MergeTree,
)
from clickhouse_alchemy.schema import Constraint, Projection


class TestColumn:
    """Tests for Column class."""

    def test_column_basic(self):
        col = Column('id', UInt64)
        assert col.name == 'id'
        assert col.compile() == 'id'

    def test_column_with_table(self, users_table):
        col = users_table.c.id
        assert col.compile() == 'users.id'

    def test_column_compile_definition(self):
        col = Column('name', String)
        assert col.compile_definition() == 'name String'

    def test_column_with_default(self):
        col = Column('status', String, default='active')
        defn = col.compile_definition()
        assert 'DEFAULT' in defn
        assert "'active'" in defn

    def test_column_with_server_default(self):
        col = Column('created_at', DateTime, server_default='now()')
        defn = col.compile_definition()
        assert 'DEFAULT now()' in defn

    def test_column_with_materialized(self):
        col = Column('year', UInt64, materialized='toYear(date)')
        defn = col.compile_definition()
        assert 'MATERIALIZED toYear(date)' in defn

    def test_column_with_alias(self):
        col = Column('full_name', String, alias="concat(first_name, ' ', last_name)")
        defn = col.compile_definition()
        assert 'ALIAS' in defn

    def test_column_with_codec(self):
        col = Column('data', String, codec='ZSTD(3)')
        defn = col.compile_definition()
        assert 'CODEC(ZSTD(3))' in defn

    def test_column_with_ttl(self):
        col = Column('temp_data', String, ttl='created_at + INTERVAL 1 DAY')
        defn = col.compile_definition()
        assert 'TTL created_at + INTERVAL 1 DAY' in defn

    def test_column_with_comment(self):
        col = Column('id', UInt64, comment='Primary key')
        defn = col.compile_definition()
        assert "COMMENT 'Primary key'" in defn


class TestTable:
    """Tests for Table class."""

    def test_table_basic(self):
        table = Table('users', Column('id', UInt64), Column('name', String))
        assert table.name == 'users'
        assert len(table.columns) == 2

    def test_table_with_schema(self):
        table = Table('users', Column('id', UInt64), schema='mydb')
        assert table.schema == 'mydb'
        assert table.compile() == 'mydb.users'

    def test_table_column_access_via_c(self, users_table):
        col = users_table.c.id
        assert col.name == 'id'
        assert col.compile() == 'users.id'

    def test_table_column_access_via_attr(self, users_table):
        col = users_table.id
        assert col.name == 'id'

    def test_table_column_not_found(self, users_table):
        with pytest.raises(AttributeError):
            _ = users_table.nonexistent

    def test_table_iterate_columns(self, users_table):
        col_names = [col.name for col in users_table]
        assert 'id' in col_names
        assert 'name' in col_names

    def test_table_with_engine(self):
        table = Table(
            'events',
            Column('id', UInt64),
            engine=MergeTree(order_by='id')
        )
        assert table.engine is not None
        assert table.engine.order_by == 'id'

    def test_table_with_indexes(self, indexed_table):
        assert len(indexed_table.indexes) == 2
        assert indexed_table.indexes[0].name == 'idx_name'

    def test_table_alias(self, users_table):
        aliased = users_table.alias('u')
        assert aliased.name == 'u'
        assert 'AS u' in aliased.compile()

    def test_table_alias_column_access(self, users_table):
        aliased = users_table.alias('u')
        col = aliased.c.id
        assert col.name == 'id'


class TestIndex:
    """Tests for Index class."""

    def test_index_basic(self):
        idx = Index('idx_name', 'name', type_='bloom_filter', granularity=4)
        sql = idx.compile()
        assert 'INDEX idx_name' in sql
        assert 'TYPE bloom_filter' in sql
        assert 'GRANULARITY 4' in sql

    def test_index_minmax(self):
        idx = Index('idx_value', 'value', type_='minmax', granularity=1)
        sql = idx.compile()
        assert 'TYPE minmax' in sql


class TestConstraint:
    """Tests for Constraint class."""

    def test_constraint_basic(self):
        from clickhouse_alchemy import column
        constraint = Constraint('check_positive', column('value') > 0)
        sql = constraint.compile()
        assert 'CONSTRAINT check_positive' in sql
        assert 'CHECK' in sql
        assert 'value > 0' in sql


class TestMetaData:
    """Tests for MetaData class."""

    def test_metadata_basic(self):
        metadata = MetaData()
        assert len(metadata.tables) == 0

    def test_metadata_with_schema(self):
        metadata = MetaData(schema='mydb')
        assert metadata.schema == 'mydb'

    def test_metadata_table_registration(self, metadata, users_table):
        assert 'users' in metadata.tables
        assert metadata['users'] is users_table

    def test_metadata_contains(self, metadata, users_table):
        assert 'users' in metadata
        assert 'nonexistent' not in metadata

    def test_metadata_iterate(self, metadata, users_table, orders_table):
        tables = list(metadata)
        assert len(tables) == 2

    def test_metadata_create_all(self, metadata, users_table):
        statements = metadata.create_all()
        assert len(statements) == 1
        assert 'CREATE TABLE' in statements[0]
        assert 'users' in statements[0]

    def test_metadata_drop_all(self, metadata, users_table):
        statements = metadata.drop_all()
        assert len(statements) == 1
        assert 'DROP TABLE' in statements[0]
        assert 'IF EXISTS' in statements[0]

    def test_metadata_clear(self, metadata, users_table):
        assert len(metadata.tables) == 1
        metadata.clear()
        assert len(metadata.tables) == 0


class TestTableMethods:
    """Tests for Table helper methods."""

    def test_table_select(self, users_table):
        stmt = users_table.select()
        sql = stmt.compile()
        assert 'SELECT' in sql
        assert 'FROM users' in sql

    def test_table_insert(self, users_table):
        stmt = users_table.insert()
        assert stmt._table is users_table

    def test_table_create(self, users_table):
        stmt = users_table.create()
        sql = stmt.compile()
        assert 'CREATE TABLE' in sql
        assert 'users' in sql

    def test_table_create_if_not_exists(self, users_table):
        stmt = users_table.create(if_not_exists=True)
        sql = stmt.compile()
        assert 'IF NOT EXISTS' in sql

    def test_table_drop(self, users_table):
        stmt = users_table.drop()
        sql = stmt.compile()
        assert 'DROP TABLE' in sql
        assert 'users' in sql

    def test_table_drop_if_exists(self, users_table):
        stmt = users_table.drop(if_exists=True)
        sql = stmt.compile()
        assert 'IF EXISTS' in sql

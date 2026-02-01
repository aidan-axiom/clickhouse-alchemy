"""Tests for DML statements (INSERT, ALTER TABLE, etc.)."""

import pytest

from clickhouse_alchemy import (
    insert,
    alter_table,
    optimize,
    truncate,
    select,
    column,
    table,
    literal,
    Table,
    Column,
    UInt64,
    String,
    Int32,
)


class TestInsert:
    """Tests for INSERT statement."""

    def test_insert_basic(self):
        stmt = insert(table('users'))
        sql = stmt.compile()
        assert 'INSERT INTO users' in sql

    def test_insert_with_columns(self):
        stmt = insert(table('users')).columns('id', 'name', 'email')
        sql = stmt.compile()
        assert 'INSERT INTO users' in sql
        assert '(id, name, email)' in sql

    def test_insert_with_values_tuple(self):
        stmt = insert(table('users')).columns('id', 'name').values((1, 'Alice'), (2, 'Bob'))
        sql = stmt.compile()
        assert 'VALUES' in sql
        assert "(1, 'Alice')" in sql
        assert "(2, 'Bob')" in sql

    def test_insert_with_values_dict(self):
        stmt = insert(table('users')).values({'id': 1, 'name': 'Alice'})
        sql = stmt.compile()
        assert 'INSERT INTO users' in sql
        assert 'VALUES' in sql
        assert '1' in sql
        assert "'Alice'" in sql

    def test_insert_multiple_dicts(self):
        stmt = insert(table('users')).values(
            {'id': 1, 'name': 'Alice'},
            {'id': 2, 'name': 'Bob'}
        )
        sql = stmt.compile()
        assert sql.count('(') >= 2  # At least 2 value groups

    def test_insert_from_select(self):
        sel = select(column('id'), column('name')).select_from(table('old_users'))
        stmt = insert(table('users')).from_select(['id', 'name'], sel)
        sql = stmt.compile()
        assert 'INSERT INTO users' in sql
        assert 'SELECT id, name FROM old_users' in sql

    def test_insert_with_table_object(self, users_table):
        stmt = insert(users_table).values({'id': 1, 'name': 'Test'})
        sql = stmt.compile()
        assert 'INSERT INTO users' in sql

    def test_insert_with_settings(self):
        stmt = insert(table('users')).values({'id': 1}).settings(async_insert=1)
        sql = stmt.compile()
        assert 'SETTINGS async_insert=1' in sql


class TestAlterTable:
    """Tests for ALTER TABLE statement."""

    def test_add_column(self):
        stmt = alter_table(table('users')).add_column('age', Int32())
        sql = stmt.compile()
        assert 'ALTER TABLE users' in sql
        assert 'ADD COLUMN age Int32' in sql

    def test_add_column_with_default(self):
        stmt = alter_table(table('users')).add_column('status', String(), default='active')
        sql = stmt.compile()
        assert "DEFAULT 'active'" in sql

    def test_add_column_after(self):
        stmt = alter_table(table('users')).add_column('middle_name', String(), after='first_name')
        sql = stmt.compile()
        assert 'AFTER first_name' in sql

    def test_drop_column(self):
        stmt = alter_table(table('users')).drop_column('old_field')
        sql = stmt.compile()
        assert 'DROP COLUMN old_field' in sql

    def test_modify_column(self):
        stmt = alter_table(table('users')).modify_column('age', UInt64())
        sql = stmt.compile()
        assert 'MODIFY COLUMN age UInt64' in sql

    def test_rename_column(self):
        stmt = alter_table(table('users')).rename_column('old_name', 'new_name')
        sql = stmt.compile()
        assert 'RENAME COLUMN old_name TO new_name' in sql

    def test_comment_column(self):
        stmt = alter_table(table('users')).comment_column('id', 'Primary key')
        sql = stmt.compile()
        assert "COMMENT COLUMN id 'Primary key'" in sql


class TestAlterTableMutations:
    """Tests for ALTER TABLE mutations (ClickHouse-specific UPDATE/DELETE)."""

    def test_delete_mutation(self):
        stmt = alter_table(table('users')).delete(column('id') < 100)
        sql = stmt.compile()
        assert 'ALTER TABLE users' in sql
        assert 'DELETE WHERE id < 100' in sql

    def test_update_mutation(self):
        stmt = alter_table(table('users')).update(
            {'name': 'Updated', 'status': 'modified'},
            column('id') == 1
        )
        sql = stmt.compile()
        assert 'UPDATE' in sql
        assert "name = 'Updated'" in sql
        assert 'WHERE id = 1' in sql

    def test_delete_with_table_object(self, users_table):
        stmt = alter_table(users_table).delete(users_table.c.id < 100)
        sql = stmt.compile()
        assert 'DELETE WHERE users.id < 100' in sql


class TestAlterTablePartitions:
    """Tests for ALTER TABLE partition operations."""

    def test_drop_partition(self):
        stmt = alter_table(table('events')).drop_partition('202401')
        sql = stmt.compile()
        assert 'DROP PARTITION 202401' in sql

    def test_detach_partition(self):
        stmt = alter_table(table('events')).detach_partition('202401')
        sql = stmt.compile()
        assert 'DETACH PARTITION 202401' in sql

    def test_attach_partition(self):
        stmt = alter_table(table('events')).attach_partition('202401')
        sql = stmt.compile()
        assert 'ATTACH PARTITION 202401' in sql

    def test_replace_partition(self):
        stmt = alter_table(table('events')).replace_partition('202401', 'events_staging')
        sql = stmt.compile()
        assert 'REPLACE PARTITION 202401 FROM events_staging' in sql

    def test_move_partition(self):
        stmt = alter_table(table('events')).move_partition('202401', 'events_archive')
        sql = stmt.compile()
        assert 'MOVE PARTITION 202401 TO TABLE events_archive' in sql

    def test_freeze_partition(self):
        stmt = alter_table(table('events')).freeze_partition('202401')
        sql = stmt.compile()
        assert 'FREEZE PARTITION 202401' in sql

    def test_freeze_all(self):
        stmt = alter_table(table('events')).freeze_partition()
        sql = stmt.compile()
        assert 'FREEZE' in sql


class TestAlterTableIndexes:
    """Tests for ALTER TABLE index operations."""

    def test_add_index(self):
        stmt = alter_table(table('users')).add_index(
            'idx_name', column('name'), 'bloom_filter', granularity=4
        )
        sql = stmt.compile()
        assert 'ADD INDEX idx_name' in sql
        assert 'TYPE bloom_filter' in sql
        assert 'GRANULARITY 4' in sql

    def test_drop_index(self):
        stmt = alter_table(table('users')).drop_index('idx_name')
        sql = stmt.compile()
        assert 'DROP INDEX idx_name' in sql

    def test_materialize_index(self):
        stmt = alter_table(table('users')).materialize_index('idx_name')
        sql = stmt.compile()
        assert 'MATERIALIZE INDEX idx_name' in sql

    def test_materialize_index_in_partition(self):
        stmt = alter_table(table('users')).materialize_index('idx_name', partition='202401')
        sql = stmt.compile()
        assert 'IN PARTITION 202401' in sql


class TestAlterTableTTL:
    """Tests for ALTER TABLE TTL operations."""

    def test_modify_ttl(self):
        stmt = alter_table(table('events')).modify_ttl('created_at + INTERVAL 30 DAY')
        sql = stmt.compile()
        assert 'MODIFY TTL created_at + INTERVAL 30 DAY' in sql

    def test_remove_ttl(self):
        stmt = alter_table(table('events')).remove_ttl()
        sql = stmt.compile()
        assert 'REMOVE TTL' in sql


class TestAlterTableSettings:
    """Tests for ALTER TABLE with settings."""

    def test_modify_setting(self):
        stmt = alter_table(table('users')).modify_setting(index_granularity=4096)
        sql = stmt.compile()
        assert 'MODIFY SETTING index_granularity = 4096' in sql

    def test_query_settings(self):
        stmt = alter_table(table('users')).delete(column('id') < 0).settings(mutations_sync=1)
        sql = stmt.compile()
        assert 'SETTINGS mutations_sync=1' in sql


class TestAlterTableMultipleOperations:
    """Tests for ALTER TABLE with multiple operations."""

    def test_multiple_operations(self):
        stmt = (alter_table(table('users'))
                .add_column('new_col', String())
                .drop_column('old_col'))
        sql = stmt.compile()
        assert 'ADD COLUMN new_col' in sql
        assert 'DROP COLUMN old_col' in sql
        assert ',' in sql  # Operations separated by comma


class TestOptimize:
    """Tests for OPTIMIZE TABLE statement."""

    def test_optimize_basic(self):
        stmt = optimize(table('users'))
        sql = stmt.compile()
        assert 'OPTIMIZE TABLE users' in sql

    def test_optimize_partition(self):
        stmt = optimize(table('events')).partition('202401')
        sql = stmt.compile()
        assert 'PARTITION 202401' in sql

    def test_optimize_final(self):
        stmt = optimize(table('users')).final()
        sql = stmt.compile()
        assert 'FINAL' in sql

    def test_optimize_deduplicate(self):
        stmt = optimize(table('users')).deduplicate()
        sql = stmt.compile()
        assert 'DEDUPLICATE' in sql

    def test_optimize_deduplicate_by(self):
        stmt = optimize(table('users')).deduplicate('id', 'name')
        sql = stmt.compile()
        assert 'DEDUPLICATE BY id, name' in sql

    def test_optimize_full(self):
        stmt = optimize(table('events')).partition('202401').final().deduplicate()
        sql = stmt.compile()
        assert 'PARTITION 202401' in sql
        assert 'FINAL' in sql
        assert 'DEDUPLICATE' in sql


class TestTruncate:
    """Tests for TRUNCATE TABLE statement."""

    def test_truncate_basic(self):
        stmt = truncate(table('users'))
        sql = stmt.compile()
        assert 'TRUNCATE TABLE users' in sql

    def test_truncate_if_exists(self):
        stmt = truncate(table('users')).if_exists()
        sql = stmt.compile()
        assert 'TRUNCATE TABLE IF EXISTS users' in sql

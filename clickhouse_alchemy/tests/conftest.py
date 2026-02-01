"""Pytest fixtures for clickhouse_alchemy tests."""

import pytest

from clickhouse_alchemy import (
    MetaData,
    Table,
    Column,
    Index,
    UInt64,
    UInt32,
    Int32,
    String,
    DateTime,
    Float64,
    Nullable,
    Array,
    LowCardinality,
    Decimal,
    MergeTree,
    ReplacingMergeTree,
)


@pytest.fixture
def metadata():
    """Create a fresh MetaData instance."""
    return MetaData()


@pytest.fixture
def users_table(metadata):
    """Create a sample users table."""
    return Table(
        'users',
        Column('id', UInt64, primary_key=True),
        Column('name', String),
        Column('email', Nullable(String)),
        Column('age', UInt32),
        Column('created_at', DateTime),
        engine=MergeTree(order_by='id'),
        metadata=metadata,
    )


@pytest.fixture
def orders_table(metadata):
    """Create a sample orders table."""
    return Table(
        'orders',
        Column('id', UInt64, primary_key=True),
        Column('user_id', UInt64),
        Column('amount', Decimal(18, 2)),
        Column('status', LowCardinality(String)),
        Column('created_at', DateTime),
        engine=ReplacingMergeTree(ver='id'),
        metadata=metadata,
    )


@pytest.fixture
def events_table(metadata):
    """Create a sample events table with complex types."""
    return Table(
        'events',
        Column('id', UInt64),
        Column('event_type', String),
        Column('tags', Array(String)),
        Column('properties', Nullable(String)),
        Column('timestamp', DateTime),
        engine=MergeTree(order_by='id'),
        metadata=metadata,
    )


@pytest.fixture
def indexed_table():
    """Create a table with indexes."""
    return Table(
        'indexed_data',
        Column('id', UInt64),
        Column('name', String),
        Column('value', Float64),
        indexes=[
            Index('idx_name', 'name', type_='bloom_filter', granularity=4),
            Index('idx_value', 'value', type_='minmax', granularity=1),
        ],
        engine=MergeTree(order_by='id'),
    )

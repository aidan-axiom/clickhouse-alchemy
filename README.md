# ClickHouse Alchemy

A SQLAlchemy Core-style library for building ClickHouse SQL statements in Python.

## Installation

```bash
pip install clickhouse-alchemy
```

## Quick Start

```python
from clickhouse_alchemy import (
    create_engine, MetaData, Table, Column,
    UInt64, String, DateTime, Nullable, Array,
    MergeTree, select, insert, func
)

# Create engine
engine = create_engine("clickhouse://localhost:8123/default")

# Define table
users = Table(
    "users",
    Column("id", UInt64),
    Column("name", String),
    Column("email", Nullable(String)),
    Column("tags", Array(String)),
    Column("created_at", DateTime),
    engine=MergeTree(order_by="id"),
)

# Execute queries
with engine.connect() as conn:
    # Create table
    conn.execute(users.create(if_not_exists=True))

    # Insert data (efficient bulk insert)
    conn.insert(users, [
        {"id": 1, "name": "Alice", "email": "alice@example.com", "tags": ["admin"]},
        {"id": 2, "name": "Bob", "email": None, "tags": ["user"]},
    ])

    # Query data
    stmt = (
        select(users.c.id, users.c.name, func.length(users.c.name).label("name_len"))
        .where(users.c.id > 0)
        .order_by(users.c.name)
        .limit(10)
    )
    result = conn.execute(stmt)
    for row in result:
        print(row)
```

## Features

### Data Types

All ClickHouse types are supported:

```python
from clickhouse_alchemy import (
    # Integers
    UInt8, UInt16, UInt32, UInt64, UInt128, UInt256,
    Int8, Int16, Int32, Int64, Int128, Int256,
    # Floats
    Float32, Float64,
    # Strings
    String, FixedString,
    # Date/Time
    Date, Date32, DateTime, DateTime64,
    # Special
    UUID, IPv4, IPv6, Boolean, Decimal,
    # Enums
    Enum8, Enum16,
    # Composites
    Array, Nullable, LowCardinality, Tuple, Map, Nested,
)

# Examples
Column("id", UInt64)
Column("name", LowCardinality(String))
Column("email", Nullable(String))
Column("tags", Array(String))
Column("metadata", Map(String, String))
Column("coords", Tuple(Float64, Float64))
Column("created_at", DateTime(timezone="UTC"))
Column("price", Decimal(18, 2))
```

### Table Engines

```python
from clickhouse_alchemy import (
    MergeTree, ReplacingMergeTree, SummingMergeTree,
    AggregatingMergeTree, CollapsingMergeTree,
    VersionedCollapsingMergeTree, ReplicatedMergeTree,
    Memory, Log, TinyLog, Distributed,
)

# MergeTree with options
Table(
    "events",
    Column("date", Date),
    Column("id", UInt64),
    Column("value", Float64),
    engine=MergeTree(
        order_by=("date", "id"),
        partition_by="toYYYYMM(date)",
        settings={"index_granularity": 8192},
    ),
)

# ReplacingMergeTree for deduplication
Table(
    "users",
    Column("id", UInt64),
    Column("version", UInt64),
    engine=ReplacingMergeTree(ver="version"),
)

# Distributed table
Table(
    "events_distributed",
    Column("id", UInt64),
    engine=Distributed(
        cluster="my_cluster",
        database="default",
        table="events_local",
        sharding_key="rand()",
    ),
)
```

### SELECT Queries

```python
from clickhouse_alchemy import select, column, table, and_, or_, func

# Basic select
stmt = select(users.c.id, users.c.name).select_from(users)

# With WHERE
stmt = select(users.c.id).where(users.c.age > 18)

# Multiple conditions
stmt = select(users.c.id).where(
    and_(
        users.c.age >= 18,
        users.c.status.in_(["active", "pending"]),
    )
)

# JOIN
stmt = (
    select(users.c.name, func.sum(orders.c.amount))
    .select_from(users)
    .left_join(orders, orders.c.user_id == users.c.id)
    .group_by(users.c.name)
    .having(func.sum(orders.c.amount) > 100)
)

# ORDER BY, LIMIT, OFFSET
stmt = (
    select(users.c.id)
    .order_by(users.c.created_at.desc())
    .limit(10)
    .offset(20)
)

# DISTINCT
stmt = select(users.c.status).distinct()

# Subquery
subq = select(orders.c.user_id).where(orders.c.amount > 1000)
stmt = select(users.c.name).where(users.c.id.in_(subq))

# CTE (Common Table Expression)
cte_query = select(users.c.id).where(users.c.active == 1)
stmt = (
    select(column("id"))
    .with_cte("active_users", cte_query)
    .select_from(table("active_users"))
)

# UNION / INTERSECT / EXCEPT
stmt1 = select(users.c.id).where(users.c.type == "a")
stmt2 = select(users.c.id).where(users.c.type == "b")
combined = stmt1.union_all(stmt2)
```

### ClickHouse-Specific Features

```python
# FINAL (for ReplacingMergeTree, etc.)
stmt = select(users.c.id).select_from(users).final()

# PREWHERE (early filtering)
stmt = (
    select(users.c.id)
    .select_from(users)
    .prewhere(users.c.date > "2024-01-01")
    .where(users.c.status == "active")
)

# SAMPLE
stmt = select(users.c.id).select_from(users).sample(0.1)  # 10% sample

# ARRAY JOIN
stmt = (
    select(events.c.id, column("tag"))
    .select_from(events)
    .array_join(events.c.tags)
)

# Query SETTINGS
stmt = (
    select(users.c.id)
    .settings(max_threads=4, max_memory_usage=10000000000)
)

# ClickHouse-specific JOINs
stmt = select(a.c.id).any_left_join(b, a.c.id == b.c.id)
stmt = select(a.c.id).asof_join(b, a.c.ts == b.c.ts)
```

### INSERT

```python
from clickhouse_alchemy import insert

# Insert with values
stmt = insert(users).values(
    {"id": 1, "name": "Alice"},
    {"id": 2, "name": "Bob"},
)
conn.execute(stmt)

# Efficient bulk insert (uses native protocol)
conn.insert(users, [
    {"id": 1, "name": "Alice"},
    {"id": 2, "name": "Bob"},
    # ... thousands of rows
])

# Insert from SELECT
stmt = insert(users_backup).from_select(
    ["id", "name"],
    select(users.c.id, users.c.name).where(users.c.active == 1)
)
```

### ALTER TABLE (Mutations)

ClickHouse doesn't have traditional UPDATE/DELETE. Use ALTER TABLE mutations instead:

```python
from clickhouse_alchemy import alter_table

# DELETE rows
stmt = alter_table(users).delete(users.c.status == "deleted")

# UPDATE rows
stmt = alter_table(users).update(
    {"status": "inactive"},
    users.c.last_login < "2023-01-01"
)

# Add/Drop columns
stmt = alter_table(users).add_column("new_field", String(), after="name")
stmt = alter_table(users).drop_column("old_field")

# Partition operations
stmt = alter_table(events).drop_partition("202301")
stmt = alter_table(events).detach_partition("202301")
```

### DDL

```python
from clickhouse_alchemy import create_table, drop_table

# CREATE TABLE
stmt = (
    create_table(users)
    .if_not_exists()
    .order_by("id")
    .partition_by("toYYYYMM(created_at)")
    .settings(index_granularity=8192)
)

# CREATE TABLE ... AS SELECT
stmt = create_table(users_backup).as_select(
    select(users.c.id, users.c.name).where(users.c.active == 1)
)

# ON CLUSTER for distributed DDL
stmt = create_table(users).on_cluster("my_cluster")

# DROP TABLE
stmt = drop_table(users).if_exists()

# CREATE/DROP DATABASE
from clickhouse_alchemy.sql.ddl import create_database, drop_database
stmt = create_database("mydb").if_not_exists()

# CREATE MATERIALIZED VIEW
from clickhouse_alchemy.sql.ddl import create_materialized_view
stmt = create_materialized_view(
    "hourly_stats",
    select(
        func.toStartOfHour(events.c.timestamp).label("hour"),
        func.count().label("cnt"),
    ).group_by(func.toStartOfHour(events.c.timestamp))
).to_table("hourly_stats_data").engine(SummingMergeTree())
```

### SQL Functions

```python
from clickhouse_alchemy import func

# Aggregates
func.count()
func.sum(column("amount"))
func.avg(column("value"))
func.min(column("price"))
func.max(column("price"))
func.uniq(column("user_id"))          # Approximate distinct
func.uniq_exact(column("user_id"))    # Exact distinct
func.quantile(0.95, column("latency"))
func.group_array(column("name"))

# String functions
func.length(column("name"))
func.lower(column("name"))
func.upper(column("name"))
func.concat(column("first"), " ", column("last"))
func.substring(column("text"), 1, 10)

# Date/Time functions
func.now()
func.today()
func.to_date(column("datetime"))
func.to_year(column("date"))
func.to_month(column("date"))
func.date_diff("day", column("start"), column("end"))
func.to_start_of_month(column("date"))

# Array functions
func.array(1, 2, 3)
func.has(column("tags"), "admin")
func.array_join(column("tags"))
func.index_of(column("arr"), "value")

# Conditional
func.if_(column("x") > 0, "positive", "non-positive")
func.coalesce(column("a"), column("b"), 0)
func.if_null(column("value"), 0)

# H3 geospatial functions
func.geo_to_h3(column("lat"), column("lon"), 10)  # Convert coords to H3 index
func.h3_to_geo(column("h3index"))                  # Get cell centroid
func.h3_to_parent(column("h3index"), 5)            # Get parent at resolution 5
func.h3_to_children(column("h3index"), 12)         # Get children at resolution 12
func.h3_k_ring(column("h3index"), 3)               # Get neighbors within distance 3
func.h3_distance(column("h3a"), column("h3b"))     # Grid distance between cells
func.h3_is_valid(column("h3index"))                # Validate H3 index

# Type conversion
func.to_uint64(column("str_id"))
func.to_string(column("id"))
func.to_datetime(column("timestamp_str"))
```

### Table Reflection

```python
from clickhouse_alchemy import MetaData, create_engine

engine = create_engine("clickhouse://localhost/mydb")
metadata = MetaData()

# Reflect all tables
metadata.reflect(engine)

# Access reflected tables
users = metadata.tables["users"]
print(users.columns)

# Reflect specific tables only
metadata.reflect(engine, only=["users", "orders"])
```

### Connection URL Formats

```python
# Basic
engine = create_engine("clickhouse://localhost/default")

# With port
engine = create_engine("clickhouse://localhost:8123/default")

# With credentials
engine = create_engine("clickhouse://user:password@localhost/default")

# HTTPS (secure)
engine = create_engine("clickhouse+https://host:8443/default")

# With options
engine = create_engine(
    "clickhouse://localhost/default",
    echo=True,  # Log SQL statements
    send_receive_timeout=30,
)
```

## Expression Operators

```python
# Comparison
column("id") == 1
column("id") != 1
column("id") > 1
column("id") >= 1
column("id") < 1
column("id") <= 1

# IN / NOT IN
column("status").in_(["a", "b", "c"])
column("status").not_in(["x", "y"])

# LIKE
column("name").like("%test%")
column("name").ilike("%TEST%")  # Case-insensitive

# BETWEEN
column("value").between(10, 100)

# NULL checks
column("email").is_null()
column("email").is_not_null()

# Boolean
and_(cond1, cond2, cond3)
or_(cond1, cond2)
not_(condition)

# Arithmetic
column("a") + column("b")
column("a") - column("b")
column("a") * 2
column("a") / 2

# Labels
func.count().label("cnt")
column("name").label("user_name")

# Ordering
column("name").asc()
column("name").desc()
column("name").desc().nulls_last()
```

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest clickhouse_alchemy/tests/ -v

# Run with coverage
pytest --cov=clickhouse_alchemy

# Type checking
mypy clickhouse_alchemy

# Linting
ruff check clickhouse_alchemy
```

## License

MIT

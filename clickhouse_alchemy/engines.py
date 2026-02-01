"""ClickHouse table engines."""

from __future__ import annotations
from typing import Any, List, Optional, Sequence, Union


class TableEngine:
    """Base class for ClickHouse table engines."""

    def compile(self) -> str:
        """Render the engine clause as SQL."""
        raise NotImplementedError


class MergeTree(TableEngine):
    """MergeTree engine - the most universal and functional table engine."""

    def __init__(
        self,
        order_by: Optional[Union[str, Sequence[str]]] = None,
        partition_by: Optional[Union[str, Sequence[str]]] = None,
        primary_key: Optional[Union[str, Sequence[str]]] = None,
        sample_by: Optional[str] = None,
        ttl: Optional[str] = None,
        settings: Optional[dict] = None,
    ):
        self.order_by = order_by
        self.partition_by = partition_by
        self.primary_key = primary_key
        self.sample_by = sample_by
        self.ttl = ttl
        self.settings = settings or {}

    def compile(self) -> str:
        return "MergeTree()"


class ReplacingMergeTree(TableEngine):
    """ReplacingMergeTree - removes duplicates with same ORDER BY key."""

    def __init__(
        self,
        ver: Optional[str] = None,
        is_deleted: Optional[str] = None,
        order_by: Optional[Union[str, Sequence[str]]] = None,
        partition_by: Optional[Union[str, Sequence[str]]] = None,
        primary_key: Optional[Union[str, Sequence[str]]] = None,
        sample_by: Optional[str] = None,
        ttl: Optional[str] = None,
        settings: Optional[dict] = None,
    ):
        self.ver = ver
        self.is_deleted = is_deleted
        self.order_by = order_by
        self.partition_by = partition_by
        self.primary_key = primary_key
        self.sample_by = sample_by
        self.ttl = ttl
        self.settings = settings or {}

    def compile(self) -> str:
        if self.ver and self.is_deleted:
            return f"ReplacingMergeTree({self.ver}, {self.is_deleted})"
        elif self.ver:
            return f"ReplacingMergeTree({self.ver})"
        return "ReplacingMergeTree()"


class SummingMergeTree(TableEngine):
    """SummingMergeTree - replaces rows and sums numeric columns."""

    def __init__(
        self,
        columns: Optional[Sequence[str]] = None,
        order_by: Optional[Union[str, Sequence[str]]] = None,
        partition_by: Optional[Union[str, Sequence[str]]] = None,
        primary_key: Optional[Union[str, Sequence[str]]] = None,
        sample_by: Optional[str] = None,
        ttl: Optional[str] = None,
        settings: Optional[dict] = None,
    ):
        self.columns = columns
        self.order_by = order_by
        self.partition_by = partition_by
        self.primary_key = primary_key
        self.sample_by = sample_by
        self.ttl = ttl
        self.settings = settings or {}

    def compile(self) -> str:
        if self.columns:
            cols = ", ".join(self.columns)
            return f"SummingMergeTree(({cols}))"
        return "SummingMergeTree()"


class AggregatingMergeTree(TableEngine):
    """AggregatingMergeTree - for incremental data aggregation."""

    def __init__(
        self,
        order_by: Optional[Union[str, Sequence[str]]] = None,
        partition_by: Optional[Union[str, Sequence[str]]] = None,
        primary_key: Optional[Union[str, Sequence[str]]] = None,
        sample_by: Optional[str] = None,
        ttl: Optional[str] = None,
        settings: Optional[dict] = None,
    ):
        self.order_by = order_by
        self.partition_by = partition_by
        self.primary_key = primary_key
        self.sample_by = sample_by
        self.ttl = ttl
        self.settings = settings or {}

    def compile(self) -> str:
        return "AggregatingMergeTree()"


class CollapsingMergeTree(TableEngine):
    """CollapsingMergeTree - collapses rows with sign column."""

    def __init__(
        self,
        sign: str,
        order_by: Optional[Union[str, Sequence[str]]] = None,
        partition_by: Optional[Union[str, Sequence[str]]] = None,
        primary_key: Optional[Union[str, Sequence[str]]] = None,
        sample_by: Optional[str] = None,
        ttl: Optional[str] = None,
        settings: Optional[dict] = None,
    ):
        self.sign = sign
        self.order_by = order_by
        self.partition_by = partition_by
        self.primary_key = primary_key
        self.sample_by = sample_by
        self.ttl = ttl
        self.settings = settings or {}

    def compile(self) -> str:
        return f"CollapsingMergeTree({self.sign})"


class VersionedCollapsingMergeTree(TableEngine):
    """VersionedCollapsingMergeTree - collapsing with version support."""

    def __init__(
        self,
        sign: str,
        version: str,
        order_by: Optional[Union[str, Sequence[str]]] = None,
        partition_by: Optional[Union[str, Sequence[str]]] = None,
        primary_key: Optional[Union[str, Sequence[str]]] = None,
        sample_by: Optional[str] = None,
        ttl: Optional[str] = None,
        settings: Optional[dict] = None,
    ):
        self.sign = sign
        self.version = version
        self.order_by = order_by
        self.partition_by = partition_by
        self.primary_key = primary_key
        self.sample_by = sample_by
        self.ttl = ttl
        self.settings = settings or {}

    def compile(self) -> str:
        return f"VersionedCollapsingMergeTree({self.sign}, {self.version})"


class GraphiteMergeTree(TableEngine):
    """GraphiteMergeTree - for storing Graphite data."""

    def __init__(
        self,
        config_section: str,
        order_by: Optional[Union[str, Sequence[str]]] = None,
        partition_by: Optional[Union[str, Sequence[str]]] = None,
        primary_key: Optional[Union[str, Sequence[str]]] = None,
        sample_by: Optional[str] = None,
        ttl: Optional[str] = None,
        settings: Optional[dict] = None,
    ):
        self.config_section = config_section
        self.order_by = order_by
        self.partition_by = partition_by
        self.primary_key = primary_key
        self.sample_by = sample_by
        self.ttl = ttl
        self.settings = settings or {}

    def compile(self) -> str:
        return f"GraphiteMergeTree('{self.config_section}')"


# Log family engines
class Log(TableEngine):
    """Log engine - simple log storage."""

    def compile(self) -> str:
        return "Log"


class TinyLog(TableEngine):
    """TinyLog engine - simplest log storage."""

    def compile(self) -> str:
        return "TinyLog"


class StripeLog(TableEngine):
    """StripeLog engine - log with better read performance."""

    def compile(self) -> str:
        return "StripeLog"


# Special engines
class Memory(TableEngine):
    """Memory engine - stores data in RAM."""

    def compile(self) -> str:
        return "Memory"


class Buffer(TableEngine):
    """Buffer engine - buffers data in RAM before flushing to destination."""

    def __init__(
        self,
        database: str,
        table: str,
        num_layers: int = 16,
        min_time: int = 10,
        max_time: int = 100,
        min_rows: int = 10000,
        max_rows: int = 1000000,
        min_bytes: int = 10000000,
        max_bytes: int = 100000000,
    ):
        self.database = database
        self.table = table
        self.num_layers = num_layers
        self.min_time = min_time
        self.max_time = max_time
        self.min_rows = min_rows
        self.max_rows = max_rows
        self.min_bytes = min_bytes
        self.max_bytes = max_bytes

    def compile(self) -> str:
        return (
            f"Buffer({self.database}, {self.table}, {self.num_layers}, "
            f"{self.min_time}, {self.max_time}, {self.min_rows}, {self.max_rows}, "
            f"{self.min_bytes}, {self.max_bytes})"
        )


class Distributed(TableEngine):
    """Distributed engine - for distributed queries across shards."""

    def __init__(
        self,
        cluster: str,
        database: str,
        table: str,
        sharding_key: Optional[str] = None,
    ):
        self.cluster = cluster
        self.database = database
        self.table = table
        self.sharding_key = sharding_key

    def compile(self) -> str:
        if self.sharding_key:
            return f"Distributed('{self.cluster}', '{self.database}', '{self.table}', {self.sharding_key})"
        return f"Distributed('{self.cluster}', '{self.database}', '{self.table}')"


class ReplicatedMergeTree(TableEngine):
    """ReplicatedMergeTree - MergeTree with replication support."""

    def __init__(
        self,
        zoo_path: Optional[str] = None,
        replica_name: Optional[str] = None,
        order_by: Optional[Union[str, Sequence[str]]] = None,
        partition_by: Optional[Union[str, Sequence[str]]] = None,
        primary_key: Optional[Union[str, Sequence[str]]] = None,
        sample_by: Optional[str] = None,
        ttl: Optional[str] = None,
        settings: Optional[dict] = None,
    ):
        self.zoo_path = zoo_path
        self.replica_name = replica_name
        self.order_by = order_by
        self.partition_by = partition_by
        self.primary_key = primary_key
        self.sample_by = sample_by
        self.ttl = ttl
        self.settings = settings or {}

    def compile(self) -> str:
        if self.zoo_path and self.replica_name:
            return f"ReplicatedMergeTree('{self.zoo_path}', '{self.replica_name}')"
        return "ReplicatedMergeTree()"


class ReplicatedReplacingMergeTree(TableEngine):
    """ReplicatedReplacingMergeTree - ReplacingMergeTree with replication."""

    def __init__(
        self,
        zoo_path: Optional[str] = None,
        replica_name: Optional[str] = None,
        ver: Optional[str] = None,
        order_by: Optional[Union[str, Sequence[str]]] = None,
        partition_by: Optional[Union[str, Sequence[str]]] = None,
        primary_key: Optional[Union[str, Sequence[str]]] = None,
        sample_by: Optional[str] = None,
        ttl: Optional[str] = None,
        settings: Optional[dict] = None,
    ):
        self.zoo_path = zoo_path
        self.replica_name = replica_name
        self.ver = ver
        self.order_by = order_by
        self.partition_by = partition_by
        self.primary_key = primary_key
        self.sample_by = sample_by
        self.ttl = ttl
        self.settings = settings or {}

    def compile(self) -> str:
        parts = []
        if self.zoo_path and self.replica_name:
            parts.extend([f"'{self.zoo_path}'", f"'{self.replica_name}'"])
        if self.ver:
            parts.append(self.ver)
        return f"ReplicatedReplacingMergeTree({', '.join(parts)})"


class Null(TableEngine):
    """Null engine - discards all data (useful for testing)."""

    def compile(self) -> str:
        return "Null"


class URL(TableEngine):
    """URL engine - reads/writes data from/to a URL."""

    def __init__(self, url: str, format: str):
        self.url = url
        self.format = format

    def compile(self) -> str:
        return f"URL('{self.url}', '{self.format}')"


class File(TableEngine):
    """File engine - reads/writes data from/to a file."""

    def __init__(self, format: str):
        self.format = format

    def compile(self) -> str:
        return f"File('{self.format}')"


class Merge(TableEngine):
    """Merge engine - combines multiple tables into one virtual table."""

    def __init__(self, database: str, tables_regex: str):
        self.database = database
        self.tables_regex = tables_regex

    def compile(self) -> str:
        return f"Merge('{self.database}', '{self.tables_regex}')"


class Dictionary(TableEngine):
    """Dictionary engine - displays dictionary data as a table."""

    def __init__(self, dictionary_name: str):
        self.dictionary_name = dictionary_name

    def compile(self) -> str:
        return f"Dictionary('{self.dictionary_name}')"


class MaterializedView(TableEngine):
    """Placeholder for MaterializedView (not a real engine, but used in DDL)."""

    def __init__(self, to_table: Optional[str] = None):
        self.to_table = to_table

    def compile(self) -> str:
        if self.to_table:
            return f"TO {self.to_table}"
        return ""

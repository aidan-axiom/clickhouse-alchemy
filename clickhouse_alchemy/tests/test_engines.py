"""Tests for ClickHouse table engines."""

import pytest

from clickhouse_alchemy import (
    MergeTree,
    ReplacingMergeTree,
    SummingMergeTree,
    AggregatingMergeTree,
    CollapsingMergeTree,
    VersionedCollapsingMergeTree,
    GraphiteMergeTree,
    Log,
    TinyLog,
    StripeLog,
    Memory,
    Buffer,
    Distributed,
    ReplicatedMergeTree,
    ReplicatedReplacingMergeTree,
    Null,
    File,
    Merge,
    Dictionary,
)


class TestMergeTreeEngines:
    """Tests for MergeTree family engines."""

    def test_mergetree_basic(self):
        engine = MergeTree()
        assert engine.compile() == 'MergeTree()'

    def test_mergetree_with_order_by(self):
        engine = MergeTree(order_by='id')
        assert engine.compile() == 'MergeTree()'
        assert engine.order_by == 'id'

    def test_mergetree_with_partition_by(self):
        engine = MergeTree(order_by='id', partition_by='toYYYYMM(date)')
        assert engine.partition_by == 'toYYYYMM(date)'

    def test_mergetree_with_settings(self):
        engine = MergeTree(order_by='id', settings={'index_granularity': 8192})
        assert engine.settings == {'index_granularity': 8192}

    def test_replacing_mergetree_basic(self):
        engine = ReplacingMergeTree()
        assert engine.compile() == 'ReplacingMergeTree()'

    def test_replacing_mergetree_with_ver(self):
        engine = ReplacingMergeTree(ver='version')
        assert engine.compile() == 'ReplacingMergeTree(version)'

    def test_replacing_mergetree_with_is_deleted(self):
        engine = ReplacingMergeTree(ver='version', is_deleted='deleted')
        assert engine.compile() == 'ReplacingMergeTree(version, deleted)'

    def test_summing_mergetree_basic(self):
        engine = SummingMergeTree()
        assert engine.compile() == 'SummingMergeTree()'

    def test_summing_mergetree_with_columns(self):
        engine = SummingMergeTree(columns=['amount', 'count'])
        assert engine.compile() == 'SummingMergeTree((amount, count))'

    def test_aggregating_mergetree(self):
        engine = AggregatingMergeTree()
        assert engine.compile() == 'AggregatingMergeTree()'

    def test_collapsing_mergetree(self):
        engine = CollapsingMergeTree(sign='sign')
        assert engine.compile() == 'CollapsingMergeTree(sign)'

    def test_versioned_collapsing_mergetree(self):
        engine = VersionedCollapsingMergeTree(sign='sign', version='version')
        assert engine.compile() == 'VersionedCollapsingMergeTree(sign, version)'

    def test_graphite_mergetree(self):
        engine = GraphiteMergeTree(config_section='graphite_rollup')
        assert engine.compile() == "GraphiteMergeTree('graphite_rollup')"


class TestReplicatedEngines:
    """Tests for replicated engines."""

    def test_replicated_mergetree_basic(self):
        engine = ReplicatedMergeTree()
        assert engine.compile() == 'ReplicatedMergeTree()'

    def test_replicated_mergetree_with_path(self):
        engine = ReplicatedMergeTree(
            zoo_path='/clickhouse/tables/{shard}/table',
            replica_name='{replica}'
        )
        assert "ReplicatedMergeTree('/clickhouse/tables/{shard}/table', '{replica}')" == engine.compile()

    def test_replicated_replacing_mergetree(self):
        engine = ReplicatedReplacingMergeTree(
            zoo_path='/clickhouse/tables/{shard}/table',
            replica_name='{replica}',
            ver='version'
        )
        sql = engine.compile()
        assert 'ReplicatedReplacingMergeTree' in sql
        assert 'version' in sql


class TestLogEngines:
    """Tests for Log family engines."""

    def test_log(self):
        engine = Log()
        assert engine.compile() == 'Log'

    def test_tinylog(self):
        engine = TinyLog()
        assert engine.compile() == 'TinyLog'

    def test_stripelog(self):
        engine = StripeLog()
        assert engine.compile() == 'StripeLog'


class TestSpecialEngines:
    """Tests for special engines."""

    def test_memory(self):
        engine = Memory()
        assert engine.compile() == 'Memory'

    def test_null(self):
        engine = Null()
        assert engine.compile() == 'Null'

    def test_file(self):
        engine = File(format='CSV')
        assert engine.compile() == "File('CSV')"

    def test_merge(self):
        engine = Merge(database='default', tables_regex='^logs_')
        assert engine.compile() == "Merge('default', '^logs_')"

    def test_dictionary(self):
        engine = Dictionary(dictionary_name='my_dict')
        assert engine.compile() == "Dictionary('my_dict')"


class TestDistributedEngine:
    """Tests for Distributed engine."""

    def test_distributed_basic(self):
        engine = Distributed(
            cluster='my_cluster',
            database='default',
            table='local_table'
        )
        assert engine.compile() == "Distributed('my_cluster', 'default', 'local_table')"

    def test_distributed_with_sharding(self):
        engine = Distributed(
            cluster='my_cluster',
            database='default',
            table='local_table',
            sharding_key='rand()'
        )
        assert engine.compile() == "Distributed('my_cluster', 'default', 'local_table', rand())"


class TestBufferEngine:
    """Tests for Buffer engine."""

    def test_buffer_basic(self):
        engine = Buffer(
            database='default',
            table='destination',
            num_layers=16,
            min_time=10,
            max_time=100,
            min_rows=10000,
            max_rows=1000000,
            min_bytes=10000000,
            max_bytes=100000000
        )
        sql = engine.compile()
        assert 'Buffer' in sql
        assert 'default' in sql
        assert 'destination' in sql

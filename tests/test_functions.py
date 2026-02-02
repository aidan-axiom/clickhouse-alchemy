"""Tests for SQL functions."""

import pytest

from clickhouse_alchemy import func, column, select, table, interval, Interval


class TestAggregateFunctions:
    """Tests for aggregate functions."""

    def test_count(self):
        expr = func.count()
        assert expr.compile() == 'count()'

    def test_count_column(self):
        expr = func.count(column('id'))
        assert expr.compile() == 'count(id)'

    def test_count_distinct(self):
        expr = func.count_distinct(column('id'))
        assert expr.compile() == 'count(DISTINCT id)'

    def test_sum(self):
        expr = func.sum(column('amount'))
        assert expr.compile() == 'sum(amount)'

    def test_avg(self):
        expr = func.avg(column('value'))
        assert expr.compile() == 'avg(value)'

    def test_min(self):
        expr = func.min(column('value'))
        assert expr.compile() == 'min(value)'

    def test_max(self):
        expr = func.max(column('value'))
        assert expr.compile() == 'max(value)'

    def test_any(self):
        expr = func.any(column('name'))
        assert expr.compile() == 'any(name)'

    def test_any_last(self):
        expr = func.any_last(column('name'))
        assert expr.compile() == 'anyLast(name)'

    def test_group_array(self):
        expr = func.group_array(column('name'))
        assert expr.compile() == 'groupArray(name)'

    def test_group_uniq_array(self):
        expr = func.group_uniq_array(column('name'))
        assert expr.compile() == 'groupUniqArray(name)'

    def test_arg_min(self):
        expr = func.arg_min(column('name'), column('id'))
        assert expr.compile() == 'argMin(name, id)'

    def test_arg_max(self):
        expr = func.arg_max(column('name'), column('id'))
        assert expr.compile() == 'argMax(name, id)'

    def test_uniq(self):
        expr = func.uniq(column('user_id'))
        assert expr.compile() == 'uniq(user_id)'

    def test_uniq_exact(self):
        expr = func.uniq_exact(column('user_id'))
        assert expr.compile() == 'uniqExact(user_id)'

    def test_median(self):
        expr = func.median(column('value'))
        assert expr.compile() == 'median(value)'

    def test_quantile(self):
        expr = func.quantile(0.95, column('latency'))
        assert expr.compile() == 'quantile(0.95)(latency)'

    def test_stddev_pop(self):
        expr = func.stddev_pop(column('value'))
        assert expr.compile() == 'stddevPop(value)'


class TestStringFunctions:
    """Tests for string functions."""

    def test_length(self):
        expr = func.length(column('name'))
        assert expr.compile() == 'length(name)'

    def test_lower(self):
        expr = func.lower(column('name'))
        assert expr.compile() == 'lower(name)'

    def test_upper(self):
        expr = func.upper(column('name'))
        assert expr.compile() == 'upper(name)'

    def test_concat(self):
        expr = func.concat(column('first'), column('last'))
        assert expr.compile() == 'concat(first, last)'

    def test_substring(self):
        expr = func.substring(column('name'), 1, 5)
        assert expr.compile() == 'substring(name, 1, 5)'

    def test_replace(self):
        expr = func.replace(column('text'), 'old', 'new')
        assert expr.compile() == "replace(text, 'old', 'new')"

    def test_trim(self):
        expr = func.trim(column('name'))
        assert expr.compile() == 'trim(name)'

    def test_reverse(self):
        expr = func.reverse(column('name'))
        assert expr.compile() == 'reverse(name)'

    def test_match(self):
        expr = func.match(column('text'), '^hello')
        assert expr.compile() == "match(text, '^hello')"

    def test_extract(self):
        expr = func.extract(column('text'), '\\d+')
        assert 'extract(text' in expr.compile()

    def test_split_by_char(self):
        expr = func.split_by_char(',', column('tags'))
        assert expr.compile() == "splitByChar(',', tags)"


class TestArrayFunctions:
    """Tests for array functions."""

    def test_array(self):
        expr = func.array(1, 2, 3)
        assert expr.compile() == 'array(1, 2, 3)'

    def test_array_join(self):
        expr = func.array_join(column('arr'))
        assert expr.compile() == 'arrayJoin(arr)'

    def test_has(self):
        expr = func.has(column('arr'), 'value')
        assert expr.compile() == "has(arr, 'value')"

    def test_has_all(self):
        expr = func.has_all(column('arr'), column('required'))
        assert expr.compile() == 'hasAll(arr, required)'

    def test_has_any(self):
        expr = func.has_any(column('arr'), column('options'))
        assert expr.compile() == 'hasAny(arr, options)'

    def test_index_of(self):
        expr = func.index_of(column('arr'), 'value')
        assert expr.compile() == "indexOf(arr, 'value')"

    def test_array_concat(self):
        expr = func.array_concat(column('a'), column('b'))
        assert expr.compile() == 'arrayConcat(a, b)'

    def test_array_distinct(self):
        expr = func.array_distinct(column('arr'))
        assert expr.compile() == 'arrayDistinct(arr)'

    def test_array_sort(self):
        expr = func.array_sort(column('arr'))
        assert expr.compile() == 'arraySort(arr)'

    def test_range(self):
        expr = func.range(10)
        assert expr.compile() == 'range(10)'


class TestDateTimeFunctions:
    """Tests for date/time functions."""

    def test_now(self):
        expr = func.now()
        assert expr.compile() == 'now()'

    def test_today(self):
        expr = func.today()
        assert expr.compile() == 'today()'

    def test_yesterday(self):
        expr = func.yesterday()
        assert expr.compile() == 'yesterday()'

    def test_to_date(self):
        expr = func.to_date(column('datetime'))
        assert expr.compile() == 'toDate(datetime)'

    def test_to_datetime(self):
        expr = func.to_datetime(column('str'))
        assert expr.compile() == 'toDateTime(str)'

    def test_to_year(self):
        expr = func.to_year(column('date'))
        assert expr.compile() == 'toYear(date)'

    def test_to_month(self):
        expr = func.to_month(column('date'))
        assert expr.compile() == 'toMonth(date)'

    def test_to_day_of_month(self):
        expr = func.to_day_of_month(column('date'))
        assert expr.compile() == 'toDayOfMonth(date)'

    def test_to_hour(self):
        expr = func.to_hour(column('datetime'))
        assert expr.compile() == 'toHour(datetime)'

    def test_to_unix_timestamp(self):
        expr = func.to_unix_timestamp(column('datetime'))
        assert expr.compile() == 'toUnixTimestamp(datetime)'

    def test_from_unix_timestamp(self):
        expr = func.from_unix_timestamp(column('ts'))
        assert expr.compile() == 'fromUnixTimestamp(ts)'

    def test_date_add(self):
        expr = func.date_add('day', 1, column('date'))
        assert expr.compile() == "dateAdd('day', 1, date)"

    def test_date_diff(self):
        expr = func.date_diff('day', column('start'), column('end'))
        assert expr.compile() == "dateDiff('day', start, end)"

    def test_to_start_of_month(self):
        expr = func.to_start_of_month(column('date'))
        assert expr.compile() == 'toStartOfMonth(date)'

    def test_format_datetime(self):
        expr = func.format_datetime(column('dt'), '%Y-%m-%d')
        assert expr.compile() == "formatDateTime(dt, '%Y-%m-%d')"

    def test_to_start_of_interval_hour(self):
        expr = func.to_start_of_interval(column('ts'), interval(1, 'HOUR'))
        assert expr.compile() == 'toStartOfInterval(ts, INTERVAL 1 HOUR)'

    def test_to_start_of_interval_minute(self):
        expr = func.to_start_of_interval(column('ts'), interval(15, 'MINUTE'))
        assert expr.compile() == 'toStartOfInterval(ts, INTERVAL 15 MINUTE)'

    def test_to_start_of_interval_day(self):
        expr = func.to_start_of_interval(column('ts'), interval(1, 'DAY'))
        assert expr.compile() == 'toStartOfInterval(ts, INTERVAL 1 DAY)'

    def test_to_start_of_interval_with_timezone(self):
        expr = func.to_start_of_interval(column('ts'), interval(1, 'HOUR'), 'UTC')
        assert expr.compile() == "toStartOfInterval(ts, INTERVAL 1 HOUR, 'UTC')"

    def test_to_start_of_interval_with_origin(self):
        expr = func.to_start_of_interval(
            column('ts'),
            interval(1, 'DAY'),
            'UTC',
            '2023-01-01'
        )
        assert expr.compile() == "toStartOfInterval(ts, INTERVAL 1 DAY, 'UTC', '2023-01-01')"

    def test_to_start_of_interval_origin_requires_timezone(self):
        with pytest.raises(ValueError, match="timezone must be specified"):
            func.to_start_of_interval(column('ts'), interval(1, 'DAY'), origin='2023-01-01')


class TestIntervalExpression:
    """Tests for Interval expression."""

    def test_interval_hour(self):
        expr = interval(1, 'HOUR')
        assert expr.compile() == 'INTERVAL 1 HOUR'

    def test_interval_minute(self):
        expr = interval(15, 'MINUTE')
        assert expr.compile() == 'INTERVAL 15 MINUTE'

    def test_interval_day(self):
        expr = interval(7, 'DAY')
        assert expr.compile() == 'INTERVAL 7 DAY'

    def test_interval_week(self):
        expr = interval(2, 'WEEK')
        assert expr.compile() == 'INTERVAL 2 WEEK'

    def test_interval_month(self):
        expr = interval(1, 'MONTH')
        assert expr.compile() == 'INTERVAL 1 MONTH'

    def test_interval_year(self):
        expr = interval(1, 'YEAR')
        assert expr.compile() == 'INTERVAL 1 YEAR'

    def test_interval_second(self):
        expr = interval(30, 'SECOND')
        assert expr.compile() == 'INTERVAL 30 SECOND'

    def test_interval_millisecond(self):
        expr = interval(100, 'MILLISECOND')
        assert expr.compile() == 'INTERVAL 100 MILLISECOND'

    def test_interval_case_insensitive(self):
        expr = interval(1, 'hour')
        assert expr.compile() == 'INTERVAL 1 HOUR'

    def test_interval_invalid_unit(self):
        with pytest.raises(ValueError, match="Invalid interval unit"):
            interval(1, 'FORTNIGHT')

    def test_interval_with_column_value(self):
        expr = interval(column('n'), 'HOUR')
        assert expr.compile() == 'INTERVAL n HOUR'


class TestTypeConversionFunctions:
    """Tests for type conversion functions."""

    def test_to_uint64(self):
        expr = func.to_uint64(column('value'))
        assert expr.compile() == 'toUInt64(value)'

    def test_to_int32(self):
        expr = func.to_int32(column('value'))
        assert expr.compile() == 'toInt32(value)'

    def test_to_float64(self):
        expr = func.to_float64(column('value'))
        assert expr.compile() == 'toFloat64(value)'

    def test_to_string(self):
        expr = func.to_string(column('value'))
        assert expr.compile() == 'toString(value)'

    def test_to_uuid(self):
        expr = func.to_uuid(column('value'))
        assert expr.compile() == 'toUUID(value)'


class TestConditionalFunctions:
    """Tests for conditional functions."""

    def test_if(self):
        expr = func.if_(column('a') > 0, 'positive', 'non-positive')
        sql = expr.compile()
        assert 'if(' in sql

    def test_multi_if(self):
        expr = func.multi_if(
            column('x') < 0, 'negative',
            column('x') == 0, 'zero',
            'positive'
        )
        assert 'multiIf(' in expr.compile()

    def test_null_if(self):
        expr = func.null_if(column('value'), 0)
        assert expr.compile() == 'nullIf(value, 0)'

    def test_if_null(self):
        expr = func.if_null(column('value'), 0)
        assert expr.compile() == 'ifNull(value, 0)'

    def test_coalesce(self):
        expr = func.coalesce(column('a'), column('b'), 0)
        assert expr.compile() == 'coalesce(a, b, 0)'

    def test_is_null(self):
        expr = func.is_null(column('value'))
        assert expr.compile() == 'isNull(value)'

    def test_is_not_null(self):
        expr = func.is_not_null(column('value'))
        assert expr.compile() == 'isNotNull(value)'


class TestMathFunctions:
    """Tests for math functions."""

    def test_abs(self):
        expr = func.abs(column('value'))
        assert expr.compile() == 'abs(value)'

    def test_ceil(self):
        expr = func.ceil(column('value'))
        assert expr.compile() == 'ceil(value)'

    def test_floor(self):
        expr = func.floor(column('value'))
        assert expr.compile() == 'floor(value)'

    def test_round(self):
        expr = func.round(column('value'), 2)
        assert expr.compile() == 'round(value, 2)'

    def test_sqrt(self):
        expr = func.sqrt(column('value'))
        assert expr.compile() == 'sqrt(value)'

    def test_power(self):
        expr = func.power(column('base'), 2)
        assert expr.compile() == 'power(base, 2)'

    def test_log(self):
        expr = func.log(column('value'))
        assert expr.compile() == 'log(value)'

    def test_greatest(self):
        expr = func.greatest(column('a'), column('b'), column('c'))
        assert expr.compile() == 'greatest(a, b, c)'

    def test_least(self):
        expr = func.least(column('a'), column('b'))
        assert expr.compile() == 'least(a, b)'


class TestHashFunctions:
    """Tests for hash functions."""

    def test_city_hash64(self):
        expr = func.city_hash64(column('value'))
        assert expr.compile() == 'cityHash64(value)'

    def test_sip_hash64(self):
        expr = func.sip_hash64(column('value'))
        assert expr.compile() == 'sipHash64(value)'

    def test_md5(self):
        expr = func.md5(column('value'))
        assert expr.compile() == 'MD5(value)'

    def test_sha256(self):
        expr = func.sha256(column('value'))
        assert expr.compile() == 'SHA256(value)'


class TestUUIDFunctions:
    """Tests for UUID functions."""

    def test_generate_uuid_v4(self):
        expr = func.generate_uuid_v4()
        assert expr.compile() == 'generateUUIDv4()'


class TestClickHouseSpecificFunctions:
    """Tests for ClickHouse-specific functions."""

    def test_running_difference(self):
        expr = func.running_difference(column('value'))
        assert expr.compile() == 'runningDifference(value)'

    def test_neighbor(self):
        expr = func.neighbor(column('value'), -1)
        assert expr.compile() == 'neighbor(value, -1)'

    def test_neighbor_with_default(self):
        expr = func.neighbor(column('value'), -1, 0)
        assert expr.compile() == 'neighbor(value, -1, 0)'

    def test_dict_get(self):
        expr = func.dictGet('my_dict', 'value', column('key'))
        assert expr.compile() == "dictGet('my_dict', 'value', key)"


class TestWindowFunctions:
    """Tests for window functions."""

    def test_row_number(self):
        expr = func.row_number()
        assert expr.compile() == 'row_number()'

    def test_rank(self):
        expr = func.rank()
        assert expr.compile() == 'rank()'

    def test_dense_rank(self):
        expr = func.dense_rank()
        assert expr.compile() == 'dense_rank()'

    def test_lag(self):
        expr = func.lag(column('value'), 1)
        assert expr.compile() == 'lag(value, 1)'

    def test_lead(self):
        expr = func.lead(column('value'), 1)
        assert expr.compile() == 'lead(value, 1)'


class TestFunctionsInSelect:
    """Tests for using functions in SELECT statements."""

    def test_select_with_aggregates(self):
        stmt = (select(
            column('status'),
            func.count().label('cnt'),
            func.sum(column('amount')).label('total')
        )
        .select_from(table('orders'))
        .group_by(column('status')))

        sql = stmt.compile()
        assert 'count() AS cnt' in sql
        assert 'sum(amount) AS total' in sql

    def test_select_with_date_functions(self):
        stmt = select(
            func.to_date(column('created_at')).label('date'),
            func.count()
        ).select_from(table('events')).group_by(func.to_date(column('created_at')))

        sql = stmt.compile()
        assert 'toDate(created_at)' in sql

    def test_nested_functions(self):
        expr = func.round(func.avg(column('value')), 2)
        assert expr.compile() == 'round(avg(value), 2)'


class TestH3Functions:
    """Tests for H3 geospatial functions."""

    # Validation & Properties
    def test_h3_is_valid(self):
        expr = func.h3_is_valid(column('h3index'))
        assert expr.compile() == 'h3IsValid(h3index)'

    def test_h3_get_resolution(self):
        expr = func.h3_get_resolution(column('h3index'))
        assert expr.compile() == 'h3GetResolution(h3index)'

    def test_h3_get_base_cell(self):
        expr = func.h3_get_base_cell(column('h3index'))
        assert expr.compile() == 'h3GetBaseCell(h3index)'

    def test_h3_is_res_class_iii(self):
        expr = func.h3_is_res_class_iii(column('h3index'))
        assert expr.compile() == 'h3IsResClassIII(h3index)'

    def test_h3_is_pentagon(self):
        expr = func.h3_is_pentagon(column('h3index'))
        assert expr.compile() == 'h3IsPentagon(h3index)'

    def test_h3_get_faces(self):
        expr = func.h3_get_faces(column('h3index'))
        assert expr.compile() == 'h3GetFaces(h3index)'

    # Coordinate Conversion
    def test_geo_to_h3(self):
        expr = func.geo_to_h3(column('lat'), column('lon'), 10)
        assert expr.compile() == 'geoToH3(lat, lon, 10)'

    def test_h3_to_geo(self):
        expr = func.h3_to_geo(column('h3index'))
        assert expr.compile() == 'h3ToGeo(h3index)'

    def test_h3_to_geo_boundary(self):
        expr = func.h3_to_geo_boundary(column('h3index'))
        assert expr.compile() == 'h3ToGeoBoundary(h3index)'

    # String Conversion
    def test_h3_to_string(self):
        expr = func.h3_to_string(column('h3index'))
        assert expr.compile() == 'h3ToString(h3index)'

    def test_string_to_h3(self):
        expr = func.string_to_h3(column('h3str'))
        assert expr.compile() == 'stringToH3(h3str)'

    # Hierarchy
    def test_h3_to_parent(self):
        expr = func.h3_to_parent(column('h3index'), 5)
        assert expr.compile() == 'h3ToParent(h3index, 5)'

    def test_h3_to_children(self):
        expr = func.h3_to_children(column('h3index'), 12)
        assert expr.compile() == 'h3ToChildren(h3index, 12)'

    def test_h3_to_center_child(self):
        expr = func.h3_to_center_child(column('h3index'), 12)
        assert expr.compile() == 'h3ToCenterChild(h3index, 12)'

    # Measurements
    def test_h3_edge_angle(self):
        expr = func.h3_edge_angle(10)
        assert expr.compile() == 'h3EdgeAngle(10)'

    def test_h3_edge_length_m(self):
        expr = func.h3_edge_length_m(10)
        assert expr.compile() == 'h3EdgeLengthM(10)'

    def test_h3_edge_length_km(self):
        expr = func.h3_edge_length_km(10)
        assert expr.compile() == 'h3EdgeLengthKm(10)'

    def test_h3_hex_area_m2(self):
        expr = func.h3_hex_area_m2(10)
        assert expr.compile() == 'h3HexAreaM2(10)'

    def test_h3_hex_area_km2(self):
        expr = func.h3_hex_area_km2(10)
        assert expr.compile() == 'h3HexAreaKm2(10)'

    def test_h3_cell_area_m2(self):
        expr = func.h3_cell_area_m2(column('h3index'))
        assert expr.compile() == 'h3CellAreaM2(h3index)'

    def test_h3_cell_area_rads2(self):
        expr = func.h3_cell_area_rads2(column('h3index'))
        assert expr.compile() == 'h3CellAreaRads2(h3index)'

    def test_h3_exact_edge_length_m(self):
        expr = func.h3_exact_edge_length_m(column('edge'))
        assert expr.compile() == 'h3ExactEdgeLengthM(edge)'

    def test_h3_exact_edge_length_km(self):
        expr = func.h3_exact_edge_length_km(column('edge'))
        assert expr.compile() == 'h3ExactEdgeLengthKm(edge)'

    def test_h3_exact_edge_length_rads(self):
        expr = func.h3_exact_edge_length_rads(column('edge'))
        assert expr.compile() == 'h3ExactEdgeLengthRads(edge)'

    def test_h3_num_hexagons(self):
        expr = func.h3_num_hexagons(10)
        assert expr.compile() == 'h3NumHexagons(10)'

    # Distance & Neighbors
    def test_h3_k_ring(self):
        expr = func.h3_k_ring(column('h3index'), 3)
        assert expr.compile() == 'h3kRing(h3index, 3)'

    def test_h3_hex_ring(self):
        expr = func.h3_hex_ring(column('h3index'), 2)
        assert expr.compile() == 'h3HexRing(h3index, 2)'

    def test_h3_indexes_are_neighbors(self):
        expr = func.h3_indexes_are_neighbors(column('h3a'), column('h3b'))
        assert expr.compile() == 'h3IndexesAreNeighbors(h3a, h3b)'

    def test_h3_distance(self):
        expr = func.h3_distance(column('h3start'), column('h3end'))
        assert expr.compile() == 'h3Distance(h3start, h3end)'

    def test_h3_line(self):
        expr = func.h3_line(column('h3start'), column('h3end'))
        assert expr.compile() == 'h3Line(h3start, h3end)'

    def test_h3_point_dist_m(self):
        expr = func.h3_point_dist_m(column('lat1'), column('lon1'), column('lat2'), column('lon2'))
        assert expr.compile() == 'h3PointDistM(lat1, lon1, lat2, lon2)'

    def test_h3_point_dist_km(self):
        expr = func.h3_point_dist_km(column('lat1'), column('lon1'), column('lat2'), column('lon2'))
        assert expr.compile() == 'h3PointDistKm(lat1, lon1, lat2, lon2)'

    def test_h3_point_dist_rads(self):
        expr = func.h3_point_dist_rads(column('lat1'), column('lon1'), column('lat2'), column('lon2'))
        assert expr.compile() == 'h3PointDistRads(lat1, lon1, lat2, lon2)'

    # Polygon Operations
    def test_h3_polygon_to_cells(self):
        expr = func.h3_polygon_to_cells(column('polygon'), 10)
        assert expr.compile() == 'h3PolygonToCells(polygon, 10)'

    # Global Functions
    def test_h3_get_res0_indexes(self):
        expr = func.h3_get_res0_indexes()
        assert expr.compile() == 'h3GetRes0Indexes()'

    def test_h3_get_pentagon_indexes(self):
        expr = func.h3_get_pentagon_indexes(5)
        assert expr.compile() == 'h3GetPentagonIndexes(5)'

    # Unidirectional Edges
    def test_h3_get_unidirectional_edge(self):
        expr = func.h3_get_unidirectional_edge(column('origin'), column('destination'))
        assert expr.compile() == 'h3GetUnidirectionalEdge(origin, destination)'

    def test_h3_unidirectional_edge_is_valid(self):
        expr = func.h3_unidirectional_edge_is_valid(column('edge'))
        assert expr.compile() == 'h3UnidirectionalEdgeIsValid(edge)'

    def test_h3_get_origin_index_from_unidirectional_edge(self):
        expr = func.h3_get_origin_index_from_unidirectional_edge(column('edge'))
        assert expr.compile() == 'h3GetOriginIndexFromUnidirectionalEdge(edge)'

    def test_h3_get_destination_index_from_unidirectional_edge(self):
        expr = func.h3_get_destination_index_from_unidirectional_edge(column('edge'))
        assert expr.compile() == 'h3GetDestinationIndexFromUnidirectionalEdge(edge)'

    def test_h3_get_indexes_from_unidirectional_edge(self):
        expr = func.h3_get_indexes_from_unidirectional_edge(column('edge'))
        assert expr.compile() == 'h3GetIndexesFromUnidirectionalEdge(edge)'

    def test_h3_get_unidirectional_edges_from_hexagon(self):
        expr = func.h3_get_unidirectional_edges_from_hexagon(column('h3index'))
        assert expr.compile() == 'h3GetUnidirectionalEdgesFromHexagon(h3index)'

    def test_h3_get_unidirectional_edge_boundary(self):
        expr = func.h3_get_unidirectional_edge_boundary(column('edge'))
        assert expr.compile() == 'h3GetUnidirectionalEdgeBoundary(edge)'

    # Integration tests
    def test_geo_to_h3_with_literals(self):
        expr = func.geo_to_h3(37.7749, -122.4194, 9)
        assert expr.compile() == 'geoToH3(37.7749, -122.4194, 9)'

    def test_h3_in_select(self):
        stmt = select(
            func.geo_to_h3(column('lat'), column('lon'), 10).label('h3'),
            func.count().label('cnt')
        ).select_from(table('events')).group_by(
            func.geo_to_h3(column('lat'), column('lon'), 10)
        )
        sql = stmt.compile()
        assert 'geoToH3(lat, lon, 10) AS h3' in sql
        assert 'GROUP BY geoToH3(lat, lon, 10)' in sql

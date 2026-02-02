"""SQL functions for ClickHouse."""

from __future__ import annotations
from typing import Any, Union

from .expression import ClauseElement, ColumnElement, FunctionCall, _ensure_clause


def _func(name: str, *args: Any, **kwargs: Any) -> FunctionCall:
    """Helper to create a function call."""
    return FunctionCall(name, *args, **kwargs)


# Aggregate functions
def count(expr: Any = None) -> FunctionCall:
    """COUNT aggregate function."""
    if expr is None:
        return FunctionCall("count")
    return FunctionCall("count", expr)


def count_distinct(expr: Any) -> FunctionCall:
    """COUNT(DISTINCT expr)."""
    return FunctionCall("count", expr, distinct=True)


def sum(expr: Any) -> FunctionCall:
    """SUM aggregate function."""
    return FunctionCall("sum", expr)


def avg(expr: Any) -> FunctionCall:
    """AVG aggregate function."""
    return FunctionCall("avg", expr)


def min(expr: Any) -> FunctionCall:
    """MIN aggregate function."""
    return FunctionCall("min", expr)


def max(expr: Any) -> FunctionCall:
    """MAX aggregate function."""
    return FunctionCall("max", expr)


def any(expr: Any) -> FunctionCall:
    """ANY aggregate function (returns any value from group)."""
    return FunctionCall("any", expr)


def any_last(expr: Any) -> FunctionCall:
    """anyLast - returns the last value encountered."""
    return FunctionCall("anyLast", expr)


def first_value(expr: Any) -> FunctionCall:
    """first_value window function."""
    return FunctionCall("first_value", expr)


def last_value(expr: Any) -> FunctionCall:
    """last_value window function."""
    return FunctionCall("last_value", expr)


def group_array(expr: Any) -> FunctionCall:
    """groupArray - creates array from column values."""
    return FunctionCall("groupArray", expr)


def group_uniq_array(expr: Any) -> FunctionCall:
    """groupUniqArray - creates array from unique values."""
    return FunctionCall("groupUniqArray", expr)


def group_array_insert_at(expr: Any, position: Any, default: Any = None) -> FunctionCall:
    """groupArrayInsertAt - inserts value at position."""
    if default is not None:
        return FunctionCall("groupArrayInsertAt", expr, position, default)
    return FunctionCall("groupArrayInsertAt", expr, position)


def arg_min(arg: Any, val: Any) -> FunctionCall:
    """argMin - returns arg for minimum val."""
    return FunctionCall("argMin", arg, val)


def arg_max(arg: Any, val: Any) -> FunctionCall:
    """argMax - returns arg for maximum val."""
    return FunctionCall("argMax", arg, val)


def uniq(expr: Any) -> FunctionCall:
    """uniq - approximate count of distinct values."""
    return FunctionCall("uniq", expr)


def uniq_exact(expr: Any) -> FunctionCall:
    """uniqExact - exact count of distinct values."""
    return FunctionCall("uniqExact", expr)


def uniq_combined(expr: Any) -> FunctionCall:
    """uniqCombined - approximate distinct count."""
    return FunctionCall("uniqCombined", expr)


def uniq_hll12(expr: Any) -> FunctionCall:
    """uniqHLL12 - HyperLogLog distinct count."""
    return FunctionCall("uniqHLL12", expr)


def median(expr: Any) -> FunctionCall:
    """median - median value."""
    return FunctionCall("median", expr)


def quantile(level: float, expr: Any) -> FunctionCall:
    """quantile - value at given quantile level."""
    return FunctionCall(f"quantile({level})", expr)


def quantiles(*levels: float) -> "_QuantilesBuilder":
    """quantiles - multiple quantile values."""
    return _QuantilesBuilder(levels)


class _QuantilesBuilder:
    def __init__(self, levels: tuple):
        self.levels = levels

    def __call__(self, expr: Any) -> FunctionCall:
        levels_str = ", ".join(str(l) for l in self.levels)
        return FunctionCall(f"quantiles({levels_str})", expr)


def stddev_pop(expr: Any) -> FunctionCall:
    """stddevPop - population standard deviation."""
    return FunctionCall("stddevPop", expr)


def stddev_samp(expr: Any) -> FunctionCall:
    """stddevSamp - sample standard deviation."""
    return FunctionCall("stddevSamp", expr)


def var_pop(expr: Any) -> FunctionCall:
    """varPop - population variance."""
    return FunctionCall("varPop", expr)


def var_samp(expr: Any) -> FunctionCall:
    """varSamp - sample variance."""
    return FunctionCall("varSamp", expr)


def covar_pop(x: Any, y: Any) -> FunctionCall:
    """covarPop - population covariance."""
    return FunctionCall("covarPop", x, y)


def covar_samp(x: Any, y: Any) -> FunctionCall:
    """covarSamp - sample covariance."""
    return FunctionCall("covarSamp", x, y)


# String functions
def length(s: Any) -> FunctionCall:
    """length - string length in bytes."""
    return FunctionCall("length", s)


def char_length(s: Any) -> FunctionCall:
    """char_length - string length in characters."""
    return FunctionCall("char_length", s)


def lower(s: Any) -> FunctionCall:
    """lower - convert to lowercase."""
    return FunctionCall("lower", s)


def upper(s: Any) -> FunctionCall:
    """upper - convert to uppercase."""
    return FunctionCall("upper", s)


def concat(*args: Any) -> FunctionCall:
    """concat - concatenate strings."""
    return FunctionCall("concat", *args)


def substring(s: Any, offset: Any, length: Any = None) -> FunctionCall:
    """substring - extract substring."""
    if length is not None:
        return FunctionCall("substring", s, offset, length)
    return FunctionCall("substring", s, offset)


def replace(s: Any, from_: Any, to: Any) -> FunctionCall:
    """replace - replace substring."""
    return FunctionCall("replace", s, from_, to)


def trim(s: Any) -> FunctionCall:
    """trim - remove whitespace from both ends."""
    return FunctionCall("trim", s)


def ltrim(s: Any) -> FunctionCall:
    """ltrim - remove whitespace from left."""
    return FunctionCall("ltrim", s)


def rtrim(s: Any) -> FunctionCall:
    """rtrim - remove whitespace from right."""
    return FunctionCall("rtrim", s)


def reverse(s: Any) -> FunctionCall:
    """reverse - reverse string."""
    return FunctionCall("reverse", s)


def format(pattern: Any, *args: Any) -> FunctionCall:
    """format - format string with arguments."""
    return FunctionCall("format", pattern, *args)


def like(s: Any, pattern: Any) -> FunctionCall:
    """like - SQL LIKE pattern matching."""
    return FunctionCall("like", s, pattern)


def not_like(s: Any, pattern: Any) -> FunctionCall:
    """notLike - negated LIKE."""
    return FunctionCall("notLike", s, pattern)


def match(s: Any, pattern: Any) -> FunctionCall:
    """match - regex match."""
    return FunctionCall("match", s, pattern)


def extract(s: Any, pattern: Any) -> FunctionCall:
    """extract - extract regex match."""
    return FunctionCall("extract", s, pattern)


def extract_all(s: Any, pattern: Any) -> FunctionCall:
    """extractAll - extract all regex matches."""
    return FunctionCall("extractAll", s, pattern)


def split_by_char(sep: Any, s: Any) -> FunctionCall:
    """splitByChar - split string by character."""
    return FunctionCall("splitByChar", sep, s)


def split_by_string(sep: Any, s: Any) -> FunctionCall:
    """splitByString - split string by substring."""
    return FunctionCall("splitByString", sep, s)


# Array functions
def array(*elements: Any) -> FunctionCall:
    """array - create array."""
    return FunctionCall("array", *elements)


def array_join(arr: Any) -> FunctionCall:
    """arrayJoin - unfold array to rows."""
    return FunctionCall("arrayJoin", arr)


def has(arr: Any, elem: Any) -> FunctionCall:
    """has - check if array contains element."""
    return FunctionCall("has", arr, elem)


def has_all(arr: Any, elements: Any) -> FunctionCall:
    """hasAll - check if array contains all elements."""
    return FunctionCall("hasAll", arr, elements)


def has_any(arr: Any, elements: Any) -> FunctionCall:
    """hasAny - check if array contains any elements."""
    return FunctionCall("hasAny", arr, elements)


def index_of(arr: Any, elem: Any) -> FunctionCall:
    """indexOf - find element index in array."""
    return FunctionCall("indexOf", arr, elem)


def array_element(arr: Any, index: Any) -> FunctionCall:
    """arrayElement - get element at index."""
    return FunctionCall("arrayElement", arr, index)


def array_concat(*arrays: Any) -> FunctionCall:
    """arrayConcat - concatenate arrays."""
    return FunctionCall("arrayConcat", *arrays)


def array_push_back(arr: Any, elem: Any) -> FunctionCall:
    """arrayPushBack - append element."""
    return FunctionCall("arrayPushBack", arr, elem)


def array_push_front(arr: Any, elem: Any) -> FunctionCall:
    """arrayPushFront - prepend element."""
    return FunctionCall("arrayPushFront", arr, elem)


def array_pop_back(arr: Any) -> FunctionCall:
    """arrayPopBack - remove last element."""
    return FunctionCall("arrayPopBack", arr)


def array_pop_front(arr: Any) -> FunctionCall:
    """arrayPopFront - remove first element."""
    return FunctionCall("arrayPopFront", arr)


def array_slice(arr: Any, offset: Any, length: Any = None) -> FunctionCall:
    """arraySlice - slice array."""
    if length is not None:
        return FunctionCall("arraySlice", arr, offset, length)
    return FunctionCall("arraySlice", arr, offset)


def array_filter(func: Any, arr: Any) -> FunctionCall:
    """arrayFilter - filter array by lambda."""
    return FunctionCall("arrayFilter", func, arr)


def array_map(func: Any, arr: Any) -> FunctionCall:
    """arrayMap - map array with lambda."""
    return FunctionCall("arrayMap", func, arr)


def array_reduce(func: Any, arr: Any) -> FunctionCall:
    """arrayReduce - reduce array."""
    return FunctionCall("arrayReduce", func, arr)


def array_distinct(arr: Any) -> FunctionCall:
    """arrayDistinct - remove duplicates."""
    return FunctionCall("arrayDistinct", arr)


def array_sort(arr: Any) -> FunctionCall:
    """arraySort - sort array."""
    return FunctionCall("arraySort", arr)


def array_reverse_sort(arr: Any) -> FunctionCall:
    """arrayReverseSort - sort array descending."""
    return FunctionCall("arrayReverseSort", arr)


def array_flatten(arr: Any) -> FunctionCall:
    """arrayFlatten - flatten nested arrays."""
    return FunctionCall("arrayFlatten", arr)


def empty_array_uint8() -> FunctionCall:
    """emptyArrayUInt8 - empty UInt8 array."""
    return FunctionCall("emptyArrayUInt8")


def empty_array_string() -> FunctionCall:
    """emptyArrayString - empty String array."""
    return FunctionCall("emptyArrayString")


def range(n: Any) -> FunctionCall:
    """range - generate array [0, n)."""
    return FunctionCall("range", n)


# Date/Time functions
def now() -> FunctionCall:
    """now - current datetime."""
    return FunctionCall("now")


def today() -> FunctionCall:
    """today - current date."""
    return FunctionCall("today")


def yesterday() -> FunctionCall:
    """yesterday - yesterday's date."""
    return FunctionCall("yesterday")


def to_date(expr: Any) -> FunctionCall:
    """toDate - convert to Date."""
    return FunctionCall("toDate", expr)


def to_datetime(expr: Any, timezone: str = None) -> FunctionCall:
    """toDateTime - convert to DateTime."""
    if timezone:
        return FunctionCall("toDateTime", expr, timezone)
    return FunctionCall("toDateTime", expr)


def to_datetime64(expr: Any, precision: int = 3, timezone: str = None) -> FunctionCall:
    """toDateTime64 - convert to DateTime64."""
    if timezone:
        return FunctionCall("toDateTime64", expr, precision, timezone)
    return FunctionCall("toDateTime64", expr, precision)


def to_year(d: Any) -> FunctionCall:
    """toYear - extract year."""
    return FunctionCall("toYear", d)


def to_quarter(d: Any) -> FunctionCall:
    """toQuarter - extract quarter."""
    return FunctionCall("toQuarter", d)


def to_month(d: Any) -> FunctionCall:
    """toMonth - extract month."""
    return FunctionCall("toMonth", d)


def to_day_of_month(d: Any) -> FunctionCall:
    """toDayOfMonth - extract day of month."""
    return FunctionCall("toDayOfMonth", d)


def to_day_of_week(d: Any) -> FunctionCall:
    """toDayOfWeek - extract day of week."""
    return FunctionCall("toDayOfWeek", d)


def to_day_of_year(d: Any) -> FunctionCall:
    """toDayOfYear - extract day of year."""
    return FunctionCall("toDayOfYear", d)


def to_hour(d: Any) -> FunctionCall:
    """toHour - extract hour."""
    return FunctionCall("toHour", d)


def to_minute(d: Any) -> FunctionCall:
    """toMinute - extract minute."""
    return FunctionCall("toMinute", d)


def to_second(d: Any) -> FunctionCall:
    """toSecond - extract second."""
    return FunctionCall("toSecond", d)


def to_unix_timestamp(d: Any) -> FunctionCall:
    """toUnixTimestamp - convert to Unix timestamp."""
    return FunctionCall("toUnixTimestamp", d)


def from_unix_timestamp(ts: Any) -> FunctionCall:
    """fromUnixTimestamp - convert from Unix timestamp."""
    return FunctionCall("fromUnixTimestamp", ts)


def date_add(unit: str, n: Any, d: Any) -> FunctionCall:
    """dateAdd - add interval to date."""
    return FunctionCall("dateAdd", unit, n, d)


def date_sub(unit: str, n: Any, d: Any) -> FunctionCall:
    """dateSub - subtract interval from date."""
    return FunctionCall("dateSub", unit, n, d)


def date_diff(unit: str, start: Any, end: Any) -> FunctionCall:
    """dateDiff - difference between dates."""
    return FunctionCall("dateDiff", unit, start, end)


def date_trunc(unit: str, d: Any) -> FunctionCall:
    """dateTrunc - truncate date to unit."""
    return FunctionCall("dateTrunc", unit, d)


def to_start_of_day(d: Any) -> FunctionCall:
    """toStartOfDay - truncate to day start."""
    return FunctionCall("toStartOfDay", d)


def to_start_of_week(d: Any) -> FunctionCall:
    """toStartOfWeek - truncate to week start."""
    return FunctionCall("toStartOfWeek", d)


def to_start_of_month(d: Any) -> FunctionCall:
    """toStartOfMonth - truncate to month start."""
    return FunctionCall("toStartOfMonth", d)


def to_start_of_quarter(d: Any) -> FunctionCall:
    """toStartOfQuarter - truncate to quarter start."""
    return FunctionCall("toStartOfQuarter", d)


def to_start_of_year(d: Any) -> FunctionCall:
    """toStartOfYear - truncate to year start."""
    return FunctionCall("toStartOfYear", d)


def to_start_of_hour(d: Any) -> FunctionCall:
    """toStartOfHour - truncate to hour start."""
    return FunctionCall("toStartOfHour", d)


def to_start_of_minute(d: Any) -> FunctionCall:
    """toStartOfMinute - truncate to minute start."""
    return FunctionCall("toStartOfMinute", d)


def to_start_of_second(d: Any) -> FunctionCall:
    """toStartOfSecond - truncate to second start."""
    return FunctionCall("toStartOfSecond", d)


def format_datetime(d: Any, fmt: Any) -> FunctionCall:
    """formatDateTime - format datetime."""
    return FunctionCall("formatDateTime", d, fmt)


def parse_datetime(s: Any, fmt: Any) -> FunctionCall:
    """parseDateTime - parse datetime string."""
    return FunctionCall("parseDateTime", s, fmt)


# Type conversion functions
def to_uint8(expr: Any) -> FunctionCall:
    """toUInt8 - convert to UInt8."""
    return FunctionCall("toUInt8", expr)


def to_uint16(expr: Any) -> FunctionCall:
    """toUInt16 - convert to UInt16."""
    return FunctionCall("toUInt16", expr)


def to_uint32(expr: Any) -> FunctionCall:
    """toUInt32 - convert to UInt32."""
    return FunctionCall("toUInt32", expr)


def to_uint64(expr: Any) -> FunctionCall:
    """toUInt64 - convert to UInt64."""
    return FunctionCall("toUInt64", expr)


def to_int8(expr: Any) -> FunctionCall:
    """toInt8 - convert to Int8."""
    return FunctionCall("toInt8", expr)


def to_int16(expr: Any) -> FunctionCall:
    """toInt16 - convert to Int16."""
    return FunctionCall("toInt16", expr)


def to_int32(expr: Any) -> FunctionCall:
    """toInt32 - convert to Int32."""
    return FunctionCall("toInt32", expr)


def to_int64(expr: Any) -> FunctionCall:
    """toInt64 - convert to Int64."""
    return FunctionCall("toInt64", expr)


def to_float32(expr: Any) -> FunctionCall:
    """toFloat32 - convert to Float32."""
    return FunctionCall("toFloat32", expr)


def to_float64(expr: Any) -> FunctionCall:
    """toFloat64 - convert to Float64."""
    return FunctionCall("toFloat64", expr)


def to_string(expr: Any) -> FunctionCall:
    """toString - convert to String."""
    return FunctionCall("toString", expr)


def to_fixed_string(expr: Any, n: int) -> FunctionCall:
    """toFixedString - convert to FixedString."""
    return FunctionCall("toFixedString", expr, n)


def to_uuid(expr: Any) -> FunctionCall:
    """toUUID - convert to UUID."""
    return FunctionCall("toUUID", expr)


def cast(expr: Any, type_: Any) -> FunctionCall:
    """CAST - cast to type."""
    if hasattr(type_, 'compile'):
        type_str = type_.compile()
    else:
        type_str = str(type_)
    # Use special CAST syntax
    from .expression import Cast
    return Cast(expr, type_)


# Conditional functions
def if_(condition: Any, then_: Any, else_: Any) -> FunctionCall:
    """if - conditional expression."""
    return FunctionCall("if", condition, then_, else_)


def multi_if(*args: Any) -> FunctionCall:
    """multiIf - multiple conditions."""
    return FunctionCall("multiIf", *args)


def null_if(x: Any, y: Any) -> FunctionCall:
    """nullIf - return NULL if equal."""
    return FunctionCall("nullIf", x, y)


def if_null(x: Any, default: Any) -> FunctionCall:
    """ifNull - return default if NULL."""
    return FunctionCall("ifNull", x, default)


def coalesce(*args: Any) -> FunctionCall:
    """coalesce - first non-NULL value."""
    return FunctionCall("coalesce", *args)


def is_null(x: Any) -> FunctionCall:
    """isNull - check if NULL."""
    return FunctionCall("isNull", x)


def is_not_null(x: Any) -> FunctionCall:
    """isNotNull - check if not NULL."""
    return FunctionCall("isNotNull", x)


def assume_not_null(x: Any) -> FunctionCall:
    """assumeNotNull - treat as non-NULL."""
    return FunctionCall("assumeNotNull", x)


def to_nullable(x: Any) -> FunctionCall:
    """toNullable - convert to Nullable."""
    return FunctionCall("toNullable", x)


# Math functions
def abs(x: Any) -> FunctionCall:
    """abs - absolute value."""
    return FunctionCall("abs", x)


def ceil(x: Any) -> FunctionCall:
    """ceil - round up."""
    return FunctionCall("ceil", x)


def floor(x: Any) -> FunctionCall:
    """floor - round down."""
    return FunctionCall("floor", x)


def round(x: Any, n: Any = None) -> FunctionCall:
    """round - round to nearest."""
    if n is not None:
        return FunctionCall("round", x, n)
    return FunctionCall("round", x)


def sqrt(x: Any) -> FunctionCall:
    """sqrt - square root."""
    return FunctionCall("sqrt", x)


def cbrt(x: Any) -> FunctionCall:
    """cbrt - cube root."""
    return FunctionCall("cbrt", x)


def power(base: Any, exp: Any) -> FunctionCall:
    """power - exponentiation."""
    return FunctionCall("power", base, exp)


def exp(x: Any) -> FunctionCall:
    """exp - e^x."""
    return FunctionCall("exp", x)


def log(x: Any) -> FunctionCall:
    """log - natural logarithm."""
    return FunctionCall("log", x)


def log2(x: Any) -> FunctionCall:
    """log2 - base-2 logarithm."""
    return FunctionCall("log2", x)


def log10(x: Any) -> FunctionCall:
    """log10 - base-10 logarithm."""
    return FunctionCall("log10", x)


def sin(x: Any) -> FunctionCall:
    """sin - sine."""
    return FunctionCall("sin", x)


def cos(x: Any) -> FunctionCall:
    """cos - cosine."""
    return FunctionCall("cos", x)


def tan(x: Any) -> FunctionCall:
    """tan - tangent."""
    return FunctionCall("tan", x)


def asin(x: Any) -> FunctionCall:
    """asin - arcsine."""
    return FunctionCall("asin", x)


def acos(x: Any) -> FunctionCall:
    """acos - arccosine."""
    return FunctionCall("acos", x)


def atan(x: Any) -> FunctionCall:
    """atan - arctangent."""
    return FunctionCall("atan", x)


def greatest(*args: Any) -> FunctionCall:
    """greatest - maximum of arguments."""
    return FunctionCall("greatest", *args)


def least(*args: Any) -> FunctionCall:
    """least - minimum of arguments."""
    return FunctionCall("least", *args)


# Hash functions
def city_hash64(*args: Any) -> FunctionCall:
    """cityHash64 - CityHash."""
    return FunctionCall("cityHash64", *args)


def sip_hash64(*args: Any) -> FunctionCall:
    """sipHash64 - SipHash."""
    return FunctionCall("sipHash64", *args)


def md5(s: Any) -> FunctionCall:
    """MD5 - MD5 hash."""
    return FunctionCall("MD5", s)


def sha1(s: Any) -> FunctionCall:
    """SHA1 - SHA1 hash."""
    return FunctionCall("SHA1", s)


def sha256(s: Any) -> FunctionCall:
    """SHA256 - SHA256 hash."""
    return FunctionCall("SHA256", s)


def xxhash32(s: Any) -> FunctionCall:
    """xxHash32 - xxHash32."""
    return FunctionCall("xxHash32", s)


def xxhash64(s: Any) -> FunctionCall:
    """xxHash64 - xxHash64."""
    return FunctionCall("xxHash64", s)


# UUID functions
def generate_uuid_v4() -> FunctionCall:
    """generateUUIDv4 - generate random UUID."""
    return FunctionCall("generateUUIDv4")


def uuid_string_to_num(s: Any) -> FunctionCall:
    """UUIDStringToNum - convert UUID string to bytes."""
    return FunctionCall("UUIDStringToNum", s)


def uuid_num_to_string(n: Any) -> FunctionCall:
    """UUIDNumToString - convert bytes to UUID string."""
    return FunctionCall("UUIDNumToString", n)


# JSON functions
def json_extract(json: Any, *path: Any) -> FunctionCall:
    """JSONExtract - extract from JSON."""
    return FunctionCall("JSONExtract", json, *path)


def json_extract_string(json: Any, *path: Any) -> FunctionCall:
    """JSONExtractString - extract string from JSON."""
    return FunctionCall("JSONExtractString", json, *path)


def json_extract_int(json: Any, *path: Any) -> FunctionCall:
    """JSONExtractInt - extract int from JSON."""
    return FunctionCall("JSONExtractInt", json, *path)


def json_extract_float(json: Any, *path: Any) -> FunctionCall:
    """JSONExtractFloat - extract float from JSON."""
    return FunctionCall("JSONExtractFloat", json, *path)


def json_extract_bool(json: Any, *path: Any) -> FunctionCall:
    """JSONExtractBool - extract bool from JSON."""
    return FunctionCall("JSONExtractBool", json, *path)


def json_extract_array_raw(json: Any, *path: Any) -> FunctionCall:
    """JSONExtractArrayRaw - extract array from JSON."""
    return FunctionCall("JSONExtractArrayRaw", json, *path)


def json_extract_keys_and_values(json: Any, *path: Any) -> FunctionCall:
    """JSONExtractKeysAndValues - extract keys and values."""
    return FunctionCall("JSONExtractKeysAndValues", json, *path)


# IP functions
def ipv4_string_to_num(s: Any) -> FunctionCall:
    """IPv4StringToNum - parse IPv4."""
    return FunctionCall("IPv4StringToNum", s)


def ipv4_num_to_string(n: Any) -> FunctionCall:
    """IPv4NumToString - format IPv4."""
    return FunctionCall("IPv4NumToString", n)


def ipv6_string_to_num(s: Any) -> FunctionCall:
    """IPv6StringToNum - parse IPv6."""
    return FunctionCall("IPv6StringToNum", s)


def ipv6_num_to_string(n: Any) -> FunctionCall:
    """IPv6NumToString - format IPv6."""
    return FunctionCall("IPv6NumToString", n)


def ipv4_cidr_to_range(cidr: Any) -> FunctionCall:
    """IPv4CIDRToRange - CIDR to range."""
    return FunctionCall("IPv4CIDRToRange", cidr)


def ipv6_cidr_to_range(cidr: Any) -> FunctionCall:
    """IPv6CIDRToRange - CIDR to range."""
    return FunctionCall("IPv6CIDRToRange", cidr)


# Tuple functions
def tuple(*args: Any) -> FunctionCall:
    """tuple - create tuple."""
    return FunctionCall("tuple", *args)


def tuple_element(t: Any, n: Any) -> FunctionCall:
    """tupleElement - get tuple element."""
    return FunctionCall("tupleElement", t, n)


# Map functions
def map(*args: Any) -> FunctionCall:
    """map - create map."""
    return FunctionCall("map", *args)


def map_keys(m: Any) -> FunctionCall:
    """mapKeys - get map keys."""
    return FunctionCall("mapKeys", m)


def map_values(m: Any) -> FunctionCall:
    """mapValues - get map values."""
    return FunctionCall("mapValues", m)


def map_contains(m: Any, key: Any) -> FunctionCall:
    """mapContains - check if key exists."""
    return FunctionCall("mapContains", m, key)


# Window functions (ClickHouse-specific)
def row_number() -> FunctionCall:
    """row_number - row number in window."""
    return FunctionCall("row_number")


def rank() -> FunctionCall:
    """rank - rank in window."""
    return FunctionCall("rank")


def dense_rank() -> FunctionCall:
    """dense_rank - dense rank in window."""
    return FunctionCall("dense_rank")


def lag(expr: Any, offset: Any = 1, default: Any = None) -> FunctionCall:
    """lag - value from previous row."""
    if default is not None:
        return FunctionCall("lag", expr, offset, default)
    return FunctionCall("lag", expr, offset)


def lead(expr: Any, offset: Any = 1, default: Any = None) -> FunctionCall:
    """lead - value from next row."""
    if default is not None:
        return FunctionCall("lead", expr, offset, default)
    return FunctionCall("lead", expr, offset)


def ntile(n: Any) -> FunctionCall:
    """ntile - bucket number."""
    return FunctionCall("ntile", n)


# ClickHouse-specific functions
def running_difference(x: Any) -> FunctionCall:
    """runningDifference - difference from previous row."""
    return FunctionCall("runningDifference", x)


def running_accumulate(x: Any) -> FunctionCall:
    """runningAccumulate - accumulate values."""
    return FunctionCall("runningAccumulate", x)


def neighbor(column: Any, offset: Any, default: Any = None) -> FunctionCall:
    """neighbor - value from relative row."""
    if default is not None:
        return FunctionCall("neighbor", column, offset, default)
    return FunctionCall("neighbor", column, offset)


def dictGet(dict_name: Any, attr_name: Any, id: Any) -> FunctionCall:
    """dictGet - get value from dictionary."""
    return FunctionCall("dictGet", dict_name, attr_name, id)


def dictHas(dict_name: Any, id: Any) -> FunctionCall:
    """dictHas - check if key exists in dictionary."""
    return FunctionCall("dictHas", dict_name, id)


# Misc functions
def random() -> FunctionCall:
    """rand - random number."""
    return FunctionCall("rand")


def rand64() -> FunctionCall:
    """rand64 - random 64-bit number."""
    return FunctionCall("rand64")


def version() -> FunctionCall:
    """version - ClickHouse version."""
    return FunctionCall("version")


def hostname() -> FunctionCall:
    """hostName - server hostname."""
    return FunctionCall("hostName")


def uptime() -> FunctionCall:
    """uptime - server uptime."""
    return FunctionCall("uptime")


def current_database() -> FunctionCall:
    """currentDatabase - current database name."""
    return FunctionCall("currentDatabase")


def current_user() -> FunctionCall:
    """currentUser - current user name."""
    return FunctionCall("currentUser")


# H3 functions - Validation & Properties
def h3_is_valid(h3index: Any) -> FunctionCall:
    """h3IsValid - validates if a number is a valid H3 index."""
    return FunctionCall("h3IsValid", h3index)


def h3_get_resolution(h3index: Any) -> FunctionCall:
    """h3GetResolution - returns the resolution of an H3 index."""
    return FunctionCall("h3GetResolution", h3index)


def h3_get_base_cell(index: Any) -> FunctionCall:
    """h3GetBaseCell - returns the base cell number of an H3 index."""
    return FunctionCall("h3GetBaseCell", index)


def h3_is_res_class_iii(index: Any) -> FunctionCall:
    """h3IsResClassIII - checks if an H3 index has Class III resolution."""
    return FunctionCall("h3IsResClassIII", index)


def h3_is_pentagon(index: Any) -> FunctionCall:
    """h3IsPentagon - checks if an H3 index is a pentagon."""
    return FunctionCall("h3IsPentagon", index)


def h3_get_faces(index: Any) -> FunctionCall:
    """h3GetFaces - returns all icosahedron faces intersected by an H3 index."""
    return FunctionCall("h3GetFaces", index)


# H3 functions - Coordinate Conversion
def geo_to_h3(lat: Any, lon: Any, resolution: Any) -> FunctionCall:
    """geoToH3 - converts geographic coordinates to H3 index."""
    return FunctionCall("geoToH3", lat, lon, resolution)


def h3_to_geo(h3index: Any) -> FunctionCall:
    """h3ToGeo - returns the centroid coordinates of an H3 index."""
    return FunctionCall("h3ToGeo", h3index)


def h3_to_geo_boundary(h3index: Any) -> FunctionCall:
    """h3ToGeoBoundary - returns the boundary coordinates of an H3 cell."""
    return FunctionCall("h3ToGeoBoundary", h3index)


# H3 functions - String Conversion
def h3_to_string(index: Any) -> FunctionCall:
    """h3ToString - converts an H3 index to its string representation."""
    return FunctionCall("h3ToString", index)


def string_to_h3(index_str: Any) -> FunctionCall:
    """stringToH3 - converts a string to an H3 index."""
    return FunctionCall("stringToH3", index_str)


# H3 functions - Hierarchy
def h3_to_parent(index: Any, resolution: Any) -> FunctionCall:
    """h3ToParent - returns the parent H3 index at a coarser resolution."""
    return FunctionCall("h3ToParent", index, resolution)


def h3_to_children(index: Any, resolution: Any) -> FunctionCall:
    """h3ToChildren - returns the children H3 indexes at a finer resolution."""
    return FunctionCall("h3ToChildren", index, resolution)


def h3_to_center_child(index: Any, resolution: Any) -> FunctionCall:
    """h3ToCenterChild - returns the center child at a finer resolution."""
    return FunctionCall("h3ToCenterChild", index, resolution)


# H3 functions - Measurements
def h3_edge_angle(resolution: Any) -> FunctionCall:
    """h3EdgeAngle - returns the average edge length in degrees."""
    return FunctionCall("h3EdgeAngle", resolution)


def h3_edge_length_m(resolution: Any) -> FunctionCall:
    """h3EdgeLengthM - returns the average edge length in meters."""
    return FunctionCall("h3EdgeLengthM", resolution)


def h3_edge_length_km(resolution: Any) -> FunctionCall:
    """h3EdgeLengthKm - returns the average edge length in kilometers."""
    return FunctionCall("h3EdgeLengthKm", resolution)


def h3_hex_area_m2(resolution: Any) -> FunctionCall:
    """h3HexAreaM2 - returns the average hexagon area in square meters."""
    return FunctionCall("h3HexAreaM2", resolution)


def h3_hex_area_km2(resolution: Any) -> FunctionCall:
    """h3HexAreaKm2 - returns the average hexagon area in square kilometers."""
    return FunctionCall("h3HexAreaKm2", resolution)


def h3_cell_area_m2(index: Any) -> FunctionCall:
    """h3CellAreaM2 - returns the exact area of a cell in square meters."""
    return FunctionCall("h3CellAreaM2", index)


def h3_cell_area_rads2(index: Any) -> FunctionCall:
    """h3CellAreaRads2 - returns the exact area of a cell in square radians."""
    return FunctionCall("h3CellAreaRads2", index)


def h3_exact_edge_length_m(index: Any) -> FunctionCall:
    """h3ExactEdgeLengthM - returns the exact edge length in meters."""
    return FunctionCall("h3ExactEdgeLengthM", index)


def h3_exact_edge_length_km(index: Any) -> FunctionCall:
    """h3ExactEdgeLengthKm - returns the exact edge length in kilometers."""
    return FunctionCall("h3ExactEdgeLengthKm", index)


def h3_exact_edge_length_rads(index: Any) -> FunctionCall:
    """h3ExactEdgeLengthRads - returns the exact edge length in radians."""
    return FunctionCall("h3ExactEdgeLengthRads", index)


def h3_num_hexagons(resolution: Any) -> FunctionCall:
    """h3NumHexagons - returns the total number of hexagons at a resolution."""
    return FunctionCall("h3NumHexagons", resolution)


# H3 functions - Distance & Neighbors
def h3_k_ring(h3index: Any, k: Any) -> FunctionCall:
    """h3kRing - returns all H3 indexes within k distance."""
    return FunctionCall("h3kRing", h3index, k)


def h3_hex_ring(index: Any, k: Any) -> FunctionCall:
    """h3HexRing - returns the hollow ring of H3 indexes at distance k."""
    return FunctionCall("h3HexRing", index, k)


def h3_indexes_are_neighbors(index1: Any, index2: Any) -> FunctionCall:
    """h3IndexesAreNeighbors - checks if two H3 indexes are neighbors."""
    return FunctionCall("h3IndexesAreNeighbors", index1, index2)


def h3_distance(start: Any, end: Any) -> FunctionCall:
    """h3Distance - returns the grid distance between two H3 indexes."""
    return FunctionCall("h3Distance", start, end)


def h3_line(start: Any, end: Any) -> FunctionCall:
    """h3Line - returns the line of H3 indexes between two indexes."""
    return FunctionCall("h3Line", start, end)


def h3_point_dist_m(lat1: Any, lon1: Any, lat2: Any, lon2: Any) -> FunctionCall:
    """h3PointDistM - returns distance between two points in meters."""
    return FunctionCall("h3PointDistM", lat1, lon1, lat2, lon2)


def h3_point_dist_km(lat1: Any, lon1: Any, lat2: Any, lon2: Any) -> FunctionCall:
    """h3PointDistKm - returns distance between two points in kilometers."""
    return FunctionCall("h3PointDistKm", lat1, lon1, lat2, lon2)


def h3_point_dist_rads(lat1: Any, lon1: Any, lat2: Any, lon2: Any) -> FunctionCall:
    """h3PointDistRads - returns distance between two points in radians."""
    return FunctionCall("h3PointDistRads", lat1, lon1, lat2, lon2)


# H3 functions - Polygon Operations
def h3_polygon_to_cells(geometry: Any, resolution: Any) -> FunctionCall:
    """h3PolygonToCells - returns H3 indexes that cover a polygon."""
    return FunctionCall("h3PolygonToCells", geometry, resolution)


# H3 functions - Global Functions
def h3_get_res0_indexes() -> FunctionCall:
    """h3GetRes0Indexes - returns all resolution 0 H3 indexes."""
    return FunctionCall("h3GetRes0Indexes")


def h3_get_pentagon_indexes(resolution: Any) -> FunctionCall:
    """h3GetPentagonIndexes - returns all pentagon indexes at a resolution."""
    return FunctionCall("h3GetPentagonIndexes", resolution)


# H3 functions - Unidirectional Edges
def h3_get_unidirectional_edge(origin: Any, destination: Any) -> FunctionCall:
    """h3GetUnidirectionalEdge - returns the unidirectional edge between two cells."""
    return FunctionCall("h3GetUnidirectionalEdge", origin, destination)


def h3_unidirectional_edge_is_valid(index: Any) -> FunctionCall:
    """h3UnidirectionalEdgeIsValid - checks if an edge index is valid."""
    return FunctionCall("h3UnidirectionalEdgeIsValid", index)


def h3_get_origin_index_from_unidirectional_edge(edge: Any) -> FunctionCall:
    """h3GetOriginIndexFromUnidirectionalEdge - returns the origin cell of an edge."""
    return FunctionCall("h3GetOriginIndexFromUnidirectionalEdge", edge)


def h3_get_destination_index_from_unidirectional_edge(edge: Any) -> FunctionCall:
    """h3GetDestinationIndexFromUnidirectionalEdge - returns the destination cell of an edge."""
    return FunctionCall("h3GetDestinationIndexFromUnidirectionalEdge", edge)


def h3_get_indexes_from_unidirectional_edge(edge: Any) -> FunctionCall:
    """h3GetIndexesFromUnidirectionalEdge - returns origin and destination cells."""
    return FunctionCall("h3GetIndexesFromUnidirectionalEdge", edge)


def h3_get_unidirectional_edges_from_hexagon(index: Any) -> FunctionCall:
    """h3GetUnidirectionalEdgesFromHexagon - returns all edges from a cell."""
    return FunctionCall("h3GetUnidirectionalEdgesFromHexagon", index)


def h3_get_unidirectional_edge_boundary(index: Any) -> FunctionCall:
    """h3GetUnidirectionalEdgeBoundary - returns the boundary of an edge."""
    return FunctionCall("h3GetUnidirectionalEdgeBoundary", index)

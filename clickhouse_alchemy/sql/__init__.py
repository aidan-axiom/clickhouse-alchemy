"""SQL expression language for ClickHouse."""

from .expression import (
    # Base classes
    ClauseElement,
    ColumnElement,
    ColumnClause,
    TableClause,
    # Expressions
    BinaryExpression,
    UnaryExpression,
    InExpression,
    BetweenExpression,
    OrderByElement,
    Label,
    Literal,
    FunctionCall,
    Cast,
    Case,
    Tuple_,
    Subquery,
    Exists,
    All,
    Any,
    ArrayAccess,
    # Factory functions
    literal,
    column,
    table,
    cast,
    case,
    tuple_,
    exists,
    all_,
    any_,
    # Boolean combinators
    and_,
    or_,
    not_,
    # Ordering
    asc,
    desc,
    nulls_first,
    nulls_last,
)

from .selectable import (
    Select,
    Join,
    CTE,
    Alias,
    Values,
    FromClause,
    # Factory functions
    select,
    cte,
    alias,
    values,
    union,
    union_all,
    intersect,
    except_,
)

from .dml import (
    Insert,
    AlterTable,
    Optimize,
    Truncate,
    # Factory functions
    insert,
    alter_table,
    optimize,
    truncate,
)

from .ddl import (
    CreateTable,
    DropTable,
    CreateDatabase,
    DropDatabase,
    CreateView,
    DropView,
    # Factory functions
    create_table,
    drop_table,
    create_database,
    drop_database,
    create_view,
    create_materialized_view,
    drop_view,
)

from . import functions as func

__all__ = [
    # Base classes
    "ClauseElement",
    "ColumnElement",
    "ColumnClause",
    "TableClause",
    # Expressions
    "BinaryExpression",
    "UnaryExpression",
    "InExpression",
    "BetweenExpression",
    "OrderByElement",
    "Label",
    "Literal",
    "FunctionCall",
    "Cast",
    "Case",
    "Tuple_",
    "Subquery",
    "Exists",
    "All",
    "Any",
    "ArrayAccess",
    # Factory functions
    "literal",
    "column",
    "table",
    "cast",
    "case",
    "tuple_",
    "exists",
    "all_",
    "any_",
    # Boolean combinators
    "and_",
    "or_",
    "not_",
    # Ordering
    "asc",
    "desc",
    "nulls_first",
    "nulls_last",
    # Selectable
    "Select",
    "Join",
    "CTE",
    "Alias",
    "Values",
    "FromClause",
    "select",
    "cte",
    "alias",
    "values",
    "union",
    "union_all",
    "intersect",
    "except_",
    # DML
    "Insert",
    "AlterTable",
    "Optimize",
    "Truncate",
    "insert",
    "alter_table",
    "optimize",
    "truncate",
    # DDL
    "CreateTable",
    "DropTable",
    "CreateDatabase",
    "DropDatabase",
    "CreateView",
    "DropView",
    "create_table",
    "drop_table",
    "create_database",
    "drop_database",
    "create_view",
    "create_materialized_view",
    "drop_view",
    # Functions module
    "func",
]

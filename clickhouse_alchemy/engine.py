"""Engine and Connection classes for executing statements."""

from __future__ import annotations
from typing import Any, Dict, Iterator, List, Optional, Sequence, Tuple, Union
from urllib.parse import urlparse, parse_qs
import re

import clickhouse_connect
from clickhouse_connect.driver import Client


class URL:
    """Database URL parser."""

    def __init__(
        self,
        drivername: str = "clickhouse",
        username: Optional[str] = None,
        password: Optional[str] = None,
        host: Optional[str] = None,
        port: Optional[int] = None,
        database: Optional[str] = None,
        query: Optional[Dict[str, Any]] = None,
    ):
        self.drivername = drivername
        self.username = username
        self.password = password
        self.host = host
        self.port = port
        self.database = database
        self.query = query or {}

    @classmethod
    def create(
        cls,
        drivername: str = "clickhouse",
        username: Optional[str] = None,
        password: Optional[str] = None,
        host: Optional[str] = None,
        port: Optional[int] = None,
        database: Optional[str] = None,
        query: Optional[Dict[str, Any]] = None,
    ) -> URL:
        """Create a URL from components."""
        return cls(
            drivername=drivername,
            username=username,
            password=password,
            host=host,
            port=port,
            database=database,
            query=query,
        )

    @classmethod
    def parse(cls, url: str) -> URL:
        """Parse a URL string."""
        # Handle clickhouse:// or clickhouse+http:// etc.
        match = re.match(r'^(\w+)(?:\+(\w+))?://', url)
        if match:
            drivername = match.group(1)
            if match.group(2):
                drivername = f"{drivername}+{match.group(2)}"
            # Replace with standard scheme for urlparse
            url = "scheme://" + url[match.end():]
        else:
            drivername = "clickhouse"

        parsed = urlparse(url)

        # Parse query string
        query: Dict[str, Any] = {}
        if parsed.query:
            for key, values in parse_qs(parsed.query).items():
                query[key] = values[0] if len(values) == 1 else values

        return cls(
            drivername=drivername,
            username=parsed.username,
            password=parsed.password,
            host=parsed.hostname,
            port=parsed.port,
            database=parsed.path.lstrip('/') if parsed.path else None,
            query=query,
        )

    @property
    def is_secure(self) -> bool:
        """Check if connection should use HTTPS/TLS."""
        return (
            '+https' in self.drivername or
            '+secure' in self.drivername or
            self.query.get('secure') in ('true', '1', True)
        )

    def __repr__(self) -> str:
        return f"URL({self.drivername}://{self.host}:{self.port}/{self.database})"

    def __str__(self) -> str:
        result = f"{self.drivername}://"
        if self.username:
            result += self.username
            if self.password:
                result += f":***"  # Hide password
            result += "@"
        if self.host:
            result += self.host
        if self.port:
            result += f":{self.port}"
        if self.database:
            result += f"/{self.database}"
        return result


class Result:
    """Query result set."""

    def __init__(
        self,
        rows: List[Tuple[Any, ...]],
        columns: List[str],
        rowcount: int = -1,
    ):
        self._rows = rows
        self._columns = columns
        self._rowcount = rowcount
        self._cursor = 0

    @classmethod
    def from_query_result(cls, query_result: Any) -> Result:
        """Create Result from clickhouse-connect QueryResult."""
        columns = list(query_result.column_names) if query_result.column_names else []
        rows = [tuple(row) for row in query_result.result_rows] if query_result.result_rows else []
        return cls(rows=rows, columns=columns, rowcount=len(rows))

    @property
    def columns(self) -> List[str]:
        """Return column names."""
        return self._columns

    @property
    def rowcount(self) -> int:
        """Return number of rows affected/returned."""
        return self._rowcount if self._rowcount >= 0 else len(self._rows)

    def fetchone(self) -> Optional[Tuple[Any, ...]]:
        """Fetch the next row."""
        if self._cursor >= len(self._rows):
            return None
        row = self._rows[self._cursor]
        self._cursor += 1
        return row

    def fetchmany(self, size: int = 1) -> List[Tuple[Any, ...]]:
        """Fetch multiple rows."""
        rows = self._rows[self._cursor:self._cursor + size]
        self._cursor += len(rows)
        return rows

    def fetchall(self) -> List[Tuple[Any, ...]]:
        """Fetch all remaining rows."""
        rows = self._rows[self._cursor:]
        self._cursor = len(self._rows)
        return rows

    def first(self) -> Optional[Tuple[Any, ...]]:
        """Fetch the first row and close."""
        if self._rows:
            return self._rows[0]
        return None

    def scalar(self) -> Optional[Any]:
        """Fetch the first column of the first row."""
        row = self.first()
        if row and len(row) > 0:
            return row[0]
        return None

    def scalars(self) -> List[Any]:
        """Fetch the first column of all rows."""
        return [row[0] for row in self._rows if row]

    def mappings(self) -> List[Dict[str, Any]]:
        """Return rows as dictionaries."""
        return [dict(zip(self._columns, row)) for row in self._rows]

    def keys(self) -> List[str]:
        """Return column names."""
        return self._columns

    def __iter__(self) -> Iterator[Tuple[Any, ...]]:
        return iter(self._rows)

    def __len__(self) -> int:
        return len(self._rows)

    def close(self) -> None:
        """Close the result (no-op for in-memory results)."""
        pass


class Connection:
    """Database connection wrapping a clickhouse-connect client."""

    def __init__(self, engine: Engine, client: Client):
        self._engine = engine
        self._client = client
        self._closed = False

    @property
    def closed(self) -> bool:
        return self._closed

    def execute(
        self,
        statement: Any,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> Result:
        """Execute a statement and return results.

        Args:
            statement: A compiled statement or SQL string
            parameters: Optional dict of parameters for parameterized queries

        Returns:
            Result object containing the query results
        """
        if self._closed:
            raise RuntimeError("Connection is closed")

        # Compile statement if needed
        if hasattr(statement, 'compile'):
            sql = statement.compile()
        else:
            sql = str(statement)

        if self._engine.echo:
            print(f"[SQL] {sql}")
            if parameters:
                print(f"[PARAMS] {parameters}")

        # Determine if this is a query (returns data) or command (DDL/DML)
        sql_upper = sql.strip().upper()
        is_query = sql_upper.startswith(('SELECT', 'SHOW', 'DESCRIBE', 'EXPLAIN', 'WITH'))

        if is_query:
            query_result = self._client.query(sql, parameters=parameters)
            return Result.from_query_result(query_result)
        else:
            # For DDL/DML, use command() which doesn't expect results
            self._client.command(sql, parameters=parameters)
            return Result(rows=[], columns=[], rowcount=-1)

    def execute_many(
        self,
        statement: Any,
        parameters: Sequence[Dict[str, Any]],
    ) -> Result:
        """Execute a statement multiple times with different parameters."""
        if self._closed:
            raise RuntimeError("Connection is closed")

        results = []
        for params in parameters:
            result = self.execute(statement, params)
            results.append(result)

        # Return the last result
        return results[-1] if results else Result(rows=[], columns=[], rowcount=0)

    def insert(
        self,
        table: Any,
        data: List[Dict[str, Any]],
        column_names: Optional[List[str]] = None,
    ) -> Result:
        """Insert data efficiently using clickhouse-connect's insert method.

        Args:
            table: Table name or Table object
            data: List of dicts with column->value mappings
            column_names: Optional list of column names (inferred from data if not provided)

        Returns:
            Result object
        """
        if self._closed:
            raise RuntimeError("Connection is closed")

        table_name = table.name if hasattr(table, 'name') else str(table)

        if not data:
            return Result(rows=[], columns=[], rowcount=0)

        # Get column names from first row if not provided
        if column_names is None:
            column_names = list(data[0].keys())

        # Convert list of dicts to list of lists
        rows = [[row.get(col) for col in column_names] for row in data]

        if self._engine.echo:
            print(f"[INSERT] {table_name} ({len(rows)} rows)")

        self._client.insert(
            table=table_name,
            data=rows,
            column_names=column_names,
        )

        return Result(rows=[], columns=[], rowcount=len(rows))

    def begin(self) -> Transaction:
        """Begin a transaction (ClickHouse has limited transaction support)."""
        return Transaction(self)

    def commit(self) -> None:
        """Commit the current transaction (no-op for most ClickHouse operations)."""
        pass

    def rollback(self) -> None:
        """Rollback the current transaction (not supported in ClickHouse)."""
        raise NotImplementedError("ClickHouse does not support rollback")

    def close(self) -> None:
        """Close the connection."""
        if not self._closed:
            self._client.close()
            self._closed = True

    def __enter__(self) -> Connection:
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()


class Transaction:
    """Transaction context manager (limited support in ClickHouse)."""

    def __init__(self, connection: Connection):
        self._connection = connection

    def commit(self) -> None:
        """Commit the transaction."""
        self._connection.commit()

    def rollback(self) -> None:
        """Rollback the transaction."""
        self._connection.rollback()

    def __enter__(self) -> Transaction:
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if exc_type is not None:
            # Exception occurred, but ClickHouse doesn't support rollback
            pass
        else:
            self.commit()


class Engine:
    """Database engine - holds configuration and creates connections."""

    def __init__(
        self,
        url: Union[str, URL],
        echo: bool = False,
        **kwargs: Any,
    ):
        if isinstance(url, str):
            url = URL.parse(url)
        self._url = url
        self._echo = echo
        self._kwargs = kwargs

    @property
    def url(self) -> URL:
        return self._url

    @property
    def echo(self) -> bool:
        return self._echo

    @echo.setter
    def echo(self, value: bool) -> None:
        self._echo = value

    @property
    def name(self) -> str:
        """Return the dialect name."""
        return self._url.drivername.split('+')[0]

    def _create_client(self) -> Client:
        """Create a clickhouse-connect client."""
        # Build connection parameters
        connect_kwargs: Dict[str, Any] = {
            'host': self._url.host or 'localhost',
            'port': self._url.port or 8123,
            'database': self._url.database or 'default',
        }

        if self._url.username:
            connect_kwargs['username'] = self._url.username
        if self._url.password:
            connect_kwargs['password'] = self._url.password

        # Handle secure connections
        if self._url.is_secure:
            connect_kwargs['secure'] = True

        # Merge any additional query parameters
        for key, value in self._url.query.items():
            if key not in ('secure',):  # Already handled
                connect_kwargs[key] = value

        # Merge kwargs passed to Engine
        connect_kwargs.update(self._kwargs)

        return clickhouse_connect.get_client(**connect_kwargs)

    def connect(self) -> Connection:
        """Create a new connection."""
        client = self._create_client()
        return Connection(self, client)

    def begin(self) -> Connection:
        """Create a connection with an implicit transaction."""
        return self.connect()

    def execute(
        self,
        statement: Any,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> Result:
        """Execute a statement using a new connection."""
        with self.connect() as conn:
            return conn.execute(statement, parameters)

    def dispose(self) -> None:
        """Dispose of the connection pool (no-op, connections are not pooled)."""
        pass

    def __repr__(self) -> str:
        return f"Engine({self._url})"


def create_engine(
    url: Union[str, URL],
    echo: bool = False,
    **kwargs: Any,
) -> Engine:
    """Create a new database engine.

    Args:
        url: Database URL. Formats supported:
            - clickhouse://user:pass@host:port/database
            - clickhouse+http://host:8123/database
            - clickhouse+https://host:8443/database (secure)
        echo: If True, log all SQL statements
        **kwargs: Additional arguments passed to clickhouse-connect

    Returns:
        Engine instance

    Examples:
        # Basic connection
        engine = create_engine("clickhouse://localhost/default")

        # With authentication
        engine = create_engine("clickhouse://user:password@localhost:8123/mydb")

        # Secure connection
        engine = create_engine("clickhouse+https://host:8443/mydb")

        # With additional options
        engine = create_engine(
            "clickhouse://localhost/default",
            echo=True,
            send_receive_timeout=30,
        )
    """
    return Engine(url=url, echo=echo, **kwargs)

"""Tests for Engine, Connection, and URL classes."""

import pytest
from unittest.mock import Mock, patch, MagicMock

from clickhouse_alchemy import create_engine, Engine, Connection, Result
from clickhouse_alchemy.engine import URL


class TestURL:
    """Tests for URL parsing."""

    def test_parse_basic(self):
        url = URL.parse('clickhouse://localhost/default')
        assert url.host == 'localhost'
        assert url.database == 'default'
        assert url.drivername == 'clickhouse'

    def test_parse_with_port(self):
        url = URL.parse('clickhouse://localhost:8123/mydb')
        assert url.host == 'localhost'
        assert url.port == 8123
        assert url.database == 'mydb'

    def test_parse_with_credentials(self):
        url = URL.parse('clickhouse://user:password@localhost/default')
        assert url.username == 'user'
        assert url.password == 'password'
        assert url.host == 'localhost'

    def test_parse_with_http_scheme(self):
        url = URL.parse('clickhouse+http://localhost:8123/default')
        assert url.drivername == 'clickhouse+http'
        assert url.port == 8123

    def test_parse_with_https_scheme(self):
        url = URL.parse('clickhouse+https://localhost:8443/default')
        assert url.drivername == 'clickhouse+https'
        assert url.is_secure is True

    def test_parse_with_query_params(self):
        url = URL.parse('clickhouse://localhost/default?secure=true&timeout=30')
        assert url.query.get('secure') == 'true'
        assert url.query.get('timeout') == '30'

    def test_is_secure_from_query(self):
        url = URL.parse('clickhouse://localhost/default?secure=true')
        assert url.is_secure is True

    def test_is_secure_from_scheme(self):
        url = URL.parse('clickhouse+https://localhost/default')
        assert url.is_secure is True

    def test_create(self):
        url = URL.create(
            host='localhost',
            port=8123,
            database='mydb',
            username='user',
            password='pass'
        )
        assert url.host == 'localhost'
        assert url.port == 8123
        assert url.database == 'mydb'
        assert url.username == 'user'

    def test_str_hides_password(self):
        url = URL.parse('clickhouse://user:secret@localhost/default')
        url_str = str(url)
        assert 'secret' not in url_str
        assert '***' in url_str

    def test_repr(self):
        url = URL.parse('clickhouse://localhost:8123/default')
        assert 'localhost' in repr(url)
        assert '8123' in repr(url)


class TestResult:
    """Tests for Result class."""

    def test_empty_result(self):
        result = Result(rows=[], columns=[])
        assert len(result) == 0
        assert result.rowcount == 0
        assert result.fetchone() is None
        assert result.fetchall() == []

    def test_result_with_data(self):
        rows = [(1, 'Alice'), (2, 'Bob'), (3, 'Charlie')]
        columns = ['id', 'name']
        result = Result(rows=rows, columns=columns)

        assert len(result) == 3
        assert result.columns == ['id', 'name']

    def test_fetchone(self):
        rows = [(1, 'Alice'), (2, 'Bob')]
        result = Result(rows=rows, columns=['id', 'name'])

        row1 = result.fetchone()
        assert row1 == (1, 'Alice')

        row2 = result.fetchone()
        assert row2 == (2, 'Bob')

        row3 = result.fetchone()
        assert row3 is None

    def test_fetchmany(self):
        rows = [(1,), (2,), (3,), (4,), (5,)]
        result = Result(rows=rows, columns=['id'])

        batch = result.fetchmany(2)
        assert len(batch) == 2
        assert batch == [(1,), (2,)]

        batch = result.fetchmany(2)
        assert len(batch) == 2
        assert batch == [(3,), (4,)]

    def test_fetchall(self):
        rows = [(1,), (2,), (3,)]
        result = Result(rows=rows, columns=['id'])

        all_rows = result.fetchall()
        assert len(all_rows) == 3

        # Should be empty after fetchall
        assert result.fetchall() == []

    def test_first(self):
        rows = [(1, 'Alice'), (2, 'Bob')]
        result = Result(rows=rows, columns=['id', 'name'])

        first = result.first()
        assert first == (1, 'Alice')

    def test_scalar(self):
        rows = [(42,)]
        result = Result(rows=rows, columns=['count'])

        value = result.scalar()
        assert value == 42

    def test_scalar_empty(self):
        result = Result(rows=[], columns=['count'])
        assert result.scalar() is None

    def test_scalars(self):
        rows = [(1,), (2,), (3,)]
        result = Result(rows=rows, columns=['id'])

        values = result.scalars()
        assert values == [1, 2, 3]

    def test_mappings(self):
        rows = [(1, 'Alice'), (2, 'Bob')]
        result = Result(rows=rows, columns=['id', 'name'])

        mappings = result.mappings()
        assert len(mappings) == 2
        assert mappings[0] == {'id': 1, 'name': 'Alice'}
        assert mappings[1] == {'id': 2, 'name': 'Bob'}

    def test_keys(self):
        result = Result(rows=[], columns=['id', 'name', 'email'])
        assert result.keys() == ['id', 'name', 'email']

    def test_iterate(self):
        rows = [(1,), (2,), (3,)]
        result = Result(rows=rows, columns=['id'])

        collected = list(result)
        assert collected == [(1,), (2,), (3,)]


class TestEngine:
    """Tests for Engine class."""

    def test_create_engine_string(self):
        engine = create_engine('clickhouse://localhost/default')
        assert engine.url.host == 'localhost'
        assert engine.url.database == 'default'

    def test_create_engine_url(self):
        url = URL.create(host='localhost', database='mydb')
        engine = create_engine(url)
        assert engine.url.host == 'localhost'
        assert engine.url.database == 'mydb'

    def test_engine_echo(self):
        engine = create_engine('clickhouse://localhost/default', echo=True)
        assert engine.echo is True

    def test_engine_echo_setter(self):
        engine = create_engine('clickhouse://localhost/default')
        assert engine.echo is False
        engine.echo = True
        assert engine.echo is True

    def test_engine_name(self):
        engine = create_engine('clickhouse://localhost/default')
        assert engine.name == 'clickhouse'

    def test_engine_name_with_scheme(self):
        engine = create_engine('clickhouse+http://localhost/default')
        assert engine.name == 'clickhouse'

    def test_engine_repr(self):
        engine = create_engine('clickhouse://localhost/default')
        assert 'Engine' in repr(engine)
        assert 'localhost' in repr(engine)


class TestConnection:
    """Tests for Connection class."""

    @patch('clickhouse_alchemy.engine.clickhouse_connect')
    def test_connection_context_manager(self, mock_cc):
        mock_client = MagicMock()
        mock_cc.get_client.return_value = mock_client

        engine = create_engine('clickhouse://localhost/default')

        with engine.connect() as conn:
            assert conn.closed is False

        assert conn.closed is True
        mock_client.close.assert_called_once()

    @patch('clickhouse_alchemy.engine.clickhouse_connect')
    def test_connection_execute_query(self, mock_cc):
        mock_client = MagicMock()
        mock_query_result = MagicMock()
        mock_query_result.column_names = ['id', 'name']
        mock_query_result.result_rows = [(1, 'Alice'), (2, 'Bob')]
        mock_client.query.return_value = mock_query_result
        mock_cc.get_client.return_value = mock_client

        engine = create_engine('clickhouse://localhost/default')

        with engine.connect() as conn:
            result = conn.execute('SELECT id, name FROM users')

            assert len(result) == 2
            assert result.columns == ['id', 'name']
            mock_client.query.assert_called_once()

    @patch('clickhouse_alchemy.engine.clickhouse_connect')
    def test_connection_execute_command(self, mock_cc):
        mock_client = MagicMock()
        mock_cc.get_client.return_value = mock_client

        engine = create_engine('clickhouse://localhost/default')

        with engine.connect() as conn:
            result = conn.execute('CREATE TABLE test (id UInt64) ENGINE = Memory')

            mock_client.command.assert_called_once()

    @patch('clickhouse_alchemy.engine.clickhouse_connect')
    def test_connection_execute_with_statement_object(self, mock_cc):
        mock_client = MagicMock()
        mock_query_result = MagicMock()
        mock_query_result.column_names = ['id']
        mock_query_result.result_rows = [(1,)]
        mock_client.query.return_value = mock_query_result
        mock_cc.get_client.return_value = mock_client

        from clickhouse_alchemy import select, column, table

        engine = create_engine('clickhouse://localhost/default')
        stmt = select(column('id')).select_from(table('users'))

        with engine.connect() as conn:
            result = conn.execute(stmt)

            # Verify the compiled SQL was passed
            call_args = mock_client.query.call_args[0][0]
            assert 'SELECT id FROM users' in call_args

    @patch('clickhouse_alchemy.engine.clickhouse_connect')
    def test_connection_insert(self, mock_cc):
        mock_client = MagicMock()
        mock_cc.get_client.return_value = mock_client

        engine = create_engine('clickhouse://localhost/default')

        with engine.connect() as conn:
            data = [
                {'id': 1, 'name': 'Alice'},
                {'id': 2, 'name': 'Bob'},
            ]
            result = conn.insert('users', data)

            mock_client.insert.assert_called_once()
            call_kwargs = mock_client.insert.call_args[1]
            assert call_kwargs['table'] == 'users'
            assert len(call_kwargs['data']) == 2

    @patch('clickhouse_alchemy.engine.clickhouse_connect')
    def test_connection_closed_raises(self, mock_cc):
        mock_client = MagicMock()
        mock_cc.get_client.return_value = mock_client

        engine = create_engine('clickhouse://localhost/default')
        conn = engine.connect()
        conn.close()

        with pytest.raises(RuntimeError, match="Connection is closed"):
            conn.execute('SELECT 1')

    def test_connection_rollback_not_supported(self):
        with patch('clickhouse_alchemy.engine.clickhouse_connect') as mock_cc:
            mock_cc.get_client.return_value = MagicMock()

            engine = create_engine('clickhouse://localhost/default')
            conn = engine.connect()

            with pytest.raises(NotImplementedError, match="rollback"):
                conn.rollback()


class TestEngineExecute:
    """Tests for Engine.execute shortcut."""

    @patch('clickhouse_alchemy.engine.clickhouse_connect')
    def test_engine_execute(self, mock_cc):
        mock_client = MagicMock()
        mock_query_result = MagicMock()
        mock_query_result.column_names = ['result']
        mock_query_result.result_rows = [(1,)]
        mock_client.query.return_value = mock_query_result
        mock_cc.get_client.return_value = mock_client

        engine = create_engine('clickhouse://localhost/default')
        result = engine.execute('SELECT 1')

        assert result.scalar() == 1
        # Connection should be closed after execute
        mock_client.close.assert_called()


class TestEngineDispose:
    """Tests for Engine.dispose."""

    def test_dispose_no_error(self):
        engine = create_engine('clickhouse://localhost/default')
        # Should not raise
        engine.dispose()

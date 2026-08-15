import os
from unittest.mock import MagicMock, patch
import pytest

# Ensure environment variables are set before app module loads
os.environ["DATABASE_URL"] = "postgres://dummy_user:dummy_pass@localhost:5432/dummy_db"
os.environ["AUTH_SERVICE_URL"] = "http://localhost:8001"

# Create global mocks for database connections
mock_pool = MagicMock()
mock_conn = MagicMock()
mock_cursor = MagicMock()

mock_pool.getconn.return_value = mock_conn
mock_conn.cursor.return_value = mock_cursor

# Patch SimpleConnectionPool during initial module import
with patch("psycopg2.pool.SimpleConnectionPool", return_value=mock_pool):
    import app as flask_app_module


@pytest.fixture
def app():
    """Provides the Flask application instance."""
    flask_app_module.app.config.update({"TESTING": True})
    return flask_app_module.app


@pytest.fixture
def client(app):
    """Provides a Flask test client."""
    return app.test_client()


@pytest.fixture
def mock_db():
    """Provides fresh mock database fixtures for each test."""
    pool_mock = MagicMock()
    conn_mock = MagicMock()
    cursor_mock = MagicMock()

    pool_mock.getconn.return_value = conn_mock
    conn_mock.cursor.return_value = cursor_mock

    flask_app_module.pool = pool_mock
    return {
        "pool": pool_mock,
        "conn": conn_mock,
        "cursor": cursor_mock,
    }

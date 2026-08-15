from unittest.mock import patch
import psycopg2
import requests


# --- Health Check Tests ---

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


# --- Authentication Middleware Tests ---

def test_auth_missing_header(client):
    response = client.get("/flags")
    assert response.status_code == 401
    assert "Authorization header" in response.get_json()["error"]


@patch("requests.get")
def test_auth_invalid_token(mock_requests_get, client):
    mock_requests_get.return_value.status_code = 401
    headers = {"Authorization": "Bearer invalid_token"}
    response = client.get("/flags", headers=headers)
    assert response.status_code == 401
    assert "Chave de API inválida" in response.get_json()["error"]


@patch("requests.get")
def test_auth_timeout(mock_requests_get, client):
    mock_requests_get.side_effect = requests.exceptions.Timeout()
    headers = {"Authorization": "Bearer valid_token"}
    response = client.get("/flags", headers=headers)
    assert response.status_code == 504
    assert "timeout" in response.get_json()["error"]


# --- POST /flags (Create Flag) Tests ---

@patch("requests.get")
def test_create_flag_success(mock_requests_get, client, mock_db):
    mock_requests_get.return_value.status_code = 200
    mock_cursor = mock_db["cursor"]
    mock_cursor.fetchone.return_value = {
        "name": "new-feature-flag",
        "description": "Enables new feature",
        "is_enabled": True,
    }

    payload = {
        "name": "new-feature-flag",
        "description": "Enables new feature",
        "is_enabled": True,
    }
    headers = {"Authorization": "Bearer valid_token"}

    response = client.post("/flags", json=payload, headers=headers)
    assert response.status_code == 201
    assert response.get_json()["name"] == "new-feature-flag"


@patch("requests.get")
def test_create_flag_missing_name(mock_requests_get, client):
    mock_requests_get.return_value.status_code = 200
    payload = {"description": "No name"}
    headers = {"Authorization": "Bearer valid_token"}

    response = client.post("/flags", json=payload, headers=headers)
    assert response.status_code == 400
    assert "obrigatório" in response.get_json()["error"]


# --- GET /flags & GET /flags/<name> Tests ---

@patch("requests.get")
def test_get_flags_success(mock_requests_get, client, mock_db):
    mock_requests_get.return_value.status_code = 200
    mock_cursor = mock_db["cursor"]
    mock_cursor.fetchall.return_value = [
        {"name": "flag-1", "is_enabled": True},
        {"name": "flag-2", "is_enabled": False},
    ]

    headers = {"Authorization": "Bearer valid_token"}
    response = client.get("/flags", headers=headers)
    assert response.status_code == 200
    assert len(response.get_json()) == 2


@patch("requests.get")
def test_get_flag_by_name_success(mock_requests_get, client, mock_db):
    mock_requests_get.return_value.status_code = 200
    mock_cursor = mock_db["cursor"]
    mock_cursor.fetchone.return_value = {"name": "flag-1", "is_enabled": True}

    headers = {"Authorization": "Bearer valid_token"}
    response = client.get("/flags/flag-1", headers=headers)
    assert response.status_code == 200
    assert response.get_json()["name"] == "flag-1"


@patch("requests.get")
def test_get_flag_not_found(mock_requests_get, client, mock_db):
    mock_requests_get.return_value.status_code = 200
    mock_cursor = mock_db["cursor"]
    mock_cursor.fetchone.return_value = None

    headers = {"Authorization": "Bearer valid_token"}
    response = client.get("/flags/nonexistent-flag", headers=headers)
    assert response.status_code == 404
    assert "Flag não encontrada" in response.get_json()["error"]


# --- DELETE /flags/<name> Tests ---

@patch("requests.get")
def test_delete_flag_success(mock_requests_get, client, mock_db):
    mock_requests_get.return_value.status_code = 200
    mock_cursor = mock_db["cursor"]
    mock_cursor.rowcount = 1

    headers = {"Authorization": "Bearer valid_token"}
    response = client.delete("/flags/flag-1", headers=headers)
    assert response.status_code == 204

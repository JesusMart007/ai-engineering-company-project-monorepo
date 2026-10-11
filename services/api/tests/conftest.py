import os
import sys
from pathlib import Path

import pytest

API_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(API_ROOT))

# Fixed auth settings for tests; real environment values win over .env, so this
# never depends on (or touches) the developer's services/api/.env.
os.environ["SECRET_KEY"] = "test-secret-key-not-for-production"
os.environ["ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"

from fastapi.testclient import TestClient  # noqa: E402

import security  # noqa: E402

# Production uses bcrypt's default cost; 4 rounds keeps the suite fast.
security.bcrypt = security.bcrypt.using(rounds=4)

import main  # noqa: E402
from database import DB_PATH_ENV, INCIDENTS_DB_PATH_ENV, USERS_DB_PATH_ENV  # noqa: E402

PASSWORD = "correct-horse-1"


@pytest.fixture()
def anon_client(tmp_path, monkeypatch):
    """API backed by temporary TinyDB files, with no credentials."""
    monkeypatch.setenv(DB_PATH_ENV, str(tmp_path / "suppliers.json"))
    monkeypatch.setenv(USERS_DB_PATH_ENV, str(tmp_path / "users.json"))
    monkeypatch.setenv(INCIDENTS_DB_PATH_ENV, str(tmp_path / "incidents.json"))
    with TestClient(main.app) as test_client:
        yield test_client


def register(client: TestClient, email: str, password: str = PASSWORD, **profile) -> dict:
    response = client.post("/users", json={"email": email, "password": password, **profile})
    assert response.status_code == 201, response.text
    return response.json()


def login(client: TestClient, email: str, password: str = PASSWORD) -> dict[str, str]:
    response = client.post("/auth/login", data={"username": email, "password": password})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.fixture()
def auth_client(anon_client):
    """Same API, with a registered user's bearer token sent on every request."""
    register(anon_client, "tester@nexova.example")
    anon_client.headers.update(login(anon_client, "tester@nexova.example"))
    return anon_client

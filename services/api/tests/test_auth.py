"""Auth tests: login, the bearer-token dependency and /auth/me."""

from __future__ import annotations

from datetime import timedelta

import pytest
from jose import jwt

from config import ALGORITHM, SECRET_KEY
from conftest import PASSWORD, login, register
from security import create_access_token


def test_full_flow_register_login_and_use_token(anon_client):
    user = register(anon_client, "ana@nexova.example", name="Ana", phone="+34 600 000 000", address="Madrid")
    response = anon_client.post("/auth/login", data={"username": "ana@nexova.example", "password": PASSWORD})
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    claims = jwt.decode(body["access_token"], SECRET_KEY, algorithms=[ALGORITHM])
    assert claims["sub"] == user["id"]
    assert "exp" in claims

    headers = {"Authorization": f"Bearer {body['access_token']}"}
    assert anon_client.get("/auth/me", headers=headers).json() == {
        "email": "ana@nexova.example",
        "role": "user",
        "profile": {"name": "Ana", "phone": "+34 600 000 000", "address": "Madrid"},
    }
    assert anon_client.get("/suppliers", headers=headers).status_code == 200


def test_login_email_is_case_insensitive(anon_client):
    register(anon_client, "ana@nexova.example")
    assert anon_client.post("/auth/login", data={"username": "ANA@Nexova.example", "password": PASSWORD}).status_code == 200


@pytest.mark.parametrize(
    ("username", "password"),
    [("ana@nexova.example", "wrong-password"), ("nobody@nexova.example", PASSWORD)],
    ids=["wrong-password", "unknown-email"],
)
def test_bad_credentials_get_the_same_generic_401(anon_client, username, password):
    register(anon_client, "ana@nexova.example")
    response = anon_client.post("/auth/login", data={"username": username, "password": password})
    assert response.status_code == 401
    assert response.json() == {"detail": "Incorrect email or password"}


def test_inactive_user_cannot_log_in_or_use_an_existing_token(anon_client):
    user = register(anon_client, "ana@nexova.example")
    headers = login(anon_client, "ana@nexova.example")
    anon_client.app.state.user_repository.update_user(user["id"], {"is_active": False})
    assert anon_client.post("/auth/login", data={"username": "ana@nexova.example", "password": PASSWORD}).status_code == 401
    assert anon_client.get("/auth/me", headers=headers).status_code == 401


@pytest.mark.parametrize(
    "headers",
    [
        pytest.param({}, id="no-header"),
        pytest.param({"Authorization": "Bearer not-a-jwt"}, id="malformed"),
        pytest.param({"Authorization": "Basic YWJjOmRlZg=="}, id="wrong-scheme"),
        pytest.param(
            {"Authorization": "Bearer " + jwt.encode({"sub": "x"}, "another-secret", algorithm="HS256")},
            id="wrong-signature",
        ),
    ],
)
def test_protected_route_rejects_missing_or_bad_token(anon_client, headers):
    response = anon_client.get("/auth/me", headers=headers)
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_expired_token_is_rejected(anon_client):
    user = register(anon_client, "ana@nexova.example")
    token = create_access_token(user["id"], expires_delta=timedelta(seconds=-1))
    response = anon_client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_token_of_deleted_user_is_rejected(anon_client):
    user = register(anon_client, "ana@nexova.example")
    headers = login(anon_client, "ana@nexova.example")
    assert anon_client.delete(f"/users/{user['id']}", headers=headers).status_code == 204
    assert anon_client.get("/auth/me", headers=headers).status_code == 401

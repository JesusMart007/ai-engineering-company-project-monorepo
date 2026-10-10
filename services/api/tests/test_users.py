"""User tests: sign-up rules, hidden password hash, and owner/admin checks."""

from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest

from conftest import PASSWORD, login, register
from security import verify_password


def _make_admin(client, user_id: str) -> None:
    client.app.state.user_repository.update_user(user_id, {"role": "admin"})


def test_register_returns_public_fields_only(anon_client):
    body = register(anon_client, "ana@nexova.example", name="Ana")
    assert set(body) == {"id", "email", "is_active", "role", "created_at"}
    assert body["role"] == "user" and body["is_active"] is True
    assert datetime.fromisoformat(body["created_at"]).utcoffset() == UTC.utcoffset(None)


def test_password_is_stored_hashed(anon_client, tmp_path):
    user = register(anon_client, "ana@nexova.example")
    stored = anon_client.app.state.user_repository.get_user(user["id"])
    assert stored.hashed_password != PASSWORD
    assert verify_password(PASSWORD, stored.hashed_password)
    assert PASSWORD not in (tmp_path / "users.json").read_text(encoding="utf-8")


def test_register_creates_the_linked_profile(anon_client, tmp_path):
    user = register(anon_client, "ana@nexova.example", name="Ana", phone="600", address="Madrid")
    profiles = json.loads((tmp_path / "users.json").read_text(encoding="utf-8"))["profiles"]
    assert [p for p in profiles.values() if p["user_id"] == user["id"]][0]["name"] == "Ana"


def test_duplicate_email_is_409(anon_client):
    register(anon_client, "ana@nexova.example")
    response = anon_client.post("/users", json={"email": "ANA@nexova.example", "password": PASSWORD})
    assert response.status_code == 409


@pytest.mark.parametrize(
    "payload",
    [
        pytest.param({"email": "x@nexova.example", "password": PASSWORD, "role": "admin"}, id="role-admin"),
        pytest.param({"email": "x@nexova.example", "password": PASSWORD, "role": "manager"}, id="role-manager"),
        pytest.param({"email": "not-an-email", "password": PASSWORD}, id="bad-email"),
        pytest.param({"email": "x@nexova.example", "password": "short"}, id="short-password"),
        pytest.param({"email": "x@nexova.example"}, id="missing-password"),
    ],
)
def test_register_rejects_invalid_payload(anon_client, payload):
    assert anon_client.post("/users", json=payload).status_code == 422


@pytest.mark.parametrize(
    ("method", "path"),
    [("GET", "/users"), ("GET", "/users/x"), ("PUT", "/users/x"), ("DELETE", "/users/x"), ("GET", "/profiles/me"), ("PUT", "/profiles/me")],
)
def test_user_routes_require_a_token(anon_client, method, path):
    assert anon_client.request(method, path, json={}).status_code == 401


def test_list_and_get_users_never_expose_the_hash(auth_client):
    users = auth_client.get("/users").json()
    assert len(users) == 1
    assert "hashed_password" not in users[0]
    assert auth_client.get(f"/users/{users[0]['id']}").json() == users[0]
    assert auth_client.get("/users/unknown").status_code == 404


def test_user_updates_own_email_and_password(anon_client):
    user = register(anon_client, "ana@nexova.example")
    headers = login(anon_client, "ana@nexova.example")
    response = anon_client.put(
        f"/users/{user['id']}", json={"email": "ana.new@nexova.example", "password": "new-password-1"}, headers=headers
    )
    assert response.status_code == 200
    assert response.json()["email"] == "ana.new@nexova.example"
    login(anon_client, "ana.new@nexova.example", "new-password-1")
    assert anon_client.post("/auth/login", data={"username": "ana.new@nexova.example", "password": PASSWORD}).status_code == 401


def test_update_to_an_email_in_use_is_409(anon_client):
    user = register(anon_client, "ana@nexova.example")
    register(anon_client, "bob@nexova.example")
    headers = login(anon_client, "ana@nexova.example")
    assert anon_client.put(f"/users/{user['id']}", json={"email": "bob@nexova.example"}, headers=headers).status_code == 409


def test_user_cannot_change_own_role(anon_client):
    user = register(anon_client, "ana@nexova.example")
    headers = login(anon_client, "ana@nexova.example")
    assert anon_client.put(f"/users/{user['id']}", json={"role": "admin"}, headers=headers).status_code == 403
    assert anon_client.get(f"/users/{user['id']}", headers=headers).json()["role"] == "user"


def test_role_rejects_unknown_values(anon_client):
    admin = register(anon_client, "admin@nexova.example")
    _make_admin(anon_client, admin["id"])
    headers = login(anon_client, "admin@nexova.example")
    assert anon_client.put(f"/users/{admin['id']}", json={"role": "superuser"}, headers=headers).status_code == 422


@pytest.mark.parametrize(
    ("method", "payload"),
    [("PUT", {"email": "hacked@nexova.example"}), ("PUT", {"password": "hacked-pass-1"}), ("DELETE", None)],
)
def test_user_a_cannot_modify_user_b(anon_client, method, payload):
    register(anon_client, "ana@nexova.example")
    bob = register(anon_client, "bob@nexova.example")
    headers = login(anon_client, "ana@nexova.example")
    assert anon_client.request(method, f"/users/{bob['id']}", json=payload, headers=headers).status_code == 403
    assert anon_client.get(f"/users/{bob['id']}", headers=headers).json() == bob


def test_admin_can_update_role_and_delete_other_users(anon_client):
    admin = register(anon_client, "admin@nexova.example")
    _make_admin(anon_client, admin["id"])
    bob = register(anon_client, "bob@nexova.example")
    headers = login(anon_client, "admin@nexova.example")
    assert anon_client.put(f"/users/{bob['id']}", json={"role": "manager"}, headers=headers).json()["role"] == "manager"
    assert anon_client.delete(f"/users/{bob['id']}", headers=headers).status_code == 204
    assert anon_client.get(f"/users/{bob['id']}", headers=headers).status_code == 404
    assert anon_client.delete(f"/users/{bob['id']}", headers=headers).status_code == 404


def test_delete_removes_the_profile_too(anon_client, tmp_path):
    user = register(anon_client, "ana@nexova.example", name="Ana")
    headers = login(anon_client, "ana@nexova.example")
    assert anon_client.delete(f"/users/{user['id']}", headers=headers).status_code == 204
    data = json.loads((tmp_path / "users.json").read_text(encoding="utf-8"))
    assert data["users"] == {} and data["profiles"] == {}

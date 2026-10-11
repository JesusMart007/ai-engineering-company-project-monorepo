"""App-wide error handling: generic JSON 500 and 422 without the submitted values."""

from __future__ import annotations

import logging

import pytest
from fastapi.testclient import TestClient

import main
from conftest import login, register
from database import DB_PATH_ENV, INCIDENTS_DB_PATH_ENV, USERS_DB_PATH_ENV


@pytest.fixture()
def lenient_client(tmp_path, monkeypatch):
    """Like auth_client, but returns 500 responses instead of re-raising server errors."""
    monkeypatch.setenv(DB_PATH_ENV, str(tmp_path / "suppliers.json"))
    monkeypatch.setenv(USERS_DB_PATH_ENV, str(tmp_path / "users.json"))
    monkeypatch.setenv(INCIDENTS_DB_PATH_ENV, str(tmp_path / "incidents.json"))
    with TestClient(main.app, raise_server_exceptions=False) as client:
        register(client, "errors@nexova.example")
        client.headers.update(login(client, "errors@nexova.example"))
        yield client


@pytest.mark.parametrize("path", ["/suppliers", "/users", "/profiles/me", "/auth/me"])
def test_unexpected_error_is_generic_json_500_and_logged(lenient_client, monkeypatch, caplog, path):
    def explode(*_, **__):
        raise RuntimeError("secret detail: /srv/data/users.json")

    state = lenient_client.app.state
    monkeypatch.setattr(state.supplier_repository, "list", explode)
    monkeypatch.setattr(state.user_repository, "list_users", explode)
    monkeypatch.setattr(state.user_repository, "get_profile", explode)
    with caplog.at_level(logging.ERROR, logger="errors"):
        response = lenient_client.get(path)
    assert response.status_code == 500
    assert response.headers["content-type"] == "application/json"
    assert response.json() == {"detail": "Ha ocurrido un error inesperado"}
    assert "secret" not in response.text and "Traceback" not in response.text
    assert f"Unexpected error in GET {path}" in caplog.text
    assert "secret detail" in caplog.text


@pytest.mark.parametrize(
    ("path", "payload", "secret"),
    [
        ("/users", {"email": "new@nexova.example", "password": "short1"}, "short1"),
        ("/auth/reset-password", {"token": "eyJsecret.reset.token", "new_password": "x"}, "eyJsecret.reset.token"),
        ("/auth/change-password", {"current_password": "MyCurrentPass!", "new_password": "y"}, "MyCurrentPass!"),
    ],
)
def test_422_keeps_field_details_but_never_echoes_input(lenient_client, path, payload, secret):
    response = lenient_client.post(path, json=payload)
    assert response.status_code == 422
    assert secret not in response.text
    issues = response.json()["detail"]
    assert all("input" not in issue for issue in issues)
    assert all({"loc", "msg", "type"} <= issue.keys() for issue in issues)


def test_422_keeps_ctx_used_by_the_signup_form(anon_client):
    issue = anon_client.post("/users", json={"email": "a@nexova.example", "password": "short"}).json()["detail"][0]
    assert issue == {
        "type": "string_too_short",
        "loc": ["body", "password"],
        "msg": "String should have at least 8 characters",
        "ctx": {"min_length": 8},
    }


def test_unknown_route_and_method_keep_json_bodies(anon_client):
    assert anon_client.get("/nope").json() == {"detail": "Not Found"}
    assert anon_client.delete("/health").status_code == 405

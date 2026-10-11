"""/auth/me and /profiles/me resolve the identity from the token, never from the request."""

from __future__ import annotations

from conftest import login, register


def test_me_returns_the_data_of_the_token_owner_only(anon_client):
    register(anon_client, "ana@nexova.example", name="Ana")
    register(anon_client, "bob@nexova.example", name="Bob")
    ana, bob = login(anon_client, "ana@nexova.example"), login(anon_client, "bob@nexova.example")
    assert anon_client.get("/auth/me", headers=ana).json()["email"] == "ana@nexova.example"
    assert anon_client.get("/auth/me", headers=bob).json()["profile"]["name"] == "Bob"


def test_me_has_no_profile_when_the_user_has_none(anon_client):
    user = register(anon_client, "ana@nexova.example")
    headers = login(anon_client, "ana@nexova.example")
    anon_client.app.state.user_repository._profiles.truncate()
    assert anon_client.get("/auth/me", headers=headers).json()["profile"] is None
    assert anon_client.get("/profiles/me", headers=headers).status_code == 404
    assert user["id"]


def test_me_reflects_a_role_change_on_the_next_request(anon_client):
    user = register(anon_client, "ana@nexova.example")
    headers = login(anon_client, "ana@nexova.example")
    anon_client.app.state.user_repository.update_user(user["id"], {"role": "manager"})
    assert anon_client.get("/auth/me", headers=headers).json()["role"] == "manager"


def test_me_and_profile_routes_reject_missing_and_invalid_tokens(anon_client):
    for path in ("/auth/me", "/profiles/me"):
        assert anon_client.get(path).status_code == 401
        assert anon_client.get(path, headers={"Authorization": "Bearer nope"}).status_code == 401

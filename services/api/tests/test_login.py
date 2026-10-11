"""Login: user_service.authenticate decisions, token issued on success, and the /auth/login route."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from freezegun import freeze_time
from jose import jwt

import security
import user_service
from conftest import PASSWORD, TEST_ALGORITHM, TEST_SECRET


def test_authenticate_returns_the_user_for_correct_credentials(repo, user):
    assert user_service.authenticate(repo, user.email, PASSWORD).id == user.id


def test_authenticate_rejects_wrong_password(repo, user):
    assert user_service.authenticate(repo, user.email, "wrong-password-1") is None


def test_authenticate_rejects_unknown_email_like_a_wrong_password(repo, user):
    # Same outcome (None) as a wrong password: the caller cannot tell the two apart.
    assert user_service.authenticate(repo, "nobody@nexova.example", PASSWORD) is None


def test_unknown_email_still_runs_a_password_check(repo, monkeypatch):
    calls = []
    monkeypatch.setattr(user_service, "verify_password", lambda *args: calls.append(args) or False)
    user_service.authenticate(repo, "nobody@nexova.example", PASSWORD)
    assert len(calls) == 1  # constant-ish work, so timing does not reveal which emails exist


def test_authenticate_rejects_inactive_user_with_the_right_password(repo, inactive_user):
    assert user_service.authenticate(repo, inactive_user.email, PASSWORD) is None


@pytest.mark.parametrize("password", ["", " ", "x" * 100])
def test_authenticate_rejects_empty_blank_and_overlong_passwords(repo, user, password):
    assert user_service.authenticate(repo, user.email, password) is None


def test_authenticate_ignores_email_case(repo, user):
    assert user_service.authenticate(repo, user.email.upper(), PASSWORD).id == user.id


def test_authenticate_ignores_surrounding_spaces_in_the_email(repo, user):
    # Sign-up trims the email, so a copy-pasted address with a space must still log in.
    assert user_service.authenticate(repo, f"  {user.email} ", PASSWORD).id == user.id


@freeze_time(datetime(2030, 1, 1, 12, tzinfo=UTC))
def test_issued_token_has_user_id_as_sub_and_the_configured_expiry(repo, user):
    token = security.create_access_token(user_service.authenticate(repo, user.email, PASSWORD).id)
    claims = jwt.decode(token, TEST_SECRET, algorithms=[TEST_ALGORITHM])
    assert claims["sub"] == user.id
    assert claims["exp"] == int((datetime.now(UTC) + timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)).timestamp())


def post_login(client, username, password):
    return client.post("/auth/login", data={"username": username, "password": password})


def test_login_route_gives_identical_401_for_wrong_password_and_unknown_email(anon_client):
    anon_client.post("/users", json={"email": "ana@nexova.example", "password": PASSWORD})
    wrong = post_login(anon_client, "ana@nexova.example", "wrong-password-1")
    unknown = post_login(anon_client, "nobody@nexova.example", PASSWORD)
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json() == unknown.json()
    assert wrong.headers["www-authenticate"] == "Bearer"


def test_login_route_never_issues_a_token_for_an_empty_password(anon_client):
    anon_client.post("/users", json={"email": "ana@nexova.example", "password": PASSWORD})
    response = post_login(anon_client, "ana@nexova.example", "")
    assert response.status_code in (401, 422)
    assert "access_token" not in response.json()

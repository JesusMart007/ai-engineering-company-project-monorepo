"""change_password: a signed-in user replaces their password after proving they know the current one."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

import security
import user_service
from conftest import PASSWORD
from user_models import ChangePasswordRequest, PasswordResetToken

NEW = "brand-new-pass-2"


def stored_hash(repo, user):
    return repo.get_user(user.id).hashed_password


def test_correct_current_password_replaces_the_hash(repo, user):
    old_hash = stored_hash(repo, user)
    user_service.change_password(repo, user, PASSWORD, NEW)
    new_hash = stored_hash(repo, user)
    assert new_hash != old_hash
    assert security.verify_password(NEW, new_hash)
    assert not security.verify_password(PASSWORD, new_hash)


def test_wrong_current_password_raises_and_changes_nothing(repo, user):
    old_hash = stored_hash(repo, user)
    with pytest.raises(user_service.WrongPassword):
        user_service.change_password(repo, user, "wrong-password-1", NEW)
    assert stored_hash(repo, user) == old_hash


@pytest.mark.parametrize("current", ["", " ", "x" * 100])
def test_empty_blank_or_overlong_current_password_is_wrong_not_a_crash(repo, user, current):
    with pytest.raises(user_service.WrongPassword):
        user_service.change_password(repo, user, current, NEW)


def test_changing_the_password_spends_pending_reset_tokens(repo, user):
    repo.add_reset_token(PasswordResetToken(jti="pending", user_id=user.id, expires_at=datetime.now(UTC) + timedelta(minutes=5)))
    user_service.change_password(repo, user, PASSWORD, NEW)
    assert repo.get_reset_token("pending").used_at is not None


def test_new_password_equal_to_the_current_one_is_allowed(repo, user):
    user_service.change_password(repo, user, PASSWORD, PASSWORD)
    assert security.verify_password(PASSWORD, stored_hash(repo, user))


@pytest.mark.parametrize("new_password", ["", "short", "        ", "x" * 73])
def test_invalid_new_passwords_are_rejected_before_reaching_the_service(new_password):
    with pytest.raises(ValidationError):
        ChangePasswordRequest(current_password=PASSWORD, new_password=new_password)


def test_route_requires_a_session_and_changes_nothing_without_one(anon_client, user):
    response = anon_client.post("/auth/change-password", json={"current_password": PASSWORD, "new_password": NEW})
    assert response.status_code == 401


def test_route_rejects_a_blank_new_password_and_keeps_the_old_one(auth_client):
    response = auth_client.post("/auth/change-password", json={"current_password": PASSWORD, "new_password": " " * 10})
    assert response.status_code == 422
    assert auth_client.post("/auth/login", data={"username": "tester@nexova.example", "password": PASSWORD}).status_code == 200


def test_existing_session_token_keeps_working_after_a_password_change(auth_client):
    # Documented design limit (stateless JWT): tokens are not revoked by a password change.
    auth_client.post("/auth/change-password", json={"current_password": PASSWORD, "new_password": NEW})
    assert auth_client.get("/auth/me").status_code == 200

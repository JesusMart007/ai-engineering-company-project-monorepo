"""Token creation/decoding, password hashing and the get_current_user dependency (called directly)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from fastapi import HTTPException
from freezegun import freeze_time
from jose import jwt

import security
from conftest import TEST_ALGORITHM, TEST_SECRET
from dependencies import get_current_user
from security import InvalidToken, create_access_token, create_reset_token, decode_access_token, decode_reset_token
from user_models import Role

START = datetime(2030, 1, 1, 12, 0, tzinfo=UTC)
ACCESS_MINUTES = security.ACCESS_TOKEN_EXPIRE_MINUTES  # 30 in the test environment


def claims_of(token: str) -> dict:
    return jwt.decode(token, TEST_SECRET, algorithms=[TEST_ALGORITHM])


def current_user_error(token, repo) -> HTTPException:
    with pytest.raises(HTTPException) as caught:
        get_current_user(token, repo)
    return caught.value


# --- creation ---------------------------------------------------------------------------------

@freeze_time(START)
def test_access_token_carries_subject_type_and_expiry_from_the_setting():
    claims = claims_of(create_access_token("user-1"))
    assert claims["sub"] == "user-1"
    assert claims["type"] == "access"
    # Regression from the ticket: exp is exactly now + ACCESS_TOKEN_EXPIRE_MINUTES.
    assert claims["exp"] == int((START + timedelta(minutes=ACCESS_MINUTES)).timestamp())


@freeze_time(START)
def test_explicit_expires_delta_overrides_the_default():
    assert claims_of(create_access_token("u", timedelta(minutes=5)))["exp"] == int((START + timedelta(minutes=5)).timestamp())


def test_token_is_rejected_after_the_configured_minutes_and_accepted_just_before():
    with freeze_time(START) as clock:
        token = create_access_token("user-1")
        clock.move_to(START + timedelta(minutes=ACCESS_MINUTES, seconds=-1))
        assert decode_access_token(token) == "user-1"
        clock.move_to(START + timedelta(minutes=ACCESS_MINUTES, seconds=1))
        with pytest.raises(InvalidToken):
            decode_access_token(token)


# --- decoding failures ------------------------------------------------------------------------

def test_decode_returns_the_subject_of_a_valid_token(make_token):
    assert decode_access_token(make_token("abc")) == "abc"


def test_token_signed_with_another_key_is_rejected(make_token):
    with pytest.raises(InvalidToken):
        decode_access_token(make_token("abc", key="another-secret-key-of-same-length!!"))


@pytest.mark.parametrize("token", ["", "abc", "a.b.c", "a.b", "....", "Bearer xyz"])
def test_malformed_tokens_are_rejected(token):
    with pytest.raises(InvalidToken):
        decode_access_token(token)


@pytest.mark.parametrize("sub", [None, ""], ids=["missing-sub", "empty-sub"])
def test_token_without_a_subject_is_rejected(make_token, sub):
    with pytest.raises(InvalidToken):
        decode_access_token(make_token(sub))


def test_token_with_non_string_subject_is_rejected(make_token):
    with pytest.raises(InvalidToken):
        decode_access_token(make_token(123))


def test_unsigned_alg_none_token_is_rejected():
    import base64
    import json

    def part(data):
        return base64.urlsafe_b64encode(json.dumps(data).encode()).rstrip(b"=").decode()

    forged = f"{part({'alg': 'none', 'typ': 'JWT'})}.{part({'sub': 'u', 'type': 'access'})}."
    with pytest.raises(InvalidToken):
        decode_access_token(forged)


def test_token_signed_with_a_different_algorithm_is_rejected(make_token):
    # Correct key, but HS512 while the API only accepts the configured algorithm.
    with pytest.raises(InvalidToken):
        decode_access_token(make_token("abc", algorithm="HS512"))


def test_token_without_type_claim_is_not_a_session_token(make_token):
    with pytest.raises(InvalidToken):
        decode_access_token(make_token("abc", type=None))


def test_token_without_expiry_is_rejected(make_token):
    # A validly signed token with no `exp` would never expire; the API always sets one.
    token = jwt.encode({"sub": "abc", "type": "access"}, TEST_SECRET, algorithm=TEST_ALGORITHM)
    with pytest.raises(InvalidToken):
        decode_access_token(token)


def test_reset_and_access_tokens_are_not_interchangeable():
    reset = create_reset_token("user-1")
    with pytest.raises(InvalidToken):
        decode_access_token(reset.token)
    with pytest.raises(InvalidToken):
        decode_reset_token(create_access_token("user-1"))


def test_reset_token_roundtrip_returns_user_and_jti():
    reset = create_reset_token("user-1")
    assert decode_reset_token(reset.token) == ("user-1", reset.jti)


def test_reset_token_without_jti_is_rejected(make_token):
    with pytest.raises(InvalidToken):
        decode_reset_token(make_token("u", type="password_reset"))


# --- hashing ----------------------------------------------------------------------------------

def test_hash_is_not_the_password_and_is_salted():
    first, second = security.hash_password("secret-pass-1"), security.hash_password("secret-pass-1")
    assert "secret-pass-1" not in first
    assert first != second  # random salt
    assert security.verify_password("secret-pass-1", first) and security.verify_password("secret-pass-1", second)


@pytest.mark.parametrize("candidate", ["", "wrong", "secret-pass-1 ", "x" * 100])
def test_verify_password_rejects_wrong_empty_and_overlong_candidates(candidate):
    assert security.verify_password(candidate, security.hash_password("secret-pass-1")) is False


# --- get_current_user -------------------------------------------------------------------------

def test_get_current_user_returns_the_token_owner(repo, user, admin, make_token):
    assert get_current_user(make_token(user.id), repo).id == user.id
    assert get_current_user(make_token(admin.id), repo).role == Role.ADMIN


@pytest.mark.parametrize("token", [None, ""], ids=["no-header", "empty"])
def test_get_current_user_without_token_is_401_with_bearer_challenge(repo, token):
    error = current_user_error(token, repo)
    assert error.status_code == 401
    assert error.headers == {"WWW-Authenticate": "Bearer"}


def test_get_current_user_rejects_expired_token(repo, user, make_token):
    assert current_user_error(make_token(user.id, expires_in=timedelta(seconds=-1)), repo).status_code == 401


def test_get_current_user_rejects_forged_malformed_and_reset_tokens(repo, user, make_token):
    for token in (make_token(user.id, key="not-the-real-secret-not-the-real-one"), "garbage", create_reset_token(user.id).token):
        assert current_user_error(token, repo).status_code == 401


def test_get_current_user_rejects_token_of_a_deleted_user(repo, user, make_token):
    token = make_token(user.id)
    repo.delete_user_with_profile(user.id)
    assert current_user_error(token, repo).status_code == 401


def test_get_current_user_rejects_inactive_user_even_with_a_valid_token(repo, inactive_user, make_token):
    assert current_user_error(make_token(inactive_user.id), repo).status_code == 401


def test_get_current_user_reads_the_role_from_the_database_not_the_token(repo, user, make_token):
    token = make_token(user.id)
    repo.update_user(user.id, {"role": "admin"})
    assert get_current_user(token, repo).role == Role.ADMIN

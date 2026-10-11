"""Sign-up: user_service.create_user and the UserCreate rules, plus the public POST /users decision."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

import security
import user_service
from conftest import PASSWORD
from database import EmailAlreadyRegistered
from user_models import Role, UserCreate


def sign_up(repo, email="ana@nexova.example", password=PASSWORD, **profile):
    return user_service.create_user(repo, UserCreate(email=email, password=password, **profile))


def test_register_creates_active_user_with_default_role_user(repo):
    created = sign_up(repo)
    stored = repo.get_user(created.id)
    assert stored.role == Role.USER
    assert stored.is_active is True
    assert stored.email == "ana@nexova.example"


def test_register_stores_a_verifiable_hash_never_the_plain_password(repo):
    stored = repo.get_user(sign_up(repo).id)
    assert stored.hashed_password != PASSWORD
    assert PASSWORD not in stored.hashed_password
    assert security.verify_password(PASSWORD, stored.hashed_password)


def test_register_creates_the_profile_with_optional_fields(repo):
    created = sign_up(repo, name="Ana", phone="+34 600", address="Madrid")
    profile = repo.get_profile(created.id)
    assert (profile.name, profile.phone, profile.address) == ("Ana", "+34 600", "Madrid")


def test_register_without_optional_fields_still_creates_an_empty_profile(repo):
    profile = repo.get_profile(sign_up(repo).id)
    assert profile is not None
    assert (profile.name, profile.phone, profile.address) == (None, None, None)


def test_duplicate_email_is_rejected_and_nothing_extra_is_stored(repo):
    sign_up(repo)
    with pytest.raises(EmailAlreadyRegistered):
        sign_up(repo, password="another-pass-9")
    assert len(repo.list_users()) == 1
    assert len(repo._profiles.all()) == 1  # no orphan profile from the failed attempt


@pytest.mark.parametrize("variant", ["ANA@NEXOVA.EXAMPLE", "Ana@Nexova.Example", "  ana@nexova.example  "])
def test_email_with_other_case_or_spaces_counts_as_duplicate(repo, variant):
    sign_up(repo)
    with pytest.raises(EmailAlreadyRegistered):
        sign_up(repo, email=variant)


@pytest.mark.parametrize("password", ["", "short", "       ", "        ", " " * 20])
def test_empty_short_or_blank_passwords_are_rejected(password):
    # Whitespace-only passwords have 8+ characters but carry no secret.
    with pytest.raises(ValidationError):
        UserCreate(email="ana@nexova.example", password=password)


@pytest.mark.parametrize("password", ["a" * 8, "a" * 72, "ñ" * 36, "pass word 1"], ids=["8-chars", "72-bytes", "72-bytes-multibyte", "inner-space"])
def test_password_length_boundaries_accepted(password):
    assert UserCreate(email="ana@nexova.example", password=password).password == password


@pytest.mark.parametrize("password", ["a" * 73, "ñ" * 37], ids=["73-bytes", "74-bytes-multibyte"])
def test_password_over_72_bytes_is_rejected(password):
    # bcrypt would silently truncate it.
    with pytest.raises(ValidationError):
        UserCreate(email="ana@nexova.example", password=password)


@pytest.mark.parametrize("email", ["not-an-email", "a@", "@b.com", "", "a b@c.com"])
def test_invalid_email_is_rejected(email):
    with pytest.raises(ValidationError):
        UserCreate(email=email, password=PASSWORD)


def test_signup_payload_cannot_carry_a_role():
    with pytest.raises(ValidationError):
        UserCreate(email="ana@nexova.example", password=PASSWORD, role="admin")


def test_public_endpoint_refuses_admin_role_and_creates_nobody(anon_client):
    response = anon_client.post("/users", json={"email": "evil@nexova.example", "password": PASSWORD, "role": "admin"})
    assert response.status_code == 422
    assert anon_client.app.state.user_repository.list_users() == []


def test_public_endpoint_maps_duplicate_to_409_without_a_second_user(anon_client):
    payload = {"email": "ana@nexova.example", "password": PASSWORD}
    assert anon_client.post("/users", json=payload).status_code == 201
    assert anon_client.post("/users", json={**payload, "email": "ANA@nexova.example"}).status_code == 409
    assert len(anon_client.app.state.user_repository.list_users()) == 1

"""Business logic for users and profiles.

Routes call these functions; they hash passwords and build records, and leave
storage to UserRepository.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from urllib.parse import urlencode

from config import FRONTEND_URL, RESET_TOKEN_EXPIRE_MINUTES
from database import UserRepository
from email_service import send_password_reset_email
from security import InvalidToken, create_reset_token, decode_reset_token, hash_password, verify_password
from user_models import PasswordResetToken, Profile, ProfileUpdate, Role, User, UserCreate, UserUpdate


def create_user(repository: UserRepository, data: UserCreate) -> User:
    """Register a user with role `user` and its profile. Raises EmailAlreadyRegistered."""
    user = User(
        id=str(uuid.uuid4()),
        email=data.email,
        hashed_password=hash_password(data.password),
        is_active=True,
        role=Role.USER,
        created_at=datetime.now(UTC),
    )
    profile = Profile(id=str(uuid.uuid4()), user_id=user.id, name=data.name, phone=data.phone, address=data.address)
    return repository.create_user_with_profile(user, profile)


def get_user_by_id(repository: UserRepository, user_id: str) -> User | None:
    return repository.get_user(user_id)


def get_user_by_email(repository: UserRepository, email: str) -> User | None:
    return repository.get_user_by_email(email.lower())


def list_users(repository: UserRepository) -> list[User]:
    return repository.list_users()


def update_user(repository: UserRepository, user_id: str, data: UserUpdate) -> User | None:
    """Apply the fields that were sent. Raises EmailAlreadyRegistered."""
    fields: dict = {}
    if data.email is not None:
        fields["email"] = data.email
    if data.password is not None:
        fields["hashed_password"] = hash_password(data.password)
    if data.role is not None:
        fields["role"] = data.role.value
    if not fields:
        return repository.get_user(user_id)
    return repository.update_user(user_id, fields)


def delete_user(repository: UserRepository, user_id: str) -> bool:
    """Delete the user and its profile. Returns False if the user did not exist."""
    return repository.delete_user_with_profile(user_id)


# Checked against unknown emails so a failed login takes as long whether or not the email exists.
_DUMMY_HASH = hash_password("not-a-real-password")


def authenticate(repository: UserRepository, email: str, password: str) -> User | None:
    """Return the user only if the email exists, the password matches and the account is active."""
    user = get_user_by_email(repository, email)
    if user is None:
        verify_password(password, _DUMMY_HASH)
        return None
    if not verify_password(password, user.hashed_password) or not user.is_active:
        return None
    return user


def get_profile(repository: UserRepository, user_id: str) -> Profile | None:
    return repository.get_profile(user_id)


def update_profile(repository: UserRepository, user_id: str, data: ProfileUpdate) -> Profile:
    """Update name, phone and address, creating the profile if it was missing."""
    current = repository.get_profile(user_id) or Profile(id=str(uuid.uuid4()), user_id=user_id)
    return repository.upsert_profile(current.model_copy(update=data.model_dump(exclude_unset=True)))


class InvalidResetToken(Exception):
    """The reset link is malformed, badly signed, expired, already used or for an inactive user."""


class WrongPassword(Exception):
    pass


def request_password_reset(repository: UserRepository, email: str) -> None:
    """Email a single-use reset link if the account exists and is active; otherwise do nothing.

    Issuing a link spends any the user still had pending, so only the latest one works.
    """
    user = get_user_by_email(repository, email)
    if user is None or not user.is_active:
        return
    reset = create_reset_token(user.id)
    repository.add_reset_token(PasswordResetToken(jti=reset.jti, user_id=user.id, expires_at=reset.expires_at))
    link = f"{FRONTEND_URL}/reset-password?{urlencode({'token': reset.token})}"
    send_password_reset_email(user.email, link, RESET_TOKEN_EXPIRE_MINUTES)


def _set_password(repository: UserRepository, user_id: str, new_password: str) -> None:
    repository.update_user(user_id, {"hashed_password": hash_password(new_password)})
    repository.invalidate_reset_tokens(user_id)


def reset_password(repository: UserRepository, token: str, new_password: str) -> None:
    """Set a new password from a reset link and spend the link. Raises InvalidResetToken."""
    try:
        user_id, jti = decode_reset_token(token)
    except InvalidToken as error:
        raise InvalidResetToken from error
    user = repository.get_user(user_id)
    if user is None or not user.is_active or not repository.consume_reset_token(jti, user_id):
        raise InvalidResetToken
    _set_password(repository, user_id, new_password)


def change_password(repository: UserRepository, user: User, current_password: str, new_password: str) -> None:
    """Change the password of a signed-in user after checking the current one. Raises WrongPassword."""
    if not verify_password(current_password, user.hashed_password):
        raise WrongPassword
    _set_password(repository, user.id, new_password)

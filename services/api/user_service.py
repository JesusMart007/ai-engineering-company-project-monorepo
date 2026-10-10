"""Business logic for users and profiles.

Routes call these functions; they hash passwords and build records, and leave
storage to UserRepository.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from database import UserRepository
from security import hash_password, verify_password
from user_models import Profile, ProfileUpdate, Role, User, UserCreate, UserUpdate


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

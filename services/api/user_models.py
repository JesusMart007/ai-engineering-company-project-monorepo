"""Pydantic models for users, profiles and auth tokens.

Users and profiles live only in TinyDB. Other modules reference a user by its
TinyDB `id` (a uuid4 string) as `user_uuid`. `hashed_password` exists only on
the internal `User` model; every response model leaves it out.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, EmailStr, Field

# Emails are compared case-insensitively, so they are stored lowercased.
Email = Annotated[EmailStr, AfterValidator(str.lower)]


def _fits_bcrypt(password: str) -> str:
    if len(password.encode("utf-8")) > 72:
        raise ValueError("password must be at most 72 bytes")
    return password


Password = Annotated[str, Field(min_length=8), AfterValidator(_fits_bcrypt)]
OptionalText = Annotated[str | None, Field(default=None, max_length=200)]


class Role(StrEnum):
    ADMIN = "admin"
    MANAGER = "manager"
    USER = "user"


class ProfileFields(BaseModel):
    name: OptionalText
    phone: OptionalText
    address: OptionalText


class UserCreate(ProfileFields):
    """Public sign-up payload. `role` is not accepted: new users are always `user`."""

    model_config = ConfigDict(extra="forbid")

    email: Email
    password: Password


class UserUpdate(BaseModel):
    """Fields a user (or an admin) may change. Only an admin may send `role`."""

    model_config = ConfigDict(extra="forbid")

    email: Email | None = None
    password: Password | None = None
    role: Role | None = None


class UserPublic(BaseModel):
    """User as returned by the API: never includes the password hash."""

    model_config = ConfigDict(extra="ignore")

    id: str
    email: EmailStr
    is_active: bool
    role: Role
    created_at: datetime


class User(UserPublic):
    """User as stored in TinyDB. Internal only."""

    hashed_password: str


class ProfileUpdate(ProfileFields):
    model_config = ConfigDict(extra="forbid")


class Profile(ProfileFields):
    model_config = ConfigDict(extra="ignore")

    id: str
    user_id: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class Me(BaseModel):
    email: EmailStr
    role: Role
    profile: ProfileFields | None

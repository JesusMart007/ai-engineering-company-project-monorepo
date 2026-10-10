"""Shared FastAPI dependencies: the user repository and the authenticated user."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer

from database import UserRepository
from security import InvalidToken, decode_access_token
from user_models import User
from user_service import get_user_by_id

# auto_error=False so a missing header gets the same 401 (and header) as a bad token.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def get_user_repository(request: Request) -> UserRepository:
    return request.app.state.user_repository


UserRepo = Annotated[UserRepository, Depends(get_user_repository)]


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(token: Annotated[str | None, Depends(oauth2_scheme)], repository: UserRepo) -> User:
    """Resolve `Authorization: Bearer <token>` to an active user, or raise 401."""
    if not token:
        raise _unauthorized("Not authenticated")
    try:
        user_id = decode_access_token(token)
    except InvalidToken as error:
        raise _unauthorized("Invalid or expired token") from error
    user = get_user_by_id(repository, user_id)
    if user is None or not user.is_active:
        raise _unauthorized("Invalid or expired token")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]

"""Login and identity endpoints. Auth is stateless JWT: no sessions or cookies."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

import user_service
from dependencies import CurrentUser, UserRepo
from security import create_access_token
from user_models import Me, Token

router = APIRouter(prefix="/auth", tags=["auth"])

UNAUTHORIZED = {401: {"description": "Missing, malformed or expired token"}}


@router.post("/login", response_model=Token, responses={401: {"description": "Incorrect email or password"}})
def login(form: Annotated[OAuth2PasswordRequestForm, Depends()], repository: UserRepo) -> Token:
    """OAuth2 password flow: send the email in the `username` field."""
    user = user_service.authenticate(repository, form.username, form.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return Token(access_token=create_access_token(user.id))


@router.get("/me", response_model=Me, responses=UNAUTHORIZED)
def read_me(current: CurrentUser, repository: UserRepo) -> Me:
    return Me(email=current.email, role=current.role, profile=user_service.get_profile(repository, current.id))

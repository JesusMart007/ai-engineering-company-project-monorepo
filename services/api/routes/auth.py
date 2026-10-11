"""Login, identity and password endpoints. Auth is stateless JWT: no sessions or cookies."""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

import user_service
from database import UserRepository
from dependencies import CurrentUser, UserRepo
from security import create_access_token
from user_models import ChangePasswordRequest, ForgotPasswordRequest, Me, Message, ResetPasswordRequest, Token

logger = logging.getLogger(__name__)

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


FORGOT_PASSWORD_MESSAGE = "If that email is registered, a password reset link is on its way."


def _send_reset_link(repository: UserRepository, email: str) -> None:
    try:
        user_service.request_password_reset(repository, email)
    except Exception:
        logger.exception("Could not issue a password reset link")


@router.post("/forgot-password", response_model=Message)
def forgot_password(payload: ForgotPasswordRequest, background: BackgroundTasks, repository: UserRepo) -> Message:
    """Always answers the same, whether or not the email exists. The lookup, the token
    and the email all happen after the response, so its timing reveals nothing either."""
    background.add_task(_send_reset_link, repository, payload.email)
    return Message(detail=FORGOT_PASSWORD_MESSAGE)


@router.post(
    "/reset-password",
    response_model=Message,
    responses={400: {"description": "Invalid, expired or already used reset link"}},
)
def reset_password(payload: ResetPasswordRequest, repository: UserRepo) -> Message:
    try:
        user_service.reset_password(repository, payload.token, payload.new_password)
    except user_service.InvalidResetToken as error:
        raise HTTPException(status_code=400, detail="This reset link is invalid, expired or already used") from error
    return Message(detail="Password updated")


@router.post(
    "/change-password",
    response_model=Message,
    responses={**UNAUTHORIZED, 400: {"description": "The current password is incorrect"}},
)
def change_password(payload: ChangePasswordRequest, current: CurrentUser, repository: UserRepo) -> Message:
    try:
        user_service.change_password(repository, current, payload.current_password, payload.new_password)
    except user_service.WrongPassword as error:
        raise HTTPException(status_code=400, detail="The current password is incorrect") from error
    return Message(detail="Password updated")

"""Password hashing (bcrypt via libpass) and JWT signing (python-jose).

Every token carries a `type` claim: "access" for sessions, "password_reset" for
reset links. Each decoder accepts only its own type, so a reset link can never
be used as a bearer token, nor a session token as a reset link.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt
from passlib.hash import bcrypt

from config import ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM, RESET_TOKEN_EXPIRE_MINUTES, SECRET_KEY

ACCESS_TOKEN_TYPE = "access"
RESET_TOKEN_TYPE = "password_reset"


class InvalidToken(Exception):
    pass


def hash_password(password: str) -> str:
    return bcrypt.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return bcrypt.verify(password, hashed_password)


def _decode(token: str, expected_type: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError as error:
        raise InvalidToken(str(error)) from error
    if payload.get("type") != expected_type:
        raise InvalidToken(f"not a {expected_type} token")
    if not isinstance(payload.get("sub"), str) or not payload["sub"]:
        raise InvalidToken("token has no subject")
    return payload


def create_access_token(user_id: str, expires_delta: timedelta | None = None) -> str:
    expire = datetime.now(UTC) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    return jwt.encode({"sub": user_id, "exp": expire, "type": ACCESS_TOKEN_TYPE}, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> str:
    """Return the user id in `sub`. Raises InvalidToken if malformed, badly signed, expired or not an access token."""
    return _decode(token, ACCESS_TOKEN_TYPE)["sub"]


@dataclass(frozen=True)
class ResetToken:
    token: str
    jti: str
    user_id: str
    expires_at: datetime


def create_reset_token(user_id: str, expires_delta: timedelta | None = None) -> ResetToken:
    """Signed single-use reset token; the caller stores its `jti` so it can be spent only once."""
    jti = str(uuid.uuid4())
    expire = datetime.now(UTC) + (expires_delta or timedelta(minutes=RESET_TOKEN_EXPIRE_MINUTES))
    claims = {"sub": user_id, "exp": expire, "jti": jti, "type": RESET_TOKEN_TYPE}
    return ResetToken(jwt.encode(claims, SECRET_KEY, algorithm=ALGORITHM), jti, user_id, expire)


def decode_reset_token(token: str) -> tuple[str, str]:
    """Return (user_id, jti). Raises InvalidToken if malformed, badly signed, expired or not a reset token."""
    payload = _decode(token, RESET_TOKEN_TYPE)
    jti = payload.get("jti")
    if not isinstance(jti, str) or not jti:
        raise InvalidToken("reset token has no jti")
    return payload["sub"], jti

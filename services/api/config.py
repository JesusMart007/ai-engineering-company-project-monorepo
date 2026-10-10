"""Settings read from the environment, with services/api/.env loaded first.

Values already set in the real environment win over the .env file, so tests
and deployments can override them without editing files.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

API_ROOT = Path(__file__).resolve().parent
load_dotenv(API_ROOT / ".env")


def _required(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"{name} is not set; copy services/api/.env.example to services/api/.env and fill it in")
    return value


SECRET_KEY = _required("SECRET_KEY")
ALGORITHM = _required("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(_required("ACCESS_TOKEN_EXPIRE_MINUTES"))

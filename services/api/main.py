"""Nexova centralized API: supplier directory, incident analysis and management, and user accounts.

Run with `uv run uvicorn main:app --reload` from services/api.
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import (
    IncidentRepository,
    SupplierRepository,
    UserRepository,
    db_path_from_env,
    incidents_db_path_from_env,
    users_db_path_from_env,
)
from routes import auth, incidents, profiles, suppliers, users
from seed import seed

ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
    if origin.strip()
]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Open TinyDB once per process; seed it so the directory never starts empty.
    repository = SupplierRepository(db_path_from_env())
    if repository.count() == 0:
        seed(repository)
    app.state.supplier_repository = repository
    app.state.user_repository = UserRepository(users_db_path_from_env())
    # Incidents start empty; historical ones are loaded with scripts/seed_incidents.py.
    app.state.incident_repository = IncidentRepository(incidents_db_path_from_env())
    try:
        yield
    finally:
        repository.close()
        app.state.user_repository.close()
        app.state.incident_repository.close()


app = FastAPI(title="Nexova API", lifespan=lifespan)
app.include_router(suppliers.router)
app.include_router(incidents.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(profiles.router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

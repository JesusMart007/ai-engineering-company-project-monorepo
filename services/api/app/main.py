from fastapi import FastAPI

from app.routers.health import router as health_router

app = FastAPI(
    title="Nexova AgentHub API",
    description="API centralizada para las operaciones ejecutivas de Nexova.",
    version="0.1.0",
)

app.include_router(health_router, prefix="/api/v1")
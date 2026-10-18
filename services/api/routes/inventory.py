"""Inventory endpoints (Supabase via SQLModel). Authentication stays on TinyDB.

Every route requires a bearer token. There is no endpoint that edits stock: it only
changes by registering an inbound or outbound order, stamped with the TinyDB id of
the authenticated user (never taken from the request body).
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

import inventory_service as service
from database import get_db
from dependencies import CurrentUser, get_current_user
from inventory_schemas import (
    AssetCreate,
    AssetEntryCreate,
    AssetEntryResponse,
    AssetExitCreate,
    AssetExitResponse,
    AssetResponse,
    Office,
    OrderResponse,
)

router = APIRouter(
    prefix="/inventory",
    tags=["inventory"],
    dependencies=[Depends(get_current_user)],
    responses={401: {"description": "Missing, malformed or expired token"}},
)

DbSession = Annotated[Session, Depends(get_db)]

ASSET_NOT_FOUND = {404: {"description": "Asset not found"}}


def _not_found(error: service.AssetNotFound) -> HTTPException:
    return HTTPException(status_code=404, detail=str(error))


@router.get("/products", response_model=list[AssetResponse])
def list_products(session: DbSession, office: Office | None = None) -> list[AssetResponse]:
    return service.list_assets(session, office)


@router.post(
    "/products",
    response_model=AssetResponse,
    status_code=status.HTTP_201_CREATED,
    responses={409: {"description": "An asset with that sku already exists"}},
)
def create_product(payload: AssetCreate, session: DbSession) -> AssetResponse:
    try:
        return service.create_asset(session, payload)
    except service.SkuAlreadyExists as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@router.get("/products/{asset_id}", response_model=AssetResponse, responses=ASSET_NOT_FOUND)
def get_product(asset_id: int, session: DbSession) -> AssetResponse:
    try:
        return service.get_asset(session, asset_id)
    except service.AssetNotFound as error:
        raise _not_found(error) from error


@router.post(
    "/orders/inbound",
    response_model=AssetEntryResponse,
    status_code=status.HTTP_201_CREATED,
    responses=ASSET_NOT_FOUND,
)
def create_inbound_order(payload: AssetEntryCreate, session: DbSession, user: CurrentUser) -> AssetEntryResponse:
    try:
        return service.create_entry(session, payload, user.id)
    except service.AssetNotFound as error:
        raise _not_found(error) from error


@router.post(
    "/orders/outbound",
    response_model=AssetExitResponse,
    status_code=status.HTTP_201_CREATED,
    responses={**ASSET_NOT_FOUND, 400: {"description": "Insufficient stock; nothing was written"}},
)
def create_outbound_order(payload: AssetExitCreate, session: DbSession, user: CurrentUser) -> AssetExitResponse:
    try:
        return service.create_exit(session, payload, user.id)
    except service.AssetNotFound as error:
        raise _not_found(error) from error
    except service.InsufficientStock as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("/orders", response_model=list[OrderResponse])
def list_orders(session: DbSession, office: Office | None = None) -> list[OrderResponse]:
    return service.list_orders(session, office)

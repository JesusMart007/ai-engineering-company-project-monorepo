"""SQLModel tables of the inventory, stored in Supabase (Postgres).

`Asset` has no stock column: stock is derived from `AssetEntry` (adds) and
`AssetExit` (removes), so the only way to change it is to register an order.
`user_uuid` is the TinyDB user id, deliberately without a foreign key: no user
table exists in Postgres.

These are the database tables. API request/response shapes live in
inventory_schemas.py and are separate classes.
"""

from datetime import UTC, datetime

from sqlalchemy import DateTime
from sqlmodel import Field, Relationship, SQLModel


def _now() -> datetime:
    return datetime.now(UTC)


class Asset(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    sku: str = Field(unique=True, index=True)
    category: str
    office: str

    entries: list["AssetEntry"] = Relationship(back_populates="asset")
    exits: list["AssetExit"] = Relationship(back_populates="asset")


class AssetEntry(SQLModel, table=True):
    """A purchase or delivery received by Nexova."""

    id: int | None = Field(default=None, primary_key=True)
    asset_id: int = Field(foreign_key="asset.id", index=True)
    quantity: int
    supplier: str
    office: str
    created_at: datetime = Field(default_factory=_now, sa_type=DateTime(timezone=True))
    user_uuid: str

    asset: Asset = Relationship(back_populates="entries")


class AssetExit(SQLModel, table=True):
    """An allocation to an employee or a consumption."""

    id: int | None = Field(default=None, primary_key=True)
    asset_id: int = Field(foreign_key="asset.id", index=True)
    quantity: int
    exit_type: str
    assigned_to: str | None = None
    office: str
    created_at: datetime = Field(default_factory=_now, sa_type=DateTime(timezone=True))
    user_uuid: str

    asset: Asset = Relationship(back_populates="exits")

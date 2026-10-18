"""Load the inventory seed of CONTEXT-nexova (Hito 5) into Supabase.

6 assets, 7 entries and 4 exits, whose net stock is:
    NXV-IT-001 12 · NXV-IT-002 6 · NXV-PER-001 16 · NXV-PER-002 12 · NXV-OFF-001 38 · NXV-TRN-001 30

Idempotent: an asset is skipped if its `sku` exists; an order is skipped if one with the
same asset, quantity, supplier / exit type, assignee, office and fixed `created_at` exists.

`user_uuid` of the seeded orders is the id of a real TinyDB user: the one whose email is in
SEED_USER_EMAIL, or the first user of the users file otherwise. Emails are never printed.

Usage, from the repo root:
    uv run --project services/api python scripts/seed_inventory.py
"""

from __future__ import annotations

import os
import sys
from datetime import UTC, datetime

from sqlmodel import Session, select

from database import DatabaseFileError, UserRepository, create_db_and_tables, get_engine, users_db_path_from_env
from inventory_models import Asset, AssetEntry, AssetExit

ASSETS = [
    ("Portátil 14\" Business", "NXV-IT-001", "hardware", "Valencia"),
    ("Portátil 14\" Business", "NXV-IT-002", "hardware", "Miami"),
    ("Ratón ergonómico", "NXV-PER-001", "peripherals", "Valencia"),
    ("Hub USB-C", "NXV-PER-002", "peripherals", "Miami"),
    ("Resma de papel A4", "NXV-OFF-001", "office_supplies", "Valencia"),
    ("Cuaderno de formación en liderazgo", "NXV-TRN-001", "training_materials", "Valencia"),
]

# (sku, quantity, supplier, office, created_at)
ENTRIES = [
    ("NXV-IT-001", 10, "TechDistrib Valencia S.L.", "Valencia", datetime(2026, 9, 1, 9, 0, tzinfo=UTC)),
    ("NXV-IT-001", 5, "TechDistrib Valencia S.L.", "Valencia", datetime(2026, 9, 8, 9, 0, tzinfo=UTC)),
    ("NXV-IT-002", 8, "Office Depot Miami", "Miami", datetime(2026, 9, 2, 9, 0, tzinfo=UTC)),
    ("NXV-PER-001", 20, "TechDistrib Valencia S.L.", "Valencia", datetime(2026, 9, 3, 9, 0, tzinfo=UTC)),
    ("NXV-PER-002", 12, "Office Depot Miami", "Miami", datetime(2026, 9, 4, 9, 0, tzinfo=UTC)),
    ("NXV-OFF-001", 50, "Papelería Central Valencia S.L.", "Valencia", datetime(2026, 9, 5, 9, 0, tzinfo=UTC)),
    ("NXV-TRN-001", 30, "Ediciones Liderazgo S.L.", "Valencia", datetime(2026, 9, 6, 9, 0, tzinfo=UTC)),
]

# (sku, quantity, exit_type, assigned_to, office, created_at)
EXITS = [
    ("NXV-IT-001", 3, "allocation", "María López", "Valencia", datetime(2026, 9, 10, 9, 0, tzinfo=UTC)),
    ("NXV-IT-002", 2, "allocation", "John Smith", "Miami", datetime(2026, 9, 11, 9, 0, tzinfo=UTC)),
    ("NXV-PER-001", 4, "allocation", "Carlos Ruiz", "Valencia", datetime(2026, 9, 12, 9, 0, tzinfo=UTC)),
    ("NXV-OFF-001", 12, "consumption", None, "Valencia", datetime(2026, 9, 13, 9, 0, tzinfo=UTC)),
]


def seed_user_id() -> str:
    """Id of the TinyDB user that signs the seeded orders."""
    repository = UserRepository(users_db_path_from_env())
    try:
        users = repository.list_users()
    finally:
        repository.close()
    wanted = os.environ.get("SEED_USER_EMAIL", "").strip().lower()
    if wanted:
        users = [user for user in users if user.email.lower() == wanted]
    if not users:
        raise LookupError("no matching user in the users file; register one first or set SEED_USER_EMAIL")
    return users[0].id


def seed(session: Session, user_uuid: str) -> dict[str, int]:
    counts = {"assets": 0, "entries": 0, "exits": 0}
    ids: dict[str, int] = {}
    for name, sku, category, office in ASSETS:
        asset = session.exec(select(Asset).where(Asset.sku == sku)).first()
        if asset is None:
            asset = Asset(name=name, sku=sku, category=category, office=office)
            session.add(asset)
            session.flush()
            counts["assets"] += 1
        ids[sku] = asset.id

    for sku, quantity, supplier, office, created_at in ENTRIES:
        same = select(AssetEntry).where(
            AssetEntry.asset_id == ids[sku],
            AssetEntry.quantity == quantity,
            AssetEntry.supplier == supplier,
            AssetEntry.office == office,
            AssetEntry.created_at == created_at,
        )
        if session.exec(same).first() is None:
            session.add(AssetEntry(asset_id=ids[sku], quantity=quantity, supplier=supplier, office=office, created_at=created_at, user_uuid=user_uuid))
            counts["entries"] += 1

    for sku, quantity, exit_type, assigned_to, office, created_at in EXITS:
        same = select(AssetExit).where(
            AssetExit.asset_id == ids[sku],
            AssetExit.quantity == quantity,
            AssetExit.exit_type == exit_type,
            AssetExit.assigned_to == assigned_to if assigned_to is not None else AssetExit.assigned_to.is_(None),
            AssetExit.office == office,
            AssetExit.created_at == created_at,
        )
        if session.exec(same).first() is None:
            session.add(
                AssetExit(asset_id=ids[sku], quantity=quantity, exit_type=exit_type, assigned_to=assigned_to, office=office, created_at=created_at, user_uuid=user_uuid)
            )
            counts["exits"] += 1

    session.commit()
    return counts


def main() -> int:
    try:
        user_uuid = seed_user_id()
    except (LookupError, DatabaseFileError, OSError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    create_db_and_tables()
    with Session(get_engine()) as session:
        counts = seed(session, user_uuid)
    print(f"Inventory seed completed (orders signed by TinyDB user {user_uuid}): {counts['assets']} assets, {counts['entries']} entries, {counts['exits']} exits inserted.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

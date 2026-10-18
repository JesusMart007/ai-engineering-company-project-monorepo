"""scripts/seed_inventory.py: idempotent and netting to the stock of CONTEXT-nexova."""

import importlib.util
import sys
from pathlib import Path

from sqlmodel import Session

import database
import inventory_service

SCRIPT = Path(__file__).resolve().parents[3] / "scripts" / "seed_inventory.py"
spec = importlib.util.spec_from_file_location("seed_inventory", SCRIPT)
seed_inventory = importlib.util.module_from_spec(spec)
sys.modules["seed_inventory"] = seed_inventory
spec.loader.exec_module(seed_inventory)

EXPECTED_STOCK = {"NXV-IT-001": 12, "NXV-IT-002": 6, "NXV-PER-001": 16, "NXV-PER-002": 12, "NXV-OFF-001": 38, "NXV-TRN-001": 30}


def test_seed_is_idempotent_and_nets_to_the_expected_stock():
    database.create_db_and_tables()
    with Session(database.get_engine()) as session:
        first = seed_inventory.seed(session, "user-1")
        second = seed_inventory.seed(session, "user-2")
        stock = {asset.sku: asset.current_stock for asset in inventory_service.list_assets(session)}
    assert first == {"assets": 6, "entries": 7, "exits": 4}
    assert second == {"assets": 0, "entries": 0, "exits": 0}
    assert stock == EXPECTED_STOCK

"""Load the initial supplier directory into TinyDB.

Run with `uv run seed`. Safe to run repeatedly: suppliers whose `name` already
exists are skipped, so the directory is never duplicated.
"""

from __future__ import annotations

import sys

from models import SupplierCreate
from database import DatabaseFileError, SupplierRepository, db_path_from_env
from seed_data import SUPPLIERS_SEED


def seed(repository: SupplierRepository) -> tuple[int, int]:
    """Insert missing seed suppliers. Returns (inserted, skipped)."""
    inserted = skipped = 0
    for raw in SUPPLIERS_SEED:
        supplier = SupplierCreate.model_validate(raw)
        if repository.exists_name(supplier.name):
            skipped += 1
            continue
        repository.create(supplier)
        inserted += 1
    return inserted, skipped


def main() -> int:
    """CLI entry point (`uv run seed`): 0 on success, 1 if the database cannot be opened or written."""
    path = db_path_from_env()
    try:
        repository = SupplierRepository(path)
    except DatabaseFileError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    except OSError as error:
        print(f"Error: cannot open the database {path}: {error.strerror or error}", file=sys.stderr)
        return 1
    try:
        inserted, skipped = seed(repository)
    except OSError as error:
        print(f"Error: cannot write to the database {path}: {error.strerror or error}", file=sys.stderr)
        return 1
    finally:
        repository.close()
    print(f"Seed completed on {path}: {inserted} inserted, {skipped} skipped (already present).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

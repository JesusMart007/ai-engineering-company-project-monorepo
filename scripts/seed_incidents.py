"""Load the helpdesk CSV (incidents-file-analyzer) into the incident manager.

Each row is validated with the analyzer's rules (nexova_shared.csv_validation),
transformed with the mapping of CONTEXT-nexova-incident-manager.es.md
(nexova_shared.incidents) and inserted through the API's IncidentRepository.
Idempotent: rows whose ticket_id is already stored (as source_id) are skipped.

Usage, from the repo root:
    uv run --project services/api python scripts/seed_incidents.py [csv_path]

The target file is the API's (INCIDENTS_DB_PATH, default services/api/data/incidents.json).
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterable, Mapping

from database import IncidentRepository, SourceIdAlreadyExists, incidents_db_path_from_env
from incident_models import IncidentRecord
from nexova_shared.csv_validation import CsvFormatError, read_csv_rows
from nexova_shared.incidents import csv_row_to_incident

DEFAULT_CSV = Path(__file__).resolve().parent / "incidents-nexova.csv"
# Row 1 of the file is the header, so the first data row is row 2.
FIRST_DATA_ROW = 2


@dataclass
class SeedReport:
    inserted: int = 0
    skipped: int = 0
    invalid: list[tuple[int, list[str]]] = field(default_factory=list)


def seed_incidents(rows: Iterable[Mapping[str, str | None]], repository: IncidentRepository) -> SeedReport:
    report = SeedReport()
    for row_number, row in enumerate(rows, start=FIRST_DATA_ROW):
        incident, reasons = csv_row_to_incident(row)
        if incident is None:
            report.invalid.append((row_number, reasons))
            continue
        if repository.exists_source(incident.source_id):
            report.skipped += 1
            continue
        try:
            repository.create(IncidentRecord(**asdict(incident), updated_at=incident.created_at))
        except SourceIdAlreadyExists:
            report.skipped += 1
            continue
        report.inserted += 1
    return report


def print_report(report: SeedReport, source: Path, target: Path) -> None:
    print("=" * 60)
    print("  NEXOVA — SEED DE INCIDENCIAS")
    print(f"  CSV: {source}")
    print(f"  Base de datos: {target}")
    print("=" * 60)
    print(f"  Insertadas ......................... {report.inserted:>4}")
    print(f"  Ya existentes (saltadas) ........... {report.skipped:>4}")
    print(f"  Inválidas (descartadas) ............ {len(report.invalid):>4}")
    if report.invalid:
        print("\nFILAS INVÁLIDAS (fila 1 = encabezado)")
        for row_number, reasons in report.invalid:
            print(f"  Fila {row_number:>4}: {'; '.join(reasons)}")
    print("=" * 60)


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed the incident manager from the helpdesk CSV")
    parser.add_argument("csv_path", nargs="?", default=str(DEFAULT_CSV), help="Helpdesk CSV (default: scripts/incidents-nexova.csv)")
    args = parser.parse_args()
    source = Path(args.csv_path)
    try:
        rows = read_csv_rows(source.read_text(encoding="utf-8-sig"))
    except FileNotFoundError:
        print(f"Error: file not found: {source}", file=sys.stderr)
        return 1
    except UnicodeDecodeError:
        print("Error: the CSV must be UTF-8 encoded", file=sys.stderr)
        return 1
    except (OSError, CsvFormatError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    target = incidents_db_path_from_env()
    repository = IncidentRepository(target)
    try:
        report = seed_incidents(rows, repository)
    finally:
        repository.close()
    print_report(report, source, target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

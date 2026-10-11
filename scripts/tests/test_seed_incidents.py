"""Checks scripts/seed_incidents.py: CONTEXT totals, invalid-row report and idempotency.

Run with the API's environment: uv run --project services/api pytest scripts/tests
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

from database import IncidentRepository  # noqa: E402
from nexova_shared.csv_validation import read_csv_rows  # noqa: E402
from seed_incidents import seed_incidents  # noqa: E402

CSV_PATH = SCRIPTS / "incidents-nexova.csv"


@pytest.fixture()
def repository(tmp_path):
    repo = IncidentRepository(tmp_path / "incidents.json")
    yield repo
    repo.close()


def test_seed_matches_context_and_reports_invalid_rows(repository):
    report = seed_incidents(read_csv_rows(CSV_PATH.read_text(encoding="utf-8")), repository)
    assert (report.inserted, report.skipped) == (96, 0)
    assert [row for row, _ in report.invalid] == [18, 44, 87, 91]
    summary = repository.summary()
    assert {k.value: v for k, v in summary.by_status.items() if v} == {"open": 27, "resolved": 56, "discarded": 13}
    assert {k.value: v for k, v in summary.by_category.items() if v} == {
        "technical_failure": 49,
        "process_error": 35,
        "client_complaint": 12,
    }
    assert {k.value: v for k, v in summary.by_origin.items() if v} == {"customer": 96}
    assert {k.value: v for k, v in summary.by_branch.items() if v} == {"central": 96}


def test_seed_is_idempotent(repository):
    rows = read_csv_rows(CSV_PATH.read_text(encoding="utf-8"))
    seed_incidents(rows, repository)
    again = seed_incidents(rows, repository)
    assert (again.inserted, again.skipped, len(again.invalid)) == (0, 96, 4)
    assert repository.summary().total == 96


def test_seeded_incident_keeps_csv_date_and_ticket_id(repository):
    seed_incidents(read_csv_rows(CSV_PATH.read_text(encoding="utf-8")), repository)
    incident = next(i for i in repository.list() if i.source_id == "NXV-000001")
    assert incident.created_at == incident.updated_at
    assert incident.created_at.isoformat() == "2024-01-18T00:00:00+00:00"


def test_cli_prints_summary_without_emails(tmp_path):
    env = {**os.environ, "INCIDENTS_DB_PATH": str(tmp_path / "incidents.json")}
    run = [sys.executable, str(SCRIPTS / "seed_incidents.py")]
    first = subprocess.run(run, capture_output=True, text=True, env=env, check=True)
    second = subprocess.run(run, capture_output=True, text=True, env=env, check=True)
    assert "Insertadas .........................   96" in first.stdout
    assert "Ya existentes (saltadas) ...........   96" in second.stdout
    assert "Fila   87: Invalid or missing email" in first.stdout
    assert "@" not in first.stdout + first.stderr


def _run_seed(tmp_path, *args: str, db: Path | None = None) -> subprocess.CompletedProcess:
    env = {**os.environ, "INCIDENTS_DB_PATH": str(db or tmp_path / "incidents.json")}
    return subprocess.run([sys.executable, str(SCRIPTS / "seed_incidents.py"), *args], capture_output=True, text=True, env=env)


@pytest.mark.parametrize(
    ("content", "message"),
    [
        (None, "file not found"),
        ("", "The CSV file is empty"),
        ("id,name\n1,x\n", "missing required columns"),
    ],
)
def test_cli_critical_input_errors_exit_1_with_a_message(tmp_path, content, message):
    csv_path = tmp_path / "input.csv"
    if content is not None:
        csv_path.write_text(content, encoding="utf-8")
    completed = _run_seed(tmp_path, str(csv_path))
    assert completed.returncode == 1
    assert message in completed.stderr
    assert "Traceback" not in completed.stderr
    assert not (tmp_path / "incidents.json").exists()


def test_cli_corrupt_database_exits_1_without_traceback(tmp_path):
    db = tmp_path / "incidents.json"
    db.write_text("{corrupt", encoding="utf-8")
    completed = _run_seed(tmp_path, db=db)
    assert completed.returncode == 1
    assert "incidents.json is not valid JSON" in completed.stderr
    assert "Traceback" not in completed.stderr

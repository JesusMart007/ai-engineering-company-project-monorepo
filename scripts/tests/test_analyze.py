"""Checks the analyzer CLI (scripts/analyze.py) against CONTEXT-nexova.es.md.

Run with the API's environment, which installs nexova_shared:
    uv run --project services/api pytest scripts/tests
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
CSV_PATH = SCRIPTS / "incidents-nexova.csv"


def test_cli_prints_report_exports_and_never_leaks_emails(tmp_path):
    completed = subprocess.run(
        [sys.executable, str(SCRIPTS / "analyze.py"), str(CSV_PATH)],
        input="s\n",
        capture_output=True,
        text=True,
        cwd=tmp_path,
        check=True,
    )
    assert "Average score: 3.84 / 5.00" in completed.stdout
    assert "¿Deseas exportar los resultados a CSV? [s/n]" in completed.stdout
    exported = (tmp_path / "results.csv").read_text(encoding="utf-8").splitlines()
    assert exported[0] == "metric,value,description"
    assert "total_records,100,Records in file" in exported
    assert "average_score,3.84,Average satisfaction score of closed tickets (1-5)" in exported
    assert "@" not in completed.stdout + completed.stderr + "\n".join(exported)


def test_cli_reports_missing_file(tmp_path):
    completed = subprocess.run(
        [sys.executable, str(SCRIPTS / "analyze.py"), "nope.csv"], capture_output=True, text=True, cwd=tmp_path
    )
    assert completed.returncode == 1
    assert "file not found" in completed.stderr

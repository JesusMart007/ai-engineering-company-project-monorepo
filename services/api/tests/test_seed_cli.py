"""`uv run seed` (seed.main): exit codes and messages."""

from __future__ import annotations

import seed
from database import DB_PATH_ENV


def test_seed_cli_succeeds_and_is_idempotent(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv(DB_PATH_ENV, str(tmp_path / "suppliers.json"))
    assert seed.main() == 0
    assert seed.main() == 0
    assert "0 inserted, 15 skipped" in capsys.readouterr().out


def test_seed_cli_corrupt_database_exits_1(tmp_path, monkeypatch, capsys):
    db = tmp_path / "suppliers.json"
    db.write_text("{corrupt", encoding="utf-8")
    monkeypatch.setenv(DB_PATH_ENV, str(db))
    assert seed.main() == 1
    assert "suppliers.json is not valid JSON" in capsys.readouterr().err

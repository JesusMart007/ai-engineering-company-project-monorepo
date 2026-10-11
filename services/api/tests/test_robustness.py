"""Defensive checks: corrupt TinyDB files, malformed password hashes, bad settings, unparseable CSVs."""

from __future__ import annotations

import pytest

import config
import security
from conftest import PASSWORD, register
from database import DatabaseFileError, IncidentRepository, SupplierRepository, UserRepository, open_db


@pytest.mark.parametrize("repository", [SupplierRepository, UserRepository, IncidentRepository])
def test_corrupt_database_file_fails_with_its_name(tmp_path, repository):
    path = tmp_path / "broken.json"
    path.write_text("{not json", encoding="utf-8")
    with pytest.raises(DatabaseFileError, match="broken.json is not valid JSON"):
        repository(path)


def test_missing_database_file_is_created_empty(tmp_path):
    db = open_db(tmp_path / "new" / "db.json")
    assert db.tables() == set()
    db.close()


def test_malformed_stored_hash_fails_the_check_instead_of_raising(caplog):
    assert security.verify_password("anything", "not-a-bcrypt-hash") is False
    assert "not a valid bcrypt hash" in caplog.text
    assert "not-a-bcrypt-hash" not in caplog.text


def test_login_with_a_corrupted_hash_is_401_not_500(anon_client):
    user = register(anon_client, "corrupt@nexova.example")
    anon_client.app.state.user_repository.update_user(user["id"], {"hashed_password": "garbage"})
    response = anon_client.post("/auth/login", data={"username": "corrupt@nexova.example", "password": PASSWORD})
    assert response.status_code == 401


@pytest.mark.parametrize("value", ["abc", "0", "-5", "1.5"])
def test_minutes_settings_must_be_positive_integers(value):
    with pytest.raises(RuntimeError, match="ACCESS_TOKEN_EXPIRE_MINUTES must be a positive whole number"):
        config._positive_int("ACCESS_TOKEN_EXPIRE_MINUTES", value)


def test_unparseable_csv_gives_a_fixed_message(auth_client):
    header = "ticket_id,date,client_company,category,description,agent_id,status,customer_email,satisfaction_score\n"
    huge_field = '"' + "x" * 200_000 + '"'
    content = (header + f"NXV-000001,2024-01-01,Acme,BILLING,{huge_field},AGT-01,OPEN,a@b.com,\n").encode()
    response = auth_client.post("/api/incidents/analyze", files={"file": ("incidents.csv", content, "text/csv")})
    assert response.status_code == 422
    assert response.json() == {"detail": "The file is not a valid CSV"}

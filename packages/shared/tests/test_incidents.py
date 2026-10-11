"""Checks the incident manager's enums, lifecycle and CSV mapping against
CONTEXT-nexova-incident-manager.es.md."""

from __future__ import annotations

import csv
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

import pytest

from nexova_shared.incidents import (
    STATUS_TRANSITIONS,
    Branch,
    IncidentCategory,
    IncidentOrigin,
    IncidentStatus,
    can_transition,
    csv_row_to_incident,
)

CSV_PATH = Path(__file__).resolve().parents[3] / "scripts" / "incidents-nexova.csv"
ROW = {
    "ticket_id": "NXV-000123",
    "date": "2024-01-18",
    "client_company": "Acme",
    "category": "ACCESS",
    "description": "Role permissions not updated after department change",
    "agent_id": "AGT-08",
    "status": "CLOSED",
    "customer_email": "someone@example.com",
    "satisfaction_score": "5",
}


def test_allowed_values_match_context():
    assert [s.value for s in IncidentStatus] == ["open", "in_progress", "resolved", "discarded"]
    assert [o.value for o in IncidentOrigin] == ["customer", "branch", "internal"]
    assert [b.value for b in Branch] == ["central", "valencia_operations", "miami_office", "remote"]
    assert [c.value for c in IncidentCategory] == [
        "technical_failure",
        "process_error",
        "client_complaint",
        "candidate_issue",
        "staff_issue",
        "sla_breach",
        "data_quality",
        "other",
    ]


VALID = {("open", "in_progress"), ("open", "discarded"), ("in_progress", "resolved"), ("in_progress", "discarded")}


@pytest.mark.parametrize("current", list(IncidentStatus))
@pytest.mark.parametrize("new", list(IncidentStatus))
def test_only_context_transitions_are_allowed(current, new):
    assert can_transition(current, new) == ((current.value, new.value) in VALID)


def test_resolved_and_discarded_are_final():
    assert STATUS_TRANSITIONS[IncidentStatus.RESOLVED] == ()
    assert STATUS_TRANSITIONS[IncidentStatus.DISCARDED] == ()


def test_valid_row_is_transformed():
    incident, reasons = csv_row_to_incident(ROW)
    assert reasons == []
    assert incident.source_id == "NXV-000123"
    assert incident.title == incident.description == ROW["description"]
    assert incident.category is IncidentCategory.TECHNICAL_FAILURE
    assert incident.status is IncidentStatus.RESOLVED
    assert incident.origin is IncidentOrigin.CUSTOMER
    assert incident.branch is Branch.CENTRAL
    assert incident.created_at == datetime(2024, 1, 18, tzinfo=UTC)


def test_title_is_first_120_characters_trimmed():
    description = "  " + "x" * 119 + " " + "tail"
    incident, _ = csv_row_to_incident({**ROW, "description": description})
    assert incident.title == "x" * 119
    assert incident.description == description


def test_invalid_row_reports_rules_but_never_values():
    incident, reasons = csv_row_to_incident({**ROW, "customer_email": "no-at-sign", "client_company": ""})
    assert incident is None
    assert reasons == ["Missing client_company", "Invalid or missing email"]
    assert not any("no-at-sign" in reason for reason in reasons)


def test_whole_csv_matches_context_totals():
    with CSV_PATH.open(encoding="utf-8", newline="") as source:
        results = [csv_row_to_incident(row) for row in csv.DictReader(source)]
    incidents = [incident for incident, _ in results if incident]
    assert (len(incidents), len(results) - len(incidents)) == (96, 4)
    assert Counter(i.status.value for i in incidents) == {"open": 27, "resolved": 56, "discarded": 13}
    assert Counter(i.category.value for i in incidents) == {
        "technical_failure": 49,
        "process_error": 35,
        "client_complaint": 12,
    }
    assert len({i.source_id for i in incidents}) == 96

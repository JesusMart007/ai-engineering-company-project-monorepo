"""Allowed values, lifecycle and CSV mapping of the centralized incident manager.

Every value comes from CONTEXT-nexova-incident-manager.es.md (Gestor de Incidencias
Centralizado · Nexova). This is the only place they are defined: the API models, the seed script
and the tests import them from here.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from enum import StrEnum
from typing import Mapping

from nexova_shared.csv_validation import RULE_LABELS, find_issues


class IncidentStatus(StrEnum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    DISCARDED = "discarded"


class IncidentCategory(StrEnum):
    TECHNICAL_FAILURE = "technical_failure"
    PROCESS_ERROR = "process_error"
    CLIENT_COMPLAINT = "client_complaint"
    CANDIDATE_ISSUE = "candidate_issue"
    STAFF_ISSUE = "staff_issue"
    SLA_BREACH = "sla_breach"
    DATA_QUALITY = "data_quality"
    OTHER = "other"


class IncidentOrigin(StrEnum):
    CUSTOMER = "customer"
    BRANCH = "branch"
    INTERNAL = "internal"


class Branch(StrEnum):
    # `central` is Nexova's head office in Valencia; also used when no office applies.
    CENTRAL = "central"
    VALENCIA_OPERATIONS = "valencia_operations"
    MIAMI_OFFICE = "miami_office"
    REMOTE = "remote"


# resolved and discarded are final: they have no outgoing transitions.
STATUS_TRANSITIONS: dict[IncidentStatus, tuple[IncidentStatus, ...]] = {
    IncidentStatus.OPEN: (IncidentStatus.IN_PROGRESS, IncidentStatus.DISCARDED),
    IncidentStatus.IN_PROGRESS: (IncidentStatus.RESOLVED, IncidentStatus.DISCARDED),
    IncidentStatus.RESOLVED: (),
    IncidentStatus.DISCARDED: (),
}


def can_transition(current: IncidentStatus, new: IncidentStatus) -> bool:
    return new in STATUS_TRANSITIONS[current]


# --- CSV (incidents-file-analyzer) -> incident model -------------------------

CSV_STATUS_MAP: dict[str, IncidentStatus] = {
    "OPEN": IncidentStatus.OPEN,
    "CLOSED": IncidentStatus.RESOLVED,
    "DISCARDED": IncidentStatus.DISCARDED,
}
CSV_CATEGORY_MAP: dict[str, IncidentCategory] = {
    "TECHNICAL": IncidentCategory.TECHNICAL_FAILURE,
    "BILLING": IncidentCategory.PROCESS_ERROR,
    "ACCESS": IncidentCategory.TECHNICAL_FAILURE,
    "HR_QUERY": IncidentCategory.PROCESS_ERROR,
    "COMPLAINT": IncidentCategory.CLIENT_COMPLAINT,
}
# Every CSV row is a complaint from a corporate client with no office of its own.
CSV_ORIGIN = IncidentOrigin.CUSTOMER
CSV_BRANCH = Branch.CENTRAL
TITLE_MAX_LENGTH = 120


@dataclass(frozen=True)
class CsvIncident:
    """A CSV row already validated and transformed into the incident model's values."""

    source_id: str
    title: str
    description: str
    category: IncidentCategory
    status: IncidentStatus
    origin: IncidentOrigin
    branch: Branch
    created_at: datetime


def csv_row_to_incident(row: Mapping[str, str | None]) -> tuple[CsvIncident | None, list[str]]:
    """Validate a CSV row with the analyzer's rules and map it to the incident model.

    Returns (incident, []) for a usable row, or (None, reasons) otherwise. Reasons
    only name rules and fields, never values, so customer emails cannot leak.
    """
    issues = find_issues(row)
    if issues:
        return None, list(dict.fromkeys(RULE_LABELS[issue.rule] for issue in issues))

    def text(field: str) -> str:
        return (row.get(field) or "").strip()

    reasons = []
    status = CSV_STATUS_MAP.get(text("status"))
    category = CSV_CATEGORY_MAP.get(text("category"))
    title = text("description")[:TITLE_MAX_LENGTH].strip()
    if status is None:
        reasons.append("Status without a mapping to the incident model")
    if category is None:
        reasons.append("Category without a mapping to the incident model")
    if not title:
        reasons.append("Empty title after trimming description")
    if reasons:
        return None, reasons

    created_at = datetime.combine(date.fromisoformat(text("date")), datetime.min.time(), tzinfo=UTC)
    return (
        CsvIncident(
            source_id=text("ticket_id"),
            title=title,
            description=row.get("description") or "",
            category=category,
            status=status,
            origin=CSV_ORIGIN,
            branch=CSV_BRANCH,
            created_at=created_at,
        ),
        [],
    )

"""Pydantic models for the centralized incident manager.

Allowed values (status, category, origin, branch) and the status lifecycle come
from nexova_shared.incidents, the single place they are defined. TinyDB has no
NOT NULL or CHECK constraints, so integrity is enforced here: every document is
built through IncidentRecord before IncidentRepository writes it.
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, StringConstraints, computed_field

from nexova_shared.incidents import (
    STATUS_TRANSITIONS,
    TITLE_MAX_LENGTH,
    Branch,
    IncidentCategory,
    IncidentOrigin,
    IncidentStatus,
)

NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
Title = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=TITLE_MAX_LENGTH)]


class IncidentCreate(BaseModel):
    """Payload of POST /api/incidents. A new incident always starts as `open`."""

    model_config = ConfigDict(extra="forbid")

    title: Title
    description: NonEmptyStr
    category: IncidentCategory
    origin: IncidentOrigin
    branch: Branch
    status: Literal[IncidentStatus.OPEN] = IncidentStatus.OPEN


class IncidentRecord(BaseModel):
    """An incident as stored. `source_id` is the CSV `ticket_id` (seed only), unique when set."""

    title: Title
    description: NonEmptyStr
    category: IncidentCategory
    status: IncidentStatus = IncidentStatus.OPEN
    origin: IncidentOrigin
    branch: Branch
    source_id: NonEmptyStr | None = None
    created_at: AwareDatetime
    updated_at: AwareDatetime


class Incident(IncidentRecord):
    id: int

    @computed_field
    @property
    def next_statuses(self) -> list[IncidentStatus]:
        """Statuses this incident can move to; empty for final states."""
        return list(STATUS_TRANSITIONS[self.status])


class StatusUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: IncidentStatus


class IncidentSummary(BaseModel):
    """Totals per allowed value; every value is present, even at zero."""

    total: int
    by_status: dict[IncidentStatus, int]
    by_category: dict[IncidentCategory, int]
    by_origin: dict[IncidentOrigin, int]
    by_branch: dict[Branch, int]

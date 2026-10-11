"""Error responses of the incident manager routes (routes/incident_manager.py).

IncidentRoute is used as the route_class of that router only, so:
- validation errors become 400 {"detail", "errors": [{"field", "message"}]} with
  messages in plain Spanish, instead of FastAPI's 422;
- unexpected exceptions become the app-wide generic 500 (errors.py), logged
  in full on the server.
Every other router (users, auth, suppliers, CSV analysis) keeps FastAPI's 422
format, which the backoffice sign-up form relies on.
"""

from __future__ import annotations

from collections.abc import Callable, Coroutine
from enum import StrEnum
from typing import Any

from fastapi import Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from starlette.exceptions import HTTPException

from errors import unexpected_error_response
from nexova_shared.incidents import Branch, IncidentCategory, IncidentOrigin, IncidentStatus

VALIDATION_DETAIL = "Datos no válidos"

# Field -> (subject with its article, adjective ending for gender agreement).
FIELDS: dict[str, tuple[str, str]] = {
    "title": ("El título", "o"),
    "description": ("La descripción", "a"),
    "category": ("La categoría", "a"),
    "origin": ("El origen", "o"),
    "branch": ("La sede", "a"),
    "status": ("El estado", "o"),
    "incident_id": ("El identificador de la incidencia", "o"),
}
ENUMS: dict[str, type[StrEnum]] = {
    "category": IncidentCategory,
    "origin": IncidentOrigin,
    "branch": Branch,
    "status": IncidentStatus,
}
REQUIRED_TYPES = {"missing", "string_too_short"}


def _field(error: dict[str, Any]) -> str:
    # loc is ("body", "title"), ("query", "status"), ("path", "incident_id")... A
    # malformed JSON body gives ("body", <character position>).
    if error.get("type") == "json_invalid":
        return "body"
    parts = [part for part in error.get("loc", ()) if isinstance(part, str) and part not in ("body", "query", "path")]
    return parts[0] if parts else "body"


def _message(field: str, error: dict[str, Any]) -> str:
    kind = error.get("type", "")
    if field == "body":
        if kind == "json_invalid":
            return "El cuerpo de la petición no es un JSON válido"
        return "Faltan los datos de la incidencia o no tienen el formato esperado"
    if kind == "extra_forbidden":
        return f"El campo «{field}» no está permitido"
    subject, ending = FIELDS.get(field, (f"El campo «{field}»", "o"))
    if kind in REQUIRED_TYPES or error.get("input") in (None, ""):
        return f"{subject} es obligatori{ending}"
    if kind == "string_too_long":
        return f"{subject} no puede superar {error.get('ctx', {}).get('max_length')} caracteres"
    if kind == "literal_error" and field == "status":
        return "Una incidencia nueva siempre se registra en estado «open»"
    if kind == "string_type":
        return f"{subject} debe ser un texto"
    if kind == "int_parsing":
        return f"{subject} debe ser un número entero"
    if field in ENUMS:
        allowed = ", ".join(value.value for value in ENUMS[field])
        return f"{subject} no es válid{ending}. Valores permitidos: {allowed}"
    return f"{subject} no es válid{ending}"


def validation_errors(errors: list[dict[str, Any]]) -> list[dict[str, str]]:
    result = []
    for error in errors:
        field = _field(error)
        result.append({"field": field, "message": _message(field, error)})
    return result


class IncidentRoute(APIRoute):
    def get_route_handler(self) -> Callable[[Request], Coroutine[Any, Any, Response]]:
        handler = super().get_route_handler()

        async def handle(request: Request) -> Response:
            try:
                return await handler(request)
            except RequestValidationError as error:
                content = {"detail": VALIDATION_DETAIL, "errors": validation_errors(list(error.errors()))}
                return JSONResponse(status_code=400, content=content)
            except HTTPException:
                raise
            except Exception:
                return unexpected_error_response(request)

        return handle

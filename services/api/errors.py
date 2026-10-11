"""App-wide error responses.

- Unexpected exceptions: 500 {"detail": "Ha ocurrido un error inesperado"}. The
  traceback goes only to the server log, never to the client.
- Validation errors: FastAPI's 422 {"detail": [{loc, msg, type, ctx}]}, minus
  `input`, which echoed what the client sent (passwords, reset tokens, emails).
  The backoffice maps these by `loc`, so the format is otherwise unchanged.

The incident manager routes answer validation errors with their own 400 format
(incident_errors.IncidentRoute) and reuse unexpected_error_response for the 500.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

UNEXPECTED_DETAIL = "Ha ocurrido un error inesperado"


def unexpected_error_response(request: Request) -> JSONResponse:
    """Log the exception being handled (with traceback) and return a generic 500."""
    logger.exception("Unexpected error in %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": UNEXPECTED_DETAIL})


async def _unexpected_error(request: Request, _: Exception) -> JSONResponse:
    return unexpected_error_response(request)


async def _validation_error(_: Request, error: RequestValidationError) -> JSONResponse:
    issues = [{key: value for key, value in issue.items() if key != "input"} for issue in error.errors()]
    return JSONResponse(status_code=422, content={"detail": jsonable_encoder(issues)})


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(RequestValidationError, _validation_error)
    app.add_exception_handler(Exception, _unexpected_error)

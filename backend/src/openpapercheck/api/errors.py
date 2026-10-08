"""
RFC 7807 / RFC 9457 Problem Details Error Handlers for OpenPaperCheck API.
Ensures every API error returns consistent, machine-readable JSON:
{
  "type": "https://openpapercheck.org/problems/...",
  "title": "...",
  "status": 404,
  "detail": "...",
  "instance": "/v1/check/..."
}
"""

from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

PROBLEM_JSON_CONTENT_TYPE = "application/problem+json"


class APIProblemError(Exception):
    """Base exception for all domain problem errors."""

    def __init__(
        self,
        status_code: int,
        title: str,
        detail: str,
        problem_type: str = "about:blank",
    ):
        super().__init__(detail)
        self.status_code = status_code
        self.title = title
        self.detail = detail
        self.problem_type = problem_type


APIProblemException = APIProblemError


class InvalidDoiError(APIProblemError):
    def __init__(self, doi: str, detail: str | None = None):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            title="Invalid DOI Syntax",
            detail=detail
            or f"'{doi}' is not a valid DOI format. Standard DOIs begin with '10.' followed by registrant code.",
            problem_type="https://openpapercheck.org/problems/invalid-doi",
        )


class DoiNotFoundError(APIProblemException):
    def __init__(self, doi: str, detail: str | None = None):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            title="DOI Not Found",
            detail=detail
            or f"DOI '{doi}' was not found in Crossref or upstream scholarly registries.",
            problem_type="https://openpapercheck.org/problems/doi-not-found",
        )


class PaperHiddenError(APIProblemException):
    def __init__(self, doi: str, reason: str | None = None):
        super().__init__(
            status_code=status.HTTP_451_UNAVAILABLE_FOR_LEGAL_REASONS,
            title="Paper Report Hidden by Moderator",
            detail=f"This paper report has been hidden from public display: {reason or 'Administrative moderation'}",
            problem_type="https://openpapercheck.org/problems/paper-hidden",
        )


class UpstreamServiceError(APIProblemException):
    def __init__(self, service: str, detail: str | None = None):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            title="Upstream Service Unavailable",
            detail=detail or f"Failed to connect to upstream service: {service}.",
            problem_type="https://openpapercheck.org/problems/upstream-service-error",
        )


def register_error_handlers(app: FastAPI) -> None:
    """Register RFC 9457 problem+json error handlers on FastAPI application."""

    @app.exception_handler(APIProblemError)
    async def problem_exception_handler(request: Request, exc: APIProblemError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            media_type=PROBLEM_JSON_CONTENT_TYPE,
            content={
                "type": exc.problem_type,
                "title": exc.title,
                "status": exc.status_code,
                "detail": exc.detail,
                "instance": request.url.path,
            },
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        title = "HTTP Error"
        if exc.status_code == status.HTTP_404_NOT_FOUND:
            title = "Resource Not Found"
        elif exc.status_code == status.HTTP_405_METHOD_NOT_ALLOWED:
            title = "Method Not Allowed"

        return JSONResponse(
            status_code=exc.status_code,
            media_type=PROBLEM_JSON_CONTENT_TYPE,
            content={
                "type": "about:blank",
                "title": title,
                "status": exc.status_code,
                "detail": str(exc.detail),
                "instance": request.url.path,
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        errors = exc.errors()
        error_details = "; ".join(f"{e.get('loc', [''])[-1]}: {e.get('msg', '')}" for e in errors)
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            media_type=PROBLEM_JSON_CONTENT_TYPE,
            content={
                "type": "https://openpapercheck.org/problems/validation-error",
                "title": "Unprocessable Request Content",
                "status": status.HTTP_422_UNPROCESSABLE_ENTITY,
                "detail": error_details or "Request validation failed.",
                "instance": request.url.path,
            },
        )

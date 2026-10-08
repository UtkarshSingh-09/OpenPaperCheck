"""
Health and Monitoring Endpoints for OpenPaperCheck REST API (v1).
Provides GET /v1/health
"""

from __future__ import annotations

from fastapi import APIRouter

from openpapercheck import __version__
from openpapercheck.api.schemas import HealthResponse
from openpapercheck.core.storage import get_manifest, has_snapshot

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Service Health Check",
    description="Returns service status, database snapshot info, and record counts for uptime monitoring.",
)
async def get_health() -> HealthResponse:
    manifest = get_manifest() or {}
    db_status = "ok" if has_snapshot() else "no_local_snapshot"

    return HealthResponse(
        status="ok",
        version=__version__,
        db=db_status,
        as_of=manifest.get("as_of", "none"),
        records_count=manifest.get("rows_count"),
        is_sample=manifest.get("is_sample", False),
    )

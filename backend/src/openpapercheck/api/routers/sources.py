"""
Data Sources Transparency Endpoints for OpenPaperCheck REST API (v1).
Provides GET /v1/sources
"""

from __future__ import annotations

from fastapi import APIRouter

from openpapercheck.core.storage import get_manifest
from openpapercheck.api.schemas import SourceMetadata, SourcesResponse

router = APIRouter(tags=["Transparency"])


@router.get(
    "/sources",
    response_model=SourcesResponse,
    summary="List Scholarly Data Sources",
    description="Returns data authorities, licenses, freshness dates, and record counts for transparency.",
)
async def get_sources() -> SourcesResponse:
    manifest = get_manifest() or {}
    rw_as_of = manifest.get("as_of", "not downloaded")
    rw_count = manifest.get("rows_count")

    sources = [
        SourceMetadata(
            name="Retraction Watch Database",
            authority="Center for Scientific Integrity / Crossref",
            license="Open Data (CC0 / Public Domain Retraction Metadata)",
            records_count=rw_count,
            as_of_date=rw_as_of,
            description="Comprehensive database of academic retractions, expressions of concern, and corrections.",
        ),
        SourceMetadata(
            name="Crossref Works API",
            authority="Crossref (crossref.org)",
            license="Open Citation Data",
            records_count=None,
            as_of_date="live query",
            description="Official DOI registration agency for scholarly publishing; provides deposited citation metadata.",
        ),
        SourceMetadata(
            name="OpenAlex",
            authority="OurResearch (openalex.org)",
            license="CC0 1.0 Universal",
            records_count=None,
            as_of_date="live query",
            description="Open and comprehensive catalog of scholarly papers, authors, and venues.",
        ),
    ]

    return SourcesResponse(sources=sources)

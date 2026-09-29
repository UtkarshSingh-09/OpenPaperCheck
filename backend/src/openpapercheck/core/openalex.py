"""
OpenAlex REST API Client (Optional Fallback).

Queries OpenAlex for scholarly work metadata, publication dates, and retraction indicators.
Strictly adheres to OpenPaperCheck fairness non-negotiables: zero personal/author/institution features.
"""

from __future__ import annotations

import os
from typing import Any

import httpx

from openpapercheck import __version__
from openpapercheck.core.doi import normalize_doi

DEFAULT_TIMEOUT = 10.0
BASE_URL = "https://api.openalex.org/works"


class OpenAlexClient:
    """Client for retrieving work metadata from OpenAlex API."""

    def __init__(
        self,
        api_key: str | None = None,
        mailto: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        self.api_key = api_key or os.environ.get("OPENALEX_API_KEY")
        self.mailto = (
            mailto or os.environ.get("CROSSREF_MAILTO") or "openpapercheck-dev@example.org"
        )
        self.timeout = timeout
        self.headers: dict[str, str] = {
            "User-Agent": (
                f"OpenPaperCheck/{__version__} "
                f"(https://github.com/UtkarshSingh-09/OpenPaperCheck; mailto:{self.mailto})"
            )
        }
        if self.api_key:
            self.headers["api-key"] = self.api_key

    def get_work(self, doi: str) -> dict[str, Any] | None:
        """
        Fetch work metadata for a normalized DOI from OpenAlex.

        Returns:
            Dict containing title, publication_year, is_retracted, and referenced_work_count,
            or None if not found or on error.
        """
        canonical = normalize_doi(doi)
        if not canonical:
            return None

        # OpenAlex requires URL-encoded canonical DOI format
        url = f"{BASE_URL}/https://doi.org/{canonical}"

        try:
            with httpx.Client(
                timeout=self.timeout,
                headers=self.headers,
                follow_redirects=True,
            ) as client:
                resp = client.get(url)
                if resp.status_code == 404:
                    return None
                resp.raise_for_status()
                data = resp.json()

            return {
                "doi": canonical,
                "title": data.get("title") or "Unknown Title",
                "publication_year": data.get("publication_year"),
                "publication_date": data.get("publication_date"),
                "is_retracted": bool(data.get("is_retracted", False)),
                "referenced_works_count": len(data.get("referenced_works", [])),
                "openalex_id": data.get("id"),
            }
        except Exception:
            # Graceful fallback: return None on network/auth/parse failure
            return None

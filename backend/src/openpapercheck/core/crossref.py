"""
Crossref REST API Client with Polite Pool support and 3-Tier Reference Parsing.
"""

from __future__ import annotations

import os
from typing import Any

import httpx

from openpapercheck import __version__
from openpapercheck.core.doi import normalize_doi

DEFAULT_TIMEOUT = 10.0
BASE_URL = "https://api.crossref.org/works"


class CrossrefClient:
    """Client for retrieving metadata and reference lists from the Crossref REST API."""

    def __init__(self, mailto: str | None = None, timeout: float = DEFAULT_TIMEOUT):
        self.mailto = (
            mailto or os.environ.get("CROSSREF_MAILTO") or "openpapercheck-dev@example.org"
        )
        self.timeout = timeout
        self.headers = {
            "User-Agent": (
                f"OpenPaperCheck/{__version__} "
                f"(https://github.com/openpapercheck/openpapercheck; mailto:{self.mailto})"
            )
        }

    def get_work(self, doi: str) -> dict[str, Any] | None:
        """
        Fetch work metadata and references for a normalized DOI.

        Returns:
            Dict containing title, journal, publisher, publication_date, and references,
            or None if the DOI was not found (HTTP 404).
        """
        canonical = normalize_doi(doi)
        if not canonical:
            return None

        url = f"{BASE_URL}/{canonical}"
        params = {"mailto": self.mailto}

        with httpx.Client(
            timeout=self.timeout, headers=self.headers, follow_redirects=True
        ) as client:
            response = client.get(url, params=params)
            if response.status_code == 404:
                return None
            response.raise_for_status()
            data = response.json()

        message = data.get("message", {})
        return self._parse_work_message(canonical, message)

    def _parse_work_message(self, doi: str, message: dict[str, Any]) -> dict[str, Any]:
        """Parse raw Crossref message into normalized structure."""
        title_list = message.get("title", [])
        title = title_list[0] if title_list else "Unknown Title"

        container = message.get("container-title", [])
        journal = container[0] if container else message.get("publisher", "Unknown Journal")
        publisher = message.get("publisher", "Unknown Publisher")

        # Parse publication date
        pub_date = None
        pub_year = None
        for date_key in ("published-print", "published-online", "published", "created"):
            parts = message.get(date_key, {}).get("date-parts", [])
            if parts and parts[0]:
                year = parts[0][0]
                month = parts[0][1] if len(parts[0]) > 1 else 1
                day = parts[0][2] if len(parts[0]) > 2 else 1
                pub_year = year
                pub_date = f"{year:04d}-{month:02d}-{day:02d}"
                break

        # Parse reference list with 3-tier honesty rule
        raw_references = message.get("reference", [])
        ref_count_header = message.get("references-count", 0)

        with_doi: list[dict[str, Any]] = []
        without_doi: list[dict[str, Any]] = []

        if raw_references:
            deposit_status = "deposited"
            for pos, ref in enumerate(raw_references, start=1):
                raw_ref_doi = ref.get("DOI")
                clean_ref_doi = normalize_doi(raw_ref_doi) if raw_ref_doi else None
                unstructured = (
                    ref.get("unstructured") or ref.get("article-title") or "Unstructured citation"
                )

                if clean_ref_doi:
                    with_doi.append(
                        {
                            "position": pos,
                            "doi": clean_ref_doi,
                            "year": ref.get("year"),
                            "raw": unstructured,
                        }
                    )
                else:
                    without_doi.append(
                        {
                            "position": pos,
                            "raw": unstructured,
                            "year": ref.get("year"),
                        }
                    )
        elif ref_count_header > 0:
            # The publisher declared references exist, but restricted open deposit in Crossref
            deposit_status = "restricted"
        else:
            deposit_status = "missing"

        return {
            "doi": doi,
            "title": title,
            "journal": journal,
            "publisher": publisher,
            "publication_date": pub_date,
            "publication_year": pub_year,
            "references": {
                "deposit_status": deposit_status,
                "total_listed": len(raw_references) if raw_references else ref_count_header,
                "with_doi": with_doi,
                "without_doi": without_doi,
            },
        }

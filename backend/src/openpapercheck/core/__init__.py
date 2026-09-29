"""
Core modules for OpenPaperCheck (zero PostgreSQL/FastAPI dependencies).
"""

from openpapercheck.core.crossref import CrossrefClient
from openpapercheck.core.doi import normalize_doi
from openpapercheck.core.models import (
    CitationTiming,
    PaperPublicState,
    determine_paper_state,
    evaluate_citation_timing,
)
from openpapercheck.core.openalex import OpenAlexClient
from openpapercheck.core.storage import check_reference_dois, get_retraction

__all__ = [
    "CitationTiming",
    "CrossrefClient",
    "OpenAlexClient",
    "PaperPublicState",
    "check_reference_dois",
    "determine_paper_state",
    "evaluate_citation_timing",
    "get_retraction",
    "normalize_doi",
]

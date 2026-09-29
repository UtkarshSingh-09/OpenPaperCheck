"""
Core modules for OpenPaperCheck (zero PostgreSQL/FastAPI dependencies).
"""

from openpapercheck.core.crossref import CrossrefClient
from openpapercheck.core.doi import normalize_doi
from openpapercheck.core.openalex import OpenAlexClient
from openpapercheck.core.storage import check_reference_dois, get_retraction

__all__ = [
    "CrossrefClient",
    "OpenAlexClient",
    "check_reference_dois",
    "get_retraction",
    "normalize_doi",
]

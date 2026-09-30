"""
DOI Normalization Utility for OpenPaperCheck.

Rules:
- DOI is case-insensitive, normalized to lowercase without URL prefix.
- Validates strictly against format: ^10\\.\\d{4,9}/\\S+$
- Never raises an unhandled exception.
"""

from __future__ import annotations

import re
import urllib.parse

# Standard DOI pattern: 10. + 4 to 9 digits + / + non-whitespace characters
DOI_PATTERN = re.compile(r"^10\.\d{4,9}/\S+$")

# Prefixes to strip
PREFIX_PATTERN = re.compile(
    r"^(https?://(?:dx\.)?doi\.org/|doi:)",
    re.IGNORECASE,
)


def normalize_doi(raw: str | None) -> str | None:
    """
    Normalise a DOI string into a canonical, lowercase, prefix-free form.

    Returns:
        Canonical DOI string if valid, otherwise None.
    """
    if not raw or not isinstance(raw, str):
        return None

    cleaned = raw.strip()
    if not cleaned:
        return None

    # Strip enclosing wrapper pairs (e.g. "(10.1038/...)", "<...>", quotes)
    while len(cleaned) >= 2 and (
        (cleaned.startswith("(") and cleaned.endswith(")"))
        or (cleaned.startswith("[") and cleaned.endswith("]"))
        or (cleaned.startswith("<") and cleaned.endswith(">"))
        or (cleaned.startswith('"') and cleaned.endswith('"'))
        or (cleaned.startswith("'") and cleaned.endswith("'"))
    ):
        cleaned = cleaned[1:-1].strip()

    # Strip standard URL and protocol prefixes
    cleaned = PREFIX_PATTERN.sub("", cleaned)

    # URL-decode (handles %2F for slashes etc.)
    cleaned = urllib.parse.unquote(cleaned)

    # Strip again and lowercase
    cleaned = cleaned.strip().lower()

    # Strip enclosing quotes or angle brackets
    cleaned = cleaned.strip("\"'<>")

    # Strip trailing punctuation often accidentally captured in citations
    cleaned = cleaned.rstrip(".,;:")

    # Strip trailing parenthesis/bracket only if unmatched (e.g. from citation context "(see 10.1038/...")
    while cleaned.endswith(")") and cleaned.count(")") > cleaned.count("("):
        cleaned = cleaned[:-1].rstrip(".,;:")
    while cleaned.endswith("]") and cleaned.count("]") > cleaned.count("["):
        cleaned = cleaned[:-1].rstrip(".,;:")

    # Validate against regex
    if not DOI_PATTERN.match(cleaned):
        return None

    return cleaned


def is_valid_doi(raw: str | None) -> bool:
    """Return True if the input represents a valid DOI."""
    return normalize_doi(raw) is not None

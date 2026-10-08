"""
Property-based tests for DOI normalisation using Hypothesis.
"""

from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st

from openpapercheck.core.doi import normalize_doi


@given(st.text())
def test_normalize_doi_never_crashes(s: str):
    """normalize_doi must never raise an unhandled exception for any text input."""
    res = normalize_doi(s)
    assert res is None or isinstance(res, str)


@given(st.from_regex(r"^10\.\d{4,9}/[a-zA-Z0-9_\-\.\(\)]*[a-zA-Z0-9\)]+$", fullmatch=True))
def test_normalize_doi_idempotent_on_valid(doi: str):
    """For any valid DOI, normalizing twice yields the exact same canonical string."""
    first = normalize_doi(doi)
    assert first is not None
    assert first == first.lower()
    second = normalize_doi(first)
    assert first == second

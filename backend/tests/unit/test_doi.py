"""
Unit tests for DOI normalisation.
"""

from __future__ import annotations

import pytest

from openpapercheck.core.doi import is_valid_doi, normalize_doi


@pytest.mark.parametrize(
    "raw,expected",
    [
        # Standard DOIs
        ("10.1038/nature12373", "10.1038/nature12373"),
        ("10.1126/science.1105458", "10.1126/science.1105458"),
        # Upper/mixed case -> lowercase
        ("10.1016/S0140-6736(97)11096-0", "10.1016/s0140-6736(97)11096-0"),
        ("10.1000/182", "10.1000/182"),
        # URL prefixes
        ("https://doi.org/10.1038/nature12373", "10.1038/nature12373"),
        ("http://doi.org/10.1038/nature12373", "10.1038/nature12373"),
        ("https://dx.doi.org/10.1038/nature12373", "10.1038/nature12373"),
        ("http://dx.doi.org/10.1038/nature12373", "10.1038/nature12373"),
        # Protocol prefix
        ("doi:10.1038/nature12373", "10.1038/nature12373"),
        ("DOI:10.1038/NATURE12373", "10.1038/nature12373"),
        # Trailing punctuation
        ("10.1038/nature12373.", "10.1038/nature12373"),
        ("10.1038/nature12373,", "10.1038/nature12373"),
        ("10.1038/nature12373;", "10.1038/nature12373"),
        ("https://doi.org/10.1038/nature12373)", "10.1038/nature12373"),
        ("(10.1038/nature12373)", "10.1038/nature12373"),
        ('"10.1038/nature12373"', "10.1038/nature12373"),
        ("<10.1038/nature12373>", "10.1038/nature12373"),
        ("10.1000/182(2)", "10.1000/182(2)"),
        # Whitespace
        ("   10.1038/nature12373 \n\t", "10.1038/nature12373"),
        # URL encoding
        ("10.1000%2F182", "10.1000/182"),
    ],
)
def test_normalize_doi_valid(raw: str, expected: str):
    assert normalize_doi(raw) == expected
    assert is_valid_doi(raw) is True


@pytest.mark.parametrize(
    "invalid",
    [
        "",
        "   ",
        None,
        "not-a-doi",
        "10.1/short",
        "10/12345",
        "https://example.com/paper.pdf",
        "arXiv:2104.12345",
    ],
)
def test_normalize_doi_invalid(invalid: str | None):
    assert normalize_doi(invalid) is None
    assert is_valid_doi(invalid) is False


def test_normalize_doi_idempotence():
    original = "https://doi.org/10.1038/NATURE12373."
    first = normalize_doi(original)
    second = normalize_doi(first)
    assert first == second == "10.1038/nature12373"

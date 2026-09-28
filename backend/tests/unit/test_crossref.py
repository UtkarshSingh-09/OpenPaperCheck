"""
Unit tests for CrossrefClient and 3-tier reference list parsing.
"""

from __future__ import annotations

import respx

from openpapercheck.core.crossref import CrossrefClient


@respx.mock
def test_crossref_client_parses_deposited_references():
    """Verify parsing work with both with-DOI and unstructured references."""
    doi = "10.1038/nature12373"
    mock_payload = {
        "status": "ok",
        "message": {
            "title": ["A high-precision sensor"],
            "container-title": ["Nature"],
            "publisher": "Springer Nature",
            "published-print": {"date-parts": [[2013, 5, 2]]},
            "references-count": 2,
            "reference": [
                {
                    "key": "ref1",
                    "DOI": "10.1126/science.1105458",
                    "article-title": "Reference paper with DOI",
                    "year": "2006",
                },
                {
                    "key": "ref2",
                    "unstructured": "Author A. 2010. Book chapter without DOI.",
                    "year": "2010",
                },
            ],
        },
    }

    respx.get(f"https://api.crossref.org/works/{doi}").respond(status_code=200, json=mock_payload)

    client = CrossrefClient(mailto="test@example.org")
    work = client.get_work(doi)

    assert work is not None
    assert work["title"] == "A high-precision sensor"
    assert work["journal"] == "Nature"
    assert work["publication_date"] == "2013-05-02"

    refs = work["references"]
    assert refs["deposit_status"] == "deposited"
    assert refs["total_listed"] == 2
    assert len(refs["with_doi"]) == 1
    assert refs["with_doi"][0]["doi"] == "10.1126/science.1105458"
    assert len(refs["without_doi"]) == 1
    assert "Book chapter" in refs["without_doi"][0]["raw"]


@respx.mock
def test_crossref_client_handles_restricted_references():
    """Verify handling when publisher declares reference counts but restricts deposit."""
    doi = "10.1016/restricted-paper"
    mock_payload = {
        "status": "ok",
        "message": {
            "title": ["Restricted paper"],
            "container-title": ["Closed Journal"],
            "publisher": "Closed Publisher",
            "references-count": 45,
            # No "reference" key in message
        },
    }

    respx.get(f"https://api.crossref.org/works/{doi}").respond(status_code=200, json=mock_payload)

    client = CrossrefClient()
    work = client.get_work(doi)

    assert work is not None
    assert work["references"]["deposit_status"] == "restricted"
    assert work["references"]["total_listed"] == 45
    assert len(work["references"]["with_doi"]) == 0
    assert len(work["references"]["without_doi"]) == 0


@respx.mock
def test_crossref_client_404_returns_none():
    """Verify 404 returns None instead of raising."""
    doi = "10.9999/nonexistent"
    respx.get(f"https://api.crossref.org/works/{doi}").respond(status_code=404)

    client = CrossrefClient()
    assert client.get_work(doi) is None

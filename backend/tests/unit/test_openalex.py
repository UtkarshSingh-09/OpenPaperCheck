"""
Unit tests for openpapercheck.core.openalex (OpenAlexClient).
"""

import respx

from openpapercheck.core.openalex import OpenAlexClient


@respx.mock
def test_openalex_get_work_success():
    client = OpenAlexClient(api_key="test-key", mailto="test@example.org")
    doi = "10.1038/nature12373"

    mock_data = {
        "id": "https://openalex.org/W2143924128",
        "title": "Nanometre-scale thermometry in a living cell",
        "publication_year": 2013,
        "publication_date": "2013-08-01",
        "is_retracted": False,
        "referenced_works": [
            "https://openalex.org/W198234123",
            "https://openalex.org/W209384712",
        ],
    }

    respx.get(f"https://api.openalex.org/works/https://doi.org/{doi}").respond(
        status_code=200, json=mock_data
    )

    work = client.get_work(doi)
    assert work is not None
    assert work["doi"] == doi
    assert work["title"] == "Nanometre-scale thermometry in a living cell"
    assert work["publication_year"] == 2013
    assert work["is_retracted"] is False
    assert work["referenced_works_count"] == 2

    # Verify zero personal/people features in output
    for key in work.keys():
        assert key not in ("authors", "institutions", "countries", "affiliations")


@respx.mock
def test_openalex_get_work_not_found():
    client = OpenAlexClient()
    doi = "10.1000/not-found-doi"

    respx.get(f"https://api.openalex.org/works/https://doi.org/{doi}").respond(status_code=404)

    work = client.get_work(doi)
    assert work is None


@respx.mock
def test_openalex_get_work_network_error():
    client = OpenAlexClient()
    doi = "10.1000/server-error-doi"

    respx.get(f"https://api.openalex.org/works/https://doi.org/{doi}").respond(status_code=500)

    # Should not raise exception, but return None gracefully
    work = client.get_work(doi)
    assert work is None


@respx.mock
def test_openalex_get_work_quota_exceeded():
    """Verify OpenAlex client handles HTTP 429 quota exhaustion gracefully."""
    client = OpenAlexClient(api_key="exhausted-key")
    doi = "10.1000/some-doi"

    respx.get(f"https://api.openalex.org/works/https://doi.org/{doi}").respond(
        status_code=429, json={"error": "Daily quota exceeded", "message": "API key daily limit reached"}
    )

    work = client.get_work(doi)
    assert work is None


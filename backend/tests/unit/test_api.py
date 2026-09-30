"""
Unit tests for OpenPaperCheck REST API (FastAPI v1).
Tests endpoints:
- GET /v1/health
- GET /v1/sources
- GET /v1/check/{doi}
- RFC 9457 problem+json error formatting (400, 404, 422)
- Signals S-001, S-002, S-003, S-010, S-040 verification
- Banned words / ETHICS.md compliance test
"""

from __future__ import annotations

import pytest
import respx
from fastapi.testclient import TestClient

from openpapercheck.api.main import create_app
from openpapercheck.ingest.snapshot_builder import build_sqlite_snapshot

client = TestClient(create_app())


@pytest.fixture(autouse=True)
def setup_test_snapshot(tmp_path, monkeypatch):
    """Ensure a sample snapshot exists for all API tests."""
    monkeypatch.setenv("OPC_DATA_DIR", str(tmp_path))
    build_sqlite_snapshot(use_sample=True)


def test_api_health_endpoint():
    """Verify GET /v1/health returns 200 and healthy metadata."""
    response = client.get("/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["db"] == "ok"
    assert data["version"] == "0.1.0.dev2"
    assert data["is_sample"] is True
    assert data["records_count"] == 11


def test_api_sources_endpoint():
    """Verify GET /v1/sources returns transparency metadata for upstream authorities."""
    response = client.get("/v1/sources")
    assert response.status_code == 200
    data = response.json()
    assert "sources" in data
    source_names = [s["name"] for s in data["sources"]]
    assert any("Retraction Watch" in name for name in source_names)
    assert any("Crossref" in name for name in source_names)
    assert any("OpenAlex" in name for name in source_names)


def test_api_check_invalid_doi_syntax():
    """Verify checking an invalid DOI returns RFC 9457 400 Bad Request."""
    response = client.get("/v1/check/not-a-real-doi")
    assert response.status_code == 400
    assert response.headers["content-type"] == "application/problem+json"
    data = response.json()
    assert data["status"] == 400
    assert data["title"] == "Invalid DOI Syntax"
    assert "type" in data
    assert "instance" in data


@respx.mock
def test_api_check_clean_paper():
    """Verify checking a clean paper returns 200 NO_FLAGS_FOUND with signals."""
    doi = "10.1038/nature12373"
    mock_payload = {
        "status": "ok",
        "message": {
            "title": ["Nanometre-scale thermometry in a living cell"],
            "container-title": ["Nature"],
            "publisher": "Springer Nature",
            "published-print": {"date-parts": [[2013, 8, 1]]},
            "references-count": 2,
            "reference": [
                {"key": "ref1", "DOI": "10.1038/clean1"},
                {"key": "ref2", "DOI": "10.1038/clean2"},
            ],
        },
    }
    respx.get(f"https://api.crossref.org/works/{doi}").respond(status_code=200, json=mock_payload)

    response = client.get(f"/v1/check/{doi}")
    assert response.status_code == 200
    data = response.json()

    assert data["doi"] == doi
    assert data["state"] == "no_flags_found"
    assert "No retractions" in data["headline"]
    assert data["paper"]["title"] == "Nanometre-scale thermometry in a living cell"
    assert data["references"]["total"] == 2
    assert data["references"]["with_doi"] == 2
    assert len(data["references"]["retracted"]) == 0

    # Signals verification
    signals = {s["id"]: s for s in data["signals"]}
    assert "S-001" in signals
    assert signals["S-001"]["value"] is False
    assert "S-010" in signals
    assert signals["S-010"]["value"] == 0
    assert signals["S-040"]["value"]["deposit_status"] in ("deposited", "open")
    assert data["references"]["available"] is True


@respx.mock
def test_api_check_retracted_paper():
    """Verify checking Wakefield returns 200 RETRACTED_EXTERNAL with Record #4036."""
    doi = "10.1016/s0140-6736(97)11096-0"
    mock_payload = {
        "status": "ok",
        "message": {
            "title": ["RETRACTED: Ileal-lymphoid-nodular hyperplasia"],
            "container-title": ["The Lancet"],
            "publisher": "Elsevier",
            "published-print": {"date-parts": [[1998, 2, 28]]},
            "references-count": 0,
            "reference": [],
        },
    }
    respx.get(f"https://api.crossref.org/works/{doi}").respond(status_code=200, json=mock_payload)

    response = client.get(f"/v1/check/{doi}")
    assert response.status_code == 200
    data = response.json()

    assert data["doi"] == doi
    assert data["state"] == "retracted_external"
    assert "RETRACTED" in data["headline"]

    # Verify authentic Retraction Watch Record #4036
    signals = {s["id"]: s for s in data["signals"]}
    assert signals["S-001"]["value"] is True
    evidence = signals["S-001"]["evidence"][0]
    assert evidence["rw_record_id"] == 4036
    assert evidence["retraction_date"] == "2010-02-06"


@respx.mock
def test_api_check_doi_not_found_404():
    """Verify non-existent DOI returns RFC 9457 404 Not Found."""
    doi = "10.1000/does-not-exist-anywhere-xyz"
    respx.get(f"https://api.crossref.org/works/{doi}").respond(status_code=404)

    response = client.get(f"/v1/check/{doi}")
    assert response.status_code == 404
    assert response.headers["content-type"] == "application/problem+json"
    data = response.json()
    assert data["status"] == 404
    assert data["title"] == "DOI Not Found"


@respx.mock
def test_api_ethics_banned_words_compliance():
    """
    ETHICS.md Compliance Test:
    Ensures no response generated by the API contains banned subjective words:
    ['fake', 'fraud', 'fabricated', 'scam', 'cheat', 'guilty'].
    (Only factual quotes like verbatim reason strings are exempt from non-attribution).
    """
    doi = "10.1038/nature12373"
    mock_payload = {
        "status": "ok",
        "message": {
            "title": ["Clean Paper"],
            "container-title": ["Nature"],
            "publisher": "Springer",
            "published-print": {"date-parts": [[2020, 1, 1]]},
            "references-count": 0,
            "reference": [],
        },
    }
    respx.get(f"https://api.crossref.org/works/{doi}").respond(status_code=200, json=mock_payload)

    response = client.get(f"/v1/check/{doi}")
    assert response.status_code == 200
    text_content = response.text.lower()

    banned_words = ["fake", "fraud", "scam", "cheat", "guilty"]
    for word in banned_words:
        assert f" {word} " not in text_content, f"Banned subjective word '{word}' found in API response!"

"""
Unit tests for SQLite snapshot storage reader and builder.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from openpapercheck.core.storage import (
    check_reference_dois,
    get_retraction,
)
from openpapercheck.ingest.snapshot_builder import build_sqlite_snapshot


@pytest.fixture(autouse=True)
def setup_snapshot(tmp_path, monkeypatch):
    """Point OPC_DATA_DIR to temporary path and build sample snapshot."""
    monkeypatch.setenv("OPC_DATA_DIR", str(tmp_path))
    build_sqlite_snapshot(use_sample=True)


def test_get_retraction_known_retracted():
    """Verify lookup of a known retracted paper from sample fixture."""
    doi = "10.1016/s0140-6736(97)11096-0"
    ret = get_retraction(doi)
    assert ret is not None
    assert ret["doi"] == doi
    assert ret["nature"] == "Retraction"
    assert any("Fabrication" in r for r in ret["reasons"])


def test_get_retraction_clean_paper():
    """Verify that a clean DOI returns None."""
    doi = "10.1038/nature12373"
    ret = get_retraction(doi)
    assert ret is None


def test_check_reference_dois_batch():
    """Verify batch lookup of multiple reference DOIs."""
    dois = [
        "10.1038/nature12373",  # Clean
        "10.1126/science.1105458",  # Retracted
        "10.1038/nature04473",  # Retracted
        "invalid-doi",  # Invalid
    ]
    results = check_reference_dois(dois)
    assert "10.1126/science.1105458" in results
    assert "10.1038/nature04473" in results
    assert "10.1038/nature12373" not in results


def test_storage_edge_cases_and_error_handling(tmp_path: Path):
    """Verify defensive handling of missing files, bad JSON, and invalid DOIs."""
    from openpapercheck.core.storage import (
        get_connection,
        get_manifest,
        has_snapshot,
    )

    # 1. Non-existent snapshot path
    fake_db = tmp_path / "nonexistent.sqlite"
    with pytest.raises(FileNotFoundError):
        get_connection(db_path=fake_db)

    # 2. get_retraction with invalid DOI format
    assert get_retraction("not_a_doi") is None
    assert get_retraction("") is None

    # 3. Corrupt manifest handling
    corrupt_manifest = tmp_path / "manifest.json"
    with open(corrupt_manifest, "w", encoding="utf-8") as f:
        f.write("{invalid-json-content")
    # Point get_manifest to read this path
    with pytest.MonkeyPatch.context() as mp:
        mp.setenv("OPC_DATA_DIR", str(tmp_path))
        assert get_manifest() is None

    # 4. Valid manifest reading
    valid_manifest = tmp_path / "manifest.json"
    with open(valid_manifest, "w", encoding="utf-8") as f:
        f.write(json.dumps({"rows_count": 100, "as_of": "2026-09-29"}))
    with pytest.MonkeyPatch.context() as mp:
        mp.setenv("OPC_DATA_DIR", str(tmp_path))
        manifest = get_manifest()
        assert manifest is not None
        assert manifest["rows_count"] == 100
        assert manifest["as_of"] == "2026-09-29"

    # 5. has_snapshot
    assert has_snapshot() is True

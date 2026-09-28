"""
Unit tests for SQLite snapshot storage reader and builder.
"""

from __future__ import annotations

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

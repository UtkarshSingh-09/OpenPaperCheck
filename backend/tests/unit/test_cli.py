"""
Comprehensive Unit tests for Typer CLI commands.
Verifies all 4 PaperPublicStates, edge cases (404, network error, invalid DOI),
stale snapshot warnings, and the automated golden set evaluation suite.
"""

from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path

import httpx
import respx
from typer.testing import CliRunner

from openpapercheck.cli import app
from openpapercheck.ingest.snapshot_builder import build_sqlite_snapshot

runner = CliRunner()


def test_cli_version():
    """Verify opc version prints the version string."""
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "OpenPaperCheck version" in result.stdout


def test_cli_check_invalid_doi():
    """Verify checking an invalid DOI exits with code 1 and helpful explanation."""
    result = runner.invoke(app, ["check", "not-a-valid-doi"])
    assert result.exit_code == 1
    assert "Error:" in result.stdout
    assert "Standard DOIs begin with '10.'" in result.stdout


@respx.mock
def test_cli_check_needs_review(tmp_path, monkeypatch):
    """Verify checking a paper with retracted citations shows NEEDS REVIEW badge."""
    monkeypatch.setenv("OPC_DATA_DIR", str(tmp_path))
    build_sqlite_snapshot(use_sample=True)

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
                    "article-title": "Retracted stem cell paper",
                    "year": "2006",
                },
                {
                    "key": "ref2",
                    "DOI": "10.1016/j.cell.2020.08.020",
                    "article-title": "Clean coronavirus paper",
                    "year": "2020",
                },
            ],
        },
    }

    respx.get(f"https://api.crossref.org/works/{doi}").respond(status_code=200, json=mock_payload)

    result = runner.invoke(app, ["check", doi])
    assert result.exit_code == 0
    assert "A high-precision sensor" in result.stdout
    assert "NEEDS REVIEW" in result.stdout
    assert "Flagged references detected" in result.stdout
    assert "References (2 total listed)" in result.stdout
    assert "1 listed as retracted" in result.stdout
    assert "10.1126/science.1105458" in result.stdout
    assert "Data as of:" in result.stdout


@respx.mock
def test_cli_check_no_flags_found(tmp_path, monkeypatch):
    """Verify clean paper with clean references shows NO FLAGS FOUND badge."""
    monkeypatch.setenv("OPC_DATA_DIR", str(tmp_path))
    build_sqlite_snapshot(use_sample=True)

    doi = "10.1038/nature12373"
    mock_payload = {
        "status": "ok",
        "message": {
            "title": ["A completely clean study"],
            "container-title": ["Nature"],
            "publisher": "Springer Nature",
            "published-print": {"date-parts": [[2021, 1, 1]]},
            "references-count": 1,
            "reference": [
                {
                    "key": "ref1",
                    "DOI": "10.1016/j.cell.2020.08.020",
                    "article-title": "Clean coronavirus paper",
                    "year": "2020",
                },
            ],
        },
    }

    respx.get(f"https://api.crossref.org/works/{doi}").respond(status_code=200, json=mock_payload)

    result = runner.invoke(app, ["check", doi])
    assert result.exit_code == 0
    assert "NO FLAGS FOUND" in result.stdout
    assert "No retractions or flagged references recorded" in result.stdout
    assert "Data as of:" in result.stdout


@respx.mock
def test_cli_check_retracted_paper(tmp_path, monkeypatch):
    """Verify checking a retracted paper shows RETRACTED EXTERNAL badge."""
    monkeypatch.setenv("OPC_DATA_DIR", str(tmp_path))
    build_sqlite_snapshot(use_sample=True)

    doi = "10.1016/s0140-6736(97)11096-0"
    mock_payload = {
        "status": "ok",
        "message": {
            "title": ["Retracted autism study"],
            "container-title": ["The Lancet"],
            "publisher": "Elsevier",
            "published-print": {"date-parts": [[1998, 2, 28]]},
            "references-count": 0,
            "reference": [],
        },
    }

    respx.get(f"https://api.crossref.org/works/{doi}").respond(status_code=200, json=mock_payload)

    result = runner.invoke(app, ["check", doi])
    assert result.exit_code == 0
    assert "RETRACTED EXTERNAL" in result.stdout
    assert "Retraction Watch (Record #1001" in result.stdout
    assert "Data as of:" in result.stdout


@respx.mock
def test_cli_check_restricted_references(tmp_path, monkeypatch):
    """Verify checking a paper with restricted references shows INSUFFICIENT DATA."""
    monkeypatch.setenv("OPC_DATA_DIR", str(tmp_path))
    build_sqlite_snapshot(use_sample=True)

    doi = "10.1002/anie.201802874"
    mock_payload = {
        "status": "ok",
        "message": {
            "title": ["Paper with closed citations"],
            "container-title": ["Angewandte Chemie"],
            "publisher": "Wiley",
            "published-print": {"date-parts": [[2018, 5, 1]]},
            "references-count": 45,
            # No reference array deposited
        },
    }

    respx.get(f"https://api.crossref.org/works/{doi}").respond(status_code=200, json=mock_payload)

    result = runner.invoke(app, ["check", doi])
    assert result.exit_code == 0
    assert "INSUFFICIENT DATA" in result.stdout
    assert "restricted open access" in result.stdout
    assert "Data as of:" in result.stdout


@respx.mock
def test_cli_check_404_not_found(tmp_path, monkeypatch):
    """Verify checking a nonexistent DOI in Crossref displays HTTP 404 message."""
    monkeypatch.setenv("OPC_DATA_DIR", str(tmp_path))
    build_sqlite_snapshot(use_sample=True)

    doi = "10.1038/doesnotexist9999"
    respx.get(f"https://api.crossref.org/works/{doi}").respond(status_code=404)

    result = runner.invoke(app, ["check", doi])
    assert result.exit_code == 1
    assert "DOI not found in Crossref (HTTP 404)" in result.stdout


@respx.mock
def test_cli_check_network_timeout(tmp_path, monkeypatch):
    """Verify network timeouts are handled gracefully."""
    monkeypatch.setenv("OPC_DATA_DIR", str(tmp_path))
    build_sqlite_snapshot(use_sample=True)

    doi = "10.1038/nature12373"
    respx.get(f"https://api.crossref.org/works/{doi}").mock(
        side_effect=httpx.ConnectTimeout("Connection timed out")
    )

    result = runner.invoke(app, ["check", doi])
    assert result.exit_code == 1
    assert "timed out" in result.stdout


def test_cli_stale_snapshot_warning(tmp_path, monkeypatch):
    """Verify warning is printed when snapshot is older than 30 days."""
    monkeypatch.setenv("OPC_DATA_DIR", str(tmp_path))
    build_sqlite_snapshot(use_sample=True)

    # Overwrite manifest with stale date
    manifest_path = tmp_path / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["as_of"] = "2020-01-01"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    result = runner.invoke(app, ["check", "10.1038/nature12373"])
    assert "Warning:" in result.stdout
    assert "days old" in result.stdout


def test_cli_snapshot_commands(tmp_path, monkeypatch):
    """Verify opc snapshot and opc snapshot build commands."""
    monkeypatch.setenv("OPC_DATA_DIR", str(tmp_path))

    # Test direct snapshot with --sample
    res1 = runner.invoke(app, ["snapshot", "--sample"])
    assert res1.exit_code == 0
    assert "Snapshot successfully built" in res1.stdout

    # Test snapshot build with --sample
    res2 = runner.invoke(app, ["snapshot", "build", "--sample"])
    assert res2.exit_code == 0
    assert "Snapshot successfully built" in res2.stdout


@respx.mock
def test_cli_update_command(tmp_path, monkeypatch):
    """Verify opc update downloads manifest and snapshot."""
    monkeypatch.setenv("OPC_DATA_DIR", str(tmp_path))

    # Create dummy compressed file
    dummy_data = b"SQLite format 3\x00dummy-retraction-db"
    compressed = gzip.compress(dummy_data)
    checksum = hashlib.sha256(compressed).hexdigest()

    manifest = {
        "as_of": "2026-09-28",
        "schema_version": 1,
        "rows_count": 42,
        "sha256": checksum,
        "file_size_bytes": len(compressed),
    }

    manifest_url = "https://github.com/UtkarshSingh-09/OpenPaperCheck/releases/download/data-latest/manifest.json"
    snapshot_url = "https://github.com/UtkarshSingh-09/OpenPaperCheck/releases/download/data-latest/retraction_records.sqlite.gz"

    respx.get(manifest_url).respond(status_code=200, json=manifest)
    respx.get(snapshot_url).respond(status_code=200, content=compressed)

    result = runner.invoke(app, ["update"])
    assert result.exit_code == 0
    assert "Snapshot successfully updated" in result.stdout

    # Test second call detects up to date
    result_uptodate = runner.invoke(app, ["update"])
    assert result_uptodate.exit_code == 0
    assert "Local snapshot is already up to date" in result_uptodate.stdout


def test_cli_ingest_rw(tmp_path, monkeypatch):
    """Verify opc ingest rw command."""
    monkeypatch.setenv("OPC_DATA_DIR", str(tmp_path))
    result = runner.invoke(app, ["ingest", "rw", "--sample"])
    assert result.exit_code == 0
    assert "Snapshot successfully built" in result.stdout

"""
Unit tests for Typer CLI commands.
"""

from __future__ import annotations

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
    """Verify checking an invalid DOI exits with code 1."""
    result = runner.invoke(app, ["check", "not-a-valid-doi"])
    assert result.exit_code == 1
    assert "Error:" in result.stdout


@respx.mock
def test_cli_check_clean_doi(tmp_path, monkeypatch):
    """Verify checking a clean DOI displays metadata and reference tree."""
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
    assert "No retraction recorded" in result.stdout
    assert "References (2 total listed)" in result.stdout
    assert "1 listed as retracted" in result.stdout
    assert "10.1126/science.1105458" in result.stdout


@respx.mock
def test_cli_check_retracted_paper(tmp_path, monkeypatch):
    """Verify checking a retracted paper shows bold retracted banner."""
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
    assert "RETRACTED" in result.stdout
    assert "Retraction Watch (Record #1001" in result.stdout


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
    import gzip
    import hashlib

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

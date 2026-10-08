"""
Comprehensive Unit tests for Typer CLI commands.
Verifies all 4 PaperPublicStates, edge cases (404, network error, invalid DOI),
stale snapshot warnings, and the automated golden set evaluation suite.
"""

from __future__ import annotations

import gzip
import hashlib
import json

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
    assert "Retraction Watch (Record #4036" in result.stdout
    assert "SAMPLE MODE:" in result.stdout
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


@respx.mock
def test_cli_check_no_internet_connection(tmp_path, monkeypatch):
    """Verify clean, graceful error message when no internet connection is available (ConnectError)."""
    monkeypatch.setenv("OPC_DATA_DIR", str(tmp_path))
    build_sqlite_snapshot(use_sample=True)

    doi = "10.1038/nature12373"
    respx.get(f"https://api.crossref.org/works/{doi}").mock(
        side_effect=httpx.ConnectError(
            "Failed to establish a new connection: [Errno 8] nodename nor servname provided, or not known"
        )
    )

    result = runner.invoke(app, ["check", doi])
    assert result.exit_code == 1
    assert "Network error querying Crossref API" in result.stdout
    assert "Unable to reach api.crossref.org" in result.stdout


@respx.mock
def test_cli_check_eoc_target_paper(tmp_path, monkeypatch):
    """Verify a target paper with only an Expression of Concern gets NEEDS REVIEW and explicit EOC notice."""
    monkeypatch.setenv("OPC_DATA_DIR", str(tmp_path))
    build_sqlite_snapshot(use_sample=True)

    doi = "10.1177/0146167209342755"
    mock_payload = {
        "status": "ok",
        "message": {
            "title": ["Why Love Has Wings and Sex Has Not"],
            "container-title": ["Personality and Social Psychology Bulletin"],
            "publisher": "SAGE Publications",
            "published-print": {"date-parts": [[2009, 11]]},
            "references-count": 0,
            "reference": [],
        },
    }
    respx.get(f"https://api.crossref.org/works/{doi}").respond(status_code=200, json=mock_payload)

    result = runner.invoke(app, ["check", doi])
    assert result.exit_code == 0
    assert "NEEDS REVIEW" in result.stdout
    assert "EXPRESSION OF CONCERN" in result.stdout
    assert "Record #5314" in result.stdout


@respx.mock
def test_cli_check_correction_not_flagged(tmp_path, monkeypatch):
    """Verify that a paper with only a routine Correction (Erratum) is NOT marked retracted or needs_review."""
    monkeypatch.setenv("OPC_DATA_DIR", str(tmp_path))
    build_sqlite_snapshot(use_sample=True)

    doi = "10.1126/science.1076185"
    mock_payload = {
        "status": "ok",
        "message": {
            "title": ["Corrected Genomics Study"],
            "container-title": ["Science"],
            "publisher": "AAAS",
            "published-print": {"date-parts": [[2003, 5, 10]]},
            "references-count": 1,
            "reference": [
                {
                    "key": "ref1",
                    "DOI": "10.1016/j.cell.2020.08.020",
                    "article-title": "Clean study",
                    "year": "2020",
                }
            ],
        },
    }
    respx.get(f"https://api.crossref.org/works/{doi}").respond(status_code=200, json=mock_payload)

    result = runner.invoke(app, ["check", doi])
    assert result.exit_code == 0
    assert "NO FLAGS FOUND" in result.stdout
    assert "RETRACTED" not in result.stdout
    assert "Correction" in result.stdout


@respx.mock
def test_cli_check_reference_with_correction_not_flagged(tmp_path, monkeypatch):
    """Verify that citing a paper that only has a Correction does NOT trigger needs_review."""
    monkeypatch.setenv("OPC_DATA_DIR", str(tmp_path))
    build_sqlite_snapshot(use_sample=True)

    import sqlite3

    db_file = tmp_path / "retraction_records.sqlite"
    with sqlite3.connect(db_file) as conn:
        conn.execute(
            """
            INSERT INTO retraction_records (rw_record_id, original_doi, nature, reasons, retraction_date, original_date, notice_urls)
            VALUES (99993, '10.1126/science.corrigendum1', 'Correction', 'Error in Text;', '2015-01-01', '2014-01-01', 'https://example.com/c')
            """
        )

    doi = "10.1038/nature99999"
    mock_payload = {
        "status": "ok",
        "message": {
            "title": ["Citing Paper With Corrected Reference"],
            "container-title": ["Nature"],
            "publisher": "Springer Nature",
            "published-print": {"date-parts": [[2016, 1, 1]]},
            "references-count": 1,
            "reference": [
                {
                    "key": "ref1",
                    "DOI": "10.1126/science.corrigendum1",
                    "article-title": "A paper that had a typo corrected",
                    "year": "2014",
                }
            ],
        },
    }
    respx.get(f"https://api.crossref.org/works/{doi}").respond(status_code=200, json=mock_payload)

    result = runner.invoke(app, ["check", doi])
    assert result.exit_code == 0
    assert "NO FLAGS FOUND" in result.stdout
    assert "NEEDS REVIEW" not in result.stdout


@respx.mock
def test_cli_check_reinstatement_not_flagged(tmp_path, monkeypatch):
    """Verify that a paper or cited reference with nature='Reinstatement' is NOT flagged as retracted or needs_review."""
    monkeypatch.setenv("OPC_DATA_DIR", str(tmp_path))
    build_sqlite_snapshot(use_sample=True)

    import sqlite3

    db_file = tmp_path / "retraction_records.sqlite"
    with sqlite3.connect(db_file) as conn:
        conn.execute(
            """
            INSERT INTO retraction_records (rw_record_id, original_doi, nature, reasons, retraction_date, original_date, notice_urls)
            VALUES (99994, '10.1016/j.reinstated.2020', 'Reinstatement', 'Author Exonerated;Investigation by Institution;', '2021-05-01', '2019-01-01', 'https://example.com/reinstated')
            """
        )

    # 1. Citing paper referencing reinstated work
    doi_citing = "10.1038/nature.citing.reinstated"
    mock_payload_citing = {
        "status": "ok",
        "message": {
            "title": ["Paper Citing A Reinstated Work"],
            "container-title": ["Nature"],
            "publisher": "Springer Nature",
            "published-print": {"date-parts": [[2022, 1, 1]]},
            "references-count": 1,
            "reference": [
                {
                    "key": "ref1",
                    "DOI": "10.1016/j.reinstated.2020",
                    "article-title": "A paper that was cleared and reinstated",
                    "year": "2019",
                }
            ],
        },
    }
    respx.get(f"https://api.crossref.org/works/{doi_citing}").respond(
        status_code=200, json=mock_payload_citing
    )

    res_citing = runner.invoke(app, ["check", doi_citing])
    assert res_citing.exit_code == 0
    assert "NO FLAGS FOUND" in res_citing.stdout
    assert "NEEDS REVIEW" not in res_citing.stdout

    # 2. Target paper itself is reinstated
    doi_reinstated = "10.1016/j.reinstated.2020"
    mock_payload_target = {
        "status": "ok",
        "message": {
            "title": ["A Cleared and Reinstated Discovery"],
            "container-title": ["Cell"],
            "publisher": "Elsevier",
            "published-print": {"date-parts": [[2019, 1, 1]]},
            "references-count": 1,
            "reference": [
                {
                    "key": "ref1",
                    "DOI": "10.1016/j.cell.2020.08.020",
                    "article-title": "Clean discovery",
                    "year": "2020",
                }
            ],
        },
    }
    respx.get(f"https://api.crossref.org/works/{doi_reinstated}").respond(
        status_code=200, json=mock_payload_target
    )

    res_target = runner.invoke(app, ["check", doi_reinstated])
    assert res_target.exit_code == 0
    assert "NO FLAGS FOUND" in res_target.stdout
    assert "RETRACTED" not in res_target.stdout
    assert "Reinstatement" in res_target.stdout


def test_opc_ingest_rw_idempotency(tmp_path, monkeypatch):
    """
    Verify DoD Requirement: 'Full RW ingest idempotent'.
    Running opc ingest rw repeatedly must produce identical row counts,
    prevent duplicate rows, enforce primary key uniqueness, and yield identical checksums.
    """
    import sqlite3

    monkeypatch.setenv("OPC_DATA_DIR", str(tmp_path))

    # Run 1: Initial ingest
    res1 = runner.invoke(app, ["ingest", "rw", "--sample"])
    assert res1.exit_code == 0
    assert "Snapshot successfully built" in res1.stdout

    db_path = tmp_path / "retraction_records.sqlite"
    manifest_path = tmp_path / "manifest.json"
    assert db_path.is_file()
    assert manifest_path.is_file()

    with sqlite3.connect(db_path) as conn:
        count_1 = conn.execute("SELECT count(*) FROM retraction_records").fetchone()[0]
        distinct_ids_1 = conn.execute(
            "SELECT count(DISTINCT rw_record_id) FROM retraction_records"
        ).fetchone()[0]

    manifest_1 = json.loads(manifest_path.read_text(encoding="utf-8"))

    # Run 2: Re-run ingest on identical source
    res2 = runner.invoke(app, ["ingest", "rw", "--sample"])
    assert res2.exit_code == 0
    assert "Snapshot successfully built" in res2.stdout

    with sqlite3.connect(db_path) as conn:
        count_2 = conn.execute("SELECT count(*) FROM retraction_records").fetchone()[0]
        distinct_ids_2 = conn.execute(
            "SELECT count(DISTINCT rw_record_id) FROM retraction_records"
        ).fetchone()[0]

    manifest_2 = json.loads(manifest_path.read_text(encoding="utf-8"))

    # Assert exact idempotency
    assert count_1 == count_2, f"Row count changed after repeated ingest: {count_1} != {count_2}"
    assert distinct_ids_1 == distinct_ids_2, "Distinct IDs changed across ingest runs"
    assert count_2 == distinct_ids_2, "Duplicate records were introduced during re-ingest"
    assert manifest_1["sha256"] == manifest_2["sha256"], (
        "Database checksum differed across identical ingest runs"
    )
    assert manifest_1["rows_count"] == manifest_2["rows_count"]

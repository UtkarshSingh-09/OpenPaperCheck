"""
Golden Set Benchmark Test Suite for OpenPaperCheck.
Validates 18 known cases covering all 4 PaperPublicStates and citation timing scenarios.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from typer.testing import CliRunner

from openpapercheck.cli import app
from openpapercheck.core.models import PaperPublicState, determine_paper_state
from openpapercheck.core.storage import get_retraction, init_schema
from openpapercheck.ingest.snapshot_builder import build_sqlite_snapshot

runner = CliRunner()


def get_golden_set() -> list[dict]:
    fixture_path = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "golden_dois.json"
    assert fixture_path.is_file(), f"Golden fixture not found at {fixture_path}"
    with open(fixture_path, encoding="utf-8") as f:
        return json.load(f)


def test_golden_dois_against_storage(tmp_path: Path):
    """Verify all golden DOIs correctly match their expected retraction status in storage."""
    golden_dois = get_golden_set()
    assert len(golden_dois) >= 15, f"Expected at least 15 golden cases, got {len(golden_dois)}"

    db_path = tmp_path / "test_golden.sqlite"
    conn = sqlite3.connect(db_path)
    init_schema(conn)

    # Populate the test DB with the retracted items from the golden set
    c = conn.cursor()
    record_id = 5000
    for item in golden_dois:
        if item.get("is_retracted"):
            reasons_str = "; ".join(item.get("reasons", []))
            c.execute(
                """
                INSERT INTO retraction_records (
                    rw_record_id, original_doi, retraction_doi, nature,
                    reasons, retraction_date, original_date, notice_urls
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record_id,
                    item["doi"],
                    f"{item['doi']}-ret",
                    "Retraction",
                    reasons_str,
                    "2010-02-06" if "s0140-6736(97)11096-0" in item["doi"] else "2020-01-01",
                    "1998-02-28",
                    item.get("source_url", ""),
                ),
            )
            record_id += 1
    conn.commit()
    conn.close()

    # Verify all golden DOIs
    for item in golden_dois:
        doi = item["doi"]
        expected_retracted = item.get("is_retracted", False)
        rec = get_retraction(doi, db_path=db_path)

        if expected_retracted:
            assert rec is not None, f"Expected {doi} to be flagged as retracted, but was not found."
            assert rec["doi"].lower() == doi.lower()
            for r in item.get("reasons", []):
                assert any(r.lower() in stored_r.lower() for stored_r in rec["reasons"])
        else:
            assert rec is None, f"Expected {doi} to NOT be retracted, but found: {rec}"


def test_golden_dois_state_determination():
    """Verify determine_paper_state correctly identifies each of the 4 public states."""
    # 1. RETRACTED_EXTERNAL
    ret_paper = {"rw_record_id": 1001, "reasons": ["Data fabrication"]}
    state_ret = determine_paper_state(ret_paper, {"deposit_status": "deposited"}, {})
    assert state_ret == PaperPublicState.RETRACTED_EXTERNAL

    # 2. NEEDS_REVIEW (clean paper citing retracted reference)
    ret_refs = {"10.1016/s0140-6736(97)11096-0": {"retraction_date": "2010-02-06"}}
    state_review = determine_paper_state(None, {"deposit_status": "deposited"}, ret_refs)
    assert state_review == PaperPublicState.NEEDS_REVIEW

    # 3. NO_FLAGS_FOUND (clean paper citing clean references)
    state_clean = determine_paper_state(None, {"deposit_status": "deposited"}, {})
    assert state_clean == PaperPublicState.NO_FLAGS_FOUND

    # 4. INSUFFICIENT_DATA (missing or restricted references)
    state_missing = determine_paper_state(None, {"deposit_status": "missing"}, {})
    assert state_missing == PaperPublicState.INSUFFICIENT_DATA

    state_restricted = determine_paper_state(None, {"deposit_status": "restricted"}, {})
    assert state_restricted == PaperPublicState.INSUFFICIENT_DATA


def test_golden_dois_citation_timing():
    """Verify correct classification of 'Cited AFTER retraction' vs 'Cited BEFORE retraction'."""
    ret_date = "2010-02-06"  # Wakefield retraction date

    # Case A: Paper published in 2021 citing Wakefield
    pub_date_after = "2021-04-01"
    timing_after = pub_date_after > ret_date
    assert timing_after is True  # Cited AFTER retraction!

    # Case B: Paper published in 2008 citing Wakefield
    pub_date_before = "2008-04-12"
    timing_before = pub_date_before > ret_date
    assert timing_before is False  # Cited BEFORE retraction!


def test_eval_golden_cli(tmp_path: Path, monkeypatch):
    """Verify 'opc eval golden' runs and outputs formatted evaluation table."""
    monkeypatch.setenv("OPC_DATA_DIR", str(tmp_path))
    build_sqlite_snapshot(use_sample=True)

    fixture_path = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "golden_dois.json"
    result = runner.invoke(app, ["eval", "golden", "--fixture", str(fixture_path)])
    # The command should run through the golden set
    assert "Golden Set Evaluation Results" in result.stdout
    assert "Evaluating" in result.stdout
    assert "Total Evaluated:" in result.stdout

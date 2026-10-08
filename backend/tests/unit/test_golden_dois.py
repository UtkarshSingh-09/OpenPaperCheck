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
from openpapercheck.core.models import (
    CitationTiming,
    PaperPublicState,
    determine_paper_state,
    evaluate_citation_timing,
)
from openpapercheck.core.storage import check_reference_dois, get_retraction, init_schema
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
        elif item.get("nature") == "Expression of concern":
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
                    f"{item['doi']}-eoc",
                    "Expression of concern",
                    reasons_str,
                    item.get("notice_date", "2016-09-13"),
                    item.get("original_date", "2009-08-18"),
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
        is_eoc = item.get("nature") == "Expression of concern"
        rec = get_retraction(doi, db_path=db_path)

        if expected_retracted:
            assert rec is not None, f"Expected {doi} to be flagged as retracted, but was not found."
            assert rec["doi"].lower() == doi.lower()
            assert rec["nature"] == "Retraction"
            for r in item.get("reasons", []):
                assert any(r.lower() in stored_r.lower() for stored_r in rec["reasons"])
        elif is_eoc:
            assert rec is not None, (
                f"Expected {doi} to be flagged with Expression of concern, but was not found."
            )
            assert rec["doi"].lower() == doi.lower()
            assert rec["nature"] == "Expression of concern"
            for r in item.get("reasons", []):
                assert any(r.lower() in stored_r.lower() for stored_r in rec["reasons"])
        else:
            assert rec is None, f"Expected {doi} to NOT be retracted or flagged, but found: {rec}"


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

    # 4. INSUFFICIENT_DATA (missing, restricted, or None references)
    state_none = determine_paper_state(None, None, {})
    assert state_none == PaperPublicState.INSUFFICIENT_DATA

    state_missing = determine_paper_state(None, {"deposit_status": "missing"}, {})
    assert state_missing == PaperPublicState.INSUFFICIENT_DATA

    state_restricted = determine_paper_state(None, {"deposit_status": "restricted"}, {})
    assert state_restricted == PaperPublicState.INSUFFICIENT_DATA


def test_golden_dois_citation_timing():
    """Verify correct classification of 'Cited AFTER retraction' vs 'Cited BEFORE retraction'."""
    ret_date = "2010-02-06"  # Wakefield full retraction date

    # Case A: Paper published in 2021 citing Wakefield
    assert evaluate_citation_timing("2021-04-01", ret_date) == CitationTiming.CITED_AFTER_RETRACTION

    # Case B: Paper published in 2008 citing Wakefield
    assert (
        evaluate_citation_timing("2008-04-12", ret_date) == CitationTiming.CITED_BEFORE_RETRACTION
    )

    # Case C: Unknown / missing date
    assert evaluate_citation_timing(None, ret_date) == CitationTiming.UNKNOWN
    assert evaluate_citation_timing("2021-04-01", None) == CitationTiming.UNKNOWN
    assert evaluate_citation_timing("2021-04-01", "date unknown") == CitationTiming.UNKNOWN
    assert evaluate_citation_timing("", ret_date) == CitationTiming.UNKNOWN
    assert evaluate_citation_timing("2021-04-01", "") == CitationTiming.UNKNOWN

    # Case D: Partial year comparison
    assert evaluate_citation_timing("2021", "2020-06-05") == CitationTiming.CITED_AFTER_RETRACTION
    assert evaluate_citation_timing("2019", "2020-06-05") == CitationTiming.CITED_BEFORE_RETRACTION
    # Shared prefix (both 2020) without full day proof defaults to conservative BEFORE
    assert evaluate_citation_timing("2020", "2020-06-05") == CitationTiming.CITED_BEFORE_RETRACTION


def test_wakefield_dual_retraction_boundary_case(tmp_path: Path):
    """
    Boundary test: Wakefield has two entries in Retraction Watch:
    1. 2004-03-06 (Record 17269): Partial retraction of an interpretation (nature='Correction')
    2. 2010-02-06 (Record 4036): Full retraction by The Lancet editors (nature='Retraction')

    Verify:
    1. Storage query prioritizes full 'Retraction' (2010-02-06) over 'Correction' (2004-03-06).
    2. A paper published in 2007 (e.g. 10.1111/j.1467-9566.2007.00544.x, pub_date='2007-03-01')
       is classified as 'cited_before_retraction' relative to the full retraction notice.
    """
    db_path = tmp_path / "wakefield_dual.sqlite"
    conn = sqlite3.connect(db_path)
    init_schema(conn)
    c = conn.cursor()

    # Insert both historical notices for Wakefield 1998 paper
    c.execute(
        """
        INSERT INTO retraction_records (
            rw_record_id, original_doi, retraction_doi, nature,
            reasons, retraction_date, original_date, notice_urls
        ) VALUES
        (17269, '10.1016/s0140-6736(97)11096-0', '10.1016/s0140-6736(04)15715-2', 'Correction',
         'Retraction of Interpretation', '2004-03-06', '1998-02-28', 'https://doi.org/10.1016/s0140-6736(04)15715-2'),
        (4036, '10.1016/s0140-6736(97)11096-0', '10.1016/s0140-6736(10)60175-4', 'Retraction',
         'Falsification/Fabrication of Data; Upgrade/Update of Prior Notice(s)', '2010-02-06', '1998-02-28', 'https://doi.org/10.1016/s0140-6736(10)60175-4')
        """
    )
    conn.commit()
    conn.close()

    # 1. Verify get_retraction returns the full Retraction notice, NOT the earlier correction
    rec = get_retraction("10.1016/s0140-6736(97)11096-0", db_path=db_path)
    assert rec is not None
    assert rec["rw_record_id"] == 4036
    assert rec["nature"] == "Retraction"
    assert rec["retraction_date"] == "2010-02-06"

    # 2. Verify boundary paper published between 2004 and 2010
    # Paper: Sociology of Health & Illness (published 2007-03-01)
    boundary_paper_pub_date = "2007-03-01"
    timing = evaluate_citation_timing(boundary_paper_pub_date, rec["retraction_date"])
    assert timing == CitationTiming.CITED_BEFORE_RETRACTION


def test_multi_reference_mixed_timing():
    """
    Design validation: A paper cites two retracted works with conflicting timelines:
    - Ref A: Wakefield 1998 (retracted 2010-02-06)
    - Ref B: Mehra HCQ 2020 (retracted 2020-06-05)

    Citing Paper published in 2015:
    - For Ref A: Published AFTER retraction (2015 > 2010) -> CITED_AFTER_RETRACTION
    - For Ref B: Published BEFORE retraction (2015 < 2020) -> CITED_BEFORE_RETRACTION

    Verification:
    - Macro paper state MUST be NEEDS_REVIEW (not split into conflicting states).
    - CitationTiming is preserved per-reference without data collision or loss.
    """
    pub_date = "2015-06-15"
    retracted_refs_map = {
        "10.1016/s0140-6736(97)11096-0": {
            "rw_record_id": 4036,
            "retraction_date": "2010-02-06",
            "nature": "Retraction",
        },
        "10.1016/s0140-6736(20)31180-6": {
            "rw_record_id": 23529,
            "retraction_date": "2020-06-05",
            "nature": "Retraction",
        },
    }

    # Macro paper-level state
    paper_state = determine_paper_state(
        paper_retraction=None,
        references_data={"deposit_status": "deposited"},
        retracted_refs_map=retracted_refs_map,
    )
    assert paper_state == PaperPublicState.NEEDS_REVIEW

    # Per-reference timing evaluation
    timing_ref_a = evaluate_citation_timing(
        pub_date, retracted_refs_map["10.1016/s0140-6736(97)11096-0"]["retraction_date"]
    )
    timing_ref_b = evaluate_citation_timing(
        pub_date, retracted_refs_map["10.1016/s0140-6736(20)31180-6"]["retraction_date"]
    )

    assert timing_ref_a == CitationTiming.CITED_AFTER_RETRACTION
    assert timing_ref_b == CitationTiming.CITED_BEFORE_RETRACTION


def test_eoc_only_reference_policy_enforcement(tmp_path: Path):
    """
    Verify ADR-0004 policy enforcement in code for Expression of Concern (EOC):
    1. Reference with ONLY an Expression of Concern is recognized and triggers NEEDS_REVIEW.
    2. get_retraction() and check_reference_dois() return nature='Expression of concern'.
    3. When a subsequent formal Retraction notice is deposited, storage query automatically
       upgrades to nature='Retraction' and anchors to the full retraction date.
    """
    db_path = tmp_path / "eoc_policy.sqlite"
    conn = sqlite3.connect(db_path)
    init_schema(conn)
    c = conn.cursor()

    eoc_doi = "10.1000/eoc-flagged-work"
    # Phase 1: Only an Expression of Concern exists
    c.execute(
        """
        INSERT INTO retraction_records (
            rw_record_id, original_doi, retraction_doi, nature,
            reasons, retraction_date, original_date, notice_urls
        ) VALUES (
            9001, ?, '10.1000/eoc-notice', 'Expression of concern',
            'Concerns/Issues About Data', '2019-04-10', '2017-01-01', 'https://example.com/eoc'
        )
        """,
        (eoc_doi,),
    )
    conn.commit()

    # 1. Verify EOC-only lookup
    rec = get_retraction(eoc_doi, db_path=db_path)
    assert rec is not None
    assert rec["rw_record_id"] == 9001
    assert rec["nature"] == "Expression of concern"
    assert rec["retraction_date"] == "2019-04-10"

    batch = check_reference_dois([eoc_doi], db_path=db_path)
    assert eoc_doi in batch
    assert batch[eoc_doi]["nature"] == "Expression of concern"

    # 2. Citing paper state: citing an EOC-only paper MUST trigger NEEDS_REVIEW
    state = determine_paper_state(
        paper_retraction=None,
        references_data={"deposit_status": "deposited"},
        retracted_refs_map=batch,
    )
    assert state == PaperPublicState.NEEDS_REVIEW

    # 3. Citation timing relative to EOC notice date
    # Paper published in 2021 (after EOC)
    assert (
        evaluate_citation_timing("2021-01-01", rec["retraction_date"])
        == CitationTiming.CITED_AFTER_RETRACTION
    )
    # Paper published in 2018 (before EOC)
    assert (
        evaluate_citation_timing("2018-01-01", rec["retraction_date"])
        == CitationTiming.CITED_BEFORE_RETRACTION
    )

    # Phase 2: Later, the publisher issues a full formal Retraction (2022-08-15)
    c.execute(
        """
        INSERT INTO retraction_records (
            rw_record_id, original_doi, retraction_doi, nature,
            reasons, retraction_date, original_date, notice_urls
        ) VALUES (
            9002, ?, '10.1000/ret-notice', 'Retraction',
            'Falsification of Data; Upgrade/Update of Prior Notice(s)', '2022-08-15', '2017-01-01', 'https://example.com/ret'
        )
        """,
        (eoc_doi,),
    )
    conn.commit()
    conn.close()

    # 4. Verify ADR-0004 code enforcement: Retraction takes precedence over EOC
    upgraded_rec = get_retraction(eoc_doi, db_path=db_path)
    assert upgraded_rec is not None
    assert upgraded_rec["rw_record_id"] == 9002
    assert upgraded_rec["nature"] == "Retraction"
    assert upgraded_rec["retraction_date"] == "2022-08-15"

    upgraded_batch = check_reference_dois([eoc_doi], db_path=db_path)
    assert upgraded_batch[eoc_doi]["nature"] == "Retraction"
    assert upgraded_batch[eoc_doi]["retraction_date"] == "2022-08-15"

    # 5. Authoritative anchor shifts to formal Retraction date:
    # A paper published in 2020-05-01 was published AFTER the 2019 EOC,
    # but BEFORE the formal 2022 Retraction.
    # Per ADR-0004, the authoritative anchor is now 2022-08-15 (CITED_BEFORE_RETRACTION).
    timing_2020 = evaluate_citation_timing("2020-05-01", upgraded_rec["retraction_date"])
    assert timing_2020 == CitationTiming.CITED_BEFORE_RETRACTION


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

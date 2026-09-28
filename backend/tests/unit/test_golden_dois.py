import json
import sqlite3
from pathlib import Path

from openpapercheck.core.storage import get_retraction, init_schema


def test_golden_dois_against_storage(tmp_path: Path):
    fixture_path = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "golden_dois.json"
    assert fixture_path.is_file(), f"Golden fixture not found at {fixture_path}"

    with open(fixture_path, encoding="utf-8") as f:
        golden_dois = json.load(f)

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
                    "2020-01-01",
                    "2010-01-01",
                    item.get("source_url", ""),
                ),
            )
            record_id += 1
    conn.commit()
    conn.close()

    # Now verify all golden DOIs
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

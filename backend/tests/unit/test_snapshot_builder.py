"""
Unit tests for Retraction Watch Snapshot Builder and Ingestion Engine.
Tests date normalization (MM/DD/YYYY vs ISO), allow-list enforcement,
CSV parsing resilience, and SQLite snapshot generation.
"""

from __future__ import annotations

import csv
import gzip
import json
import sqlite3
from pathlib import Path

from openpapercheck.ingest.snapshot_builder import (
    build_sqlite_snapshot,
    normalize_date,
)

# --- Date Normalization Tests ---


def test_normalize_date_us_format():
    """Verify US MM/DD/YYYY format is correctly parsed to ISO YYYY-MM-DD."""
    assert normalize_date("2/9/2024 0:00") == "2024-02-09"
    assert normalize_date("12/23/2020 0:00") == "2020-12-23"
    assert normalize_date("1/5/2019") == "2019-01-05"


def test_normalize_date_iso_format():
    """Verify ISO format YYYY-MM-DD is preserved."""
    assert normalize_date("2010-02-06") == "2010-02-06"
    assert normalize_date("1998-02-28 12:00") == "1998-02-28"


def test_normalize_date_ambiguous_month_day():
    """
    Verify ambiguous dates where both components are <= 12.
    Retraction Watch standard is MM/DD/YYYY:
    3/5/2020 means March 5, 2020 (NOT May 3).
    """
    assert normalize_date("3/5/2020") == "2020-03-05"
    assert normalize_date("11/12/2018") == "2018-11-12"
    assert normalize_date("5/3/2021") == "2021-05-03"


def test_normalize_date_edge_cases():
    """Verify edge cases like None, empty strings, null, and invalid tokens."""
    assert normalize_date(None) is None
    assert normalize_date("") is None
    assert normalize_date("   ") is None
    assert normalize_date("null") is None
    assert normalize_date("NULL") is None
    assert normalize_date("None") is None
    assert normalize_date("unknown") == "unknown"
    # Malformed non-numeric date components (ValueError paths)
    assert normalize_date("aa/bb/cccc") == "aa/bb/cccc"
    assert normalize_date("yyyy-mm-dd") == "yyyy-mm-dd"


# --- CSV Ingestion & Allow-List Tests ---


def test_build_sqlite_snapshot_from_csv(tmp_path: Path, monkeypatch):
    """
    Verify building snapshot from a raw CSV file:
    - Parses allow-listed columns
    - Drops banned demographic/identity columns (Author, Institution, Country, Subject)
    - Normalizes dates to ISO
    - Creates indices and manifest
    """
    monkeypatch.setenv("OPC_DATA_DIR", str(tmp_path))

    # Create synthetic dirty CSV with banned columns
    csv_file = tmp_path / "test_retractions.csv"
    headers = [
        "Record ID",
        "Title",
        "Subject",
        "Institution",
        "Journal",
        "Publisher",
        "Country",
        "Author",
        "URLS",
        "ArticleType",
        "RetractionDate",
        "RetractionDOI",
        "RetractionPubMedID",
        "OriginalPaperDate",
        "OriginalPaperDOI",
        "OriginalPaperPubMedID",
        "RetractionNature",
        "Reason",
        "Paywalled",
        "Notes",
    ]

    rows = [
        [
            "10001",
            "Study on Quantum Effects",
            "(PHY) Physics",
            "University of Example, Physics Dept",
            "Nature Physics",
            "Springer Nature",
            "United States",
            "John Doe; Jane Smith",
            "https://retractionwatch.com/notice/1",
            "Research Article",
            "4/15/2021 0:00",
            "10.1038/retraction-1",
            "12345678",
            "6/10/2018 0:00",
            "10.1038/s41567-018-0001-x",
            "87654321",
            "Retraction",
            "Falsification of Data; Error in Analyses",
            "No",
            "Notice issued by editors",
        ],
        [
            "10002",
            "Another Study with Ambiguous Date",
            "(BIO) Biology",
            "Institute of Science",
            "Cell",
            "Elsevier",
            "United Kingdom",
            "Alice Brown",
            "https://retractionwatch.com/notice/2",
            "Research Article",
            "3/5/2020 0:00",  # March 5, 2020
            "10.1016/retraction-2",
            "0",
            "11/12/2017 0:00",  # Nov 12, 2017
            "10.1016/j.cell.2017.0002-y",
            "0",
            "Retraction",
            "Unreliable Results",
            "No",
            "",
        ],
        [
            "not-an-id",  # Invalid record ID - should be skipped safely
            "Malformed Row",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "1/1/2020",
            "",
            "",
            "1/1/2019",
            "10.1000/malformed",
            "",
            "Retraction",
            "",
            "",
            "",
        ],
    ]

    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)

    # Build snapshot
    db_path = build_sqlite_snapshot(csv_path=csv_file)
    assert db_path.is_file()

    # Verify SQLite schema
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(retraction_records);")
    col_info = cursor.fetchall()
    col_names = [c[1].lower() for c in col_info]

    # Verify STRICT lack of banned columns
    banned = {"author", "institution", "country", "subject", "affiliation", "nationality"}
    for b in banned:
        assert b not in col_names, f"Banned column '{b}' found in SQLite schema!"

    # Verify inserted records
    cursor.execute(
        "SELECT rw_record_id, original_doi, retraction_date, original_date, reasons FROM retraction_records ORDER BY rw_record_id;"
    )
    records = cursor.fetchall()
    conn.close()

    assert len(records) == 2, f"Expected 2 valid records, got {len(records)}"

    # Check record 1
    r1 = records[0]
    assert r1[0] == 10001
    assert r1[1] == "10.1038/s41567-018-0001-x"
    assert r1[2] == "2021-04-15"  # Normalized from 4/15/2021
    assert r1[3] == "2018-06-10"  # Normalized from 6/10/2018

    # Check record 2
    r2 = records[1]
    assert r2[0] == 10002
    assert r2[1] == "10.1016/j.cell.2017.0002-y"
    assert r2[2] == "2020-03-05"  # Normalized from 3/5/2020
    assert r2[3] == "2017-11-12"  # Normalized from 11/12/2017

    # Verify manifest.json
    manifest_file = tmp_path / "manifest.json"
    assert manifest_file.is_file()
    with open(manifest_file, encoding="utf-8") as f:
        manifest = json.load(f)
    assert manifest["rows_count"] == 2
    assert "sha256" in manifest

    # Verify compressed archive
    gz_file = tmp_path / "retraction_records.sqlite.gz"
    assert gz_file.is_file()
    with gzip.open(gz_file, "rb") as f_in:
        decompressed = f_in.read(100)
    assert decompressed.startswith(b"SQLite format 3")


def test_snapshot_builder_batch_flush(tmp_path: Path, monkeypatch):
    """Verify that snapshot builder flushes batches exceeding 5000 rows."""
    monkeypatch.setenv("OPC_DATA_DIR", str(tmp_path))

    large_csv = tmp_path / "large_raw.csv"
    headers = [
        "Record ID",
        "OriginalPaperDOI",
        "RetractionDOI",
        "RetractionNature",
        "Reason",
        "RetractionDate",
        "OriginalPaperDate",
        "URLS",
    ]
    with open(large_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for i in range(5005):
            writer.writerow(
                [
                    i + 1,
                    f"10.1000/batch-doi-{i}",
                    f"10.1000/ret-doi-{i}",
                    "Retraction",
                    "Falsification of Data",
                    "2020-01-01",
                    "2018-01-01",
                    "https://example.com/notice",
                ]
            )

    sqlite_path = build_sqlite_snapshot(csv_path=large_csv)
    assert sqlite_path.is_file()

    conn = sqlite3.connect(sqlite_path)
    c = conn.cursor()
    c.execute("SELECT count(*) FROM retraction_records;")
    count = c.fetchone()[0]
    conn.close()
    assert count == 5005

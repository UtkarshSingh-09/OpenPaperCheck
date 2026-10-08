"""
Fairness deny-list unit tests: Enforces non-negotiable rule that author,
institution, and country are NEVER ingested, stored, or profiled.
Tests both sample builds and production SQLite snapshot.
"""

from __future__ import annotations

import sqlite3

from openpapercheck.core.storage import get_snapshot_path, has_snapshot
from openpapercheck.ingest.snapshot_builder import ALLOW_LISTED_COLS, build_sqlite_snapshot

BANNED_COLUMNS = {
    "author",
    "authors",
    "institution",
    "institutions",
    "country",
    "countries",
    "affiliation",
    "affiliations",
    "nationality",
    "subject",
}


def test_allowlist_does_not_contain_people_features():
    """Verify that author, institution, and country are excluded from allowlist."""
    for col in ALLOW_LISTED_COLS:
        assert col.lower() not in BANNED_COLUMNS, (
            f"Banned column '{col}' found in ALLOW_LISTED_COLS!"
        )


def test_sqlite_schema_has_no_people_columns(tmp_path, monkeypatch):
    """Verify that compiled SQLite database contains no people columns."""
    monkeypatch.setenv("OPC_DATA_DIR", str(tmp_path))
    db_path = build_sqlite_snapshot(use_sample=True)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(retraction_records);")
    columns = [row[1].lower() for row in cursor.fetchall()]
    conn.close()

    for col in columns:
        assert col not in BANNED_COLUMNS, (
            f"Banned column '{col}' exists in retraction_records table!"
        )


def test_production_snapshot_fairness():
    """Verify that local production SQLite snapshot strictly contains no banned columns."""
    if not has_snapshot():
        return

    db_path = get_snapshot_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(retraction_records);")
    columns = [row[1].lower() for row in cursor.fetchall()]

    # Verify column count and names
    for col in columns:
        assert col not in BANNED_COLUMNS, f"Banned column '{col}' in production snapshot!"

    # Ensure only 8 allowed columns exist in the table
    allowed_db_columns = {
        "rw_record_id",
        "original_doi",
        "retraction_doi",
        "nature",
        "reasons",
        "retraction_date",
        "original_date",
        "notice_urls",
    }
    assert set(columns) == allowed_db_columns, (
        f"Unexpected columns in production snapshot: {columns}"
    )
    conn.close()

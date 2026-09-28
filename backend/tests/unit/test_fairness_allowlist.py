"""
Fairness deny-list unit tests: Enforces non-negotiable rule that author,
institution, and country are NEVER ingested, stored, or profiled.
"""

from __future__ import annotations

import sqlite3

from openpapercheck.ingest.snapshot_builder import ALLOW_LISTED_COLS, build_sqlite_snapshot


def test_allowlist_does_not_contain_people_features():
    """Verify that author, institution, and country are excluded from allowlist."""
    banned = {"author", "institution", "country", "affiliation", "nationality"}
    for col in ALLOW_LISTED_COLS:
        assert col.lower() not in banned, f"Banned column '{col}' found in ALLOW_LISTED_COLS!"


def test_sqlite_schema_has_no_people_columns(tmp_path, monkeypatch):
    """Verify that compiled SQLite database contains no people columns."""
    monkeypatch.setenv("OPC_DATA_DIR", str(tmp_path))
    db_path = build_sqlite_snapshot(use_sample=True)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(retraction_records);")
    columns = [row[1].lower() for row in cursor.fetchall()]
    conn.close()

    banned = {"author", "institution", "country", "affiliation", "nationality"}
    for col in columns:
        assert col not in banned, f"Banned column '{col}' exists in retraction_records table!"

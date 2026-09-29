"""
SQLite Snapshot Storage for OpenPaperCheck CLI.

Uses ONLY standard library sqlite3 for fast, zero-dependency lookups.
"""

from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path
from typing import Any

from openpapercheck.core.doi import normalize_doi

def get_data_dir() -> Path:
    """Return data directory, creating it if necessary."""
    data_dir = Path(os.environ.get("OPC_DATA_DIR") or Path.home() / ".cache" / "openpapercheck")
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def get_snapshot_file() -> Path:
    """Return path to snapshot file in data directory."""
    return get_data_dir() / "retraction_records.sqlite"


def get_manifest_file() -> Path:
    """Return path to manifest file in data directory."""
    return get_data_dir() / "manifest.json"


# Backwards compatibility aliases
DEFAULT_DIR = Path(os.environ.get("OPC_DATA_DIR") or Path.home() / ".cache" / "openpapercheck")
SNAPSHOT_FILE = DEFAULT_DIR / "retraction_records.sqlite"
MANIFEST_FILE = DEFAULT_DIR / "manifest.json"


def init_schema(conn: sqlite3.Connection) -> None:
    """Initialize standard retraction_records table and indices."""
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS retraction_records (
            rw_record_id INTEGER PRIMARY KEY,
            original_doi TEXT,
            retraction_doi TEXT,
            nature TEXT NOT NULL,
            reasons TEXT,
            retraction_date TEXT,
            original_date TEXT,
            notice_urls TEXT
        );
        """
    )
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_rr_original_doi ON retraction_records (lower(original_doi));
        """
    )
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_rr_nature ON retraction_records (nature);
        """
    )
    conn.commit()


def get_snapshot_path() -> Path:
    """Return path to local SQLite snapshot."""
    # Check if local development snapshot exists first
    local_dev = Path("data/snapshots/retraction_records.sqlite")
    if local_dev.is_file() and not os.environ.get("OPC_DATA_DIR"):
        return local_dev
    return get_snapshot_file()


def has_snapshot() -> bool:
    """Return True if a readable SQLite snapshot exists."""
    return get_snapshot_path().is_file()


def get_manifest() -> dict[str, Any] | None:
    """Load the current snapshot manifest if available."""
    manifest_path = get_manifest_file()
    if not manifest_path.is_file():
        return None
    try:
        with open(manifest_path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def get_connection(readonly: bool = True, db_path: Path | None = None) -> sqlite3.Connection:
    """Open a connection to the SQLite snapshot."""
    path = db_path or get_snapshot_path()
    if not path.is_file():
        raise FileNotFoundError(
            f"No retraction database snapshot found at {path}. "
            "Please run 'opc update' to download the latest verified snapshot."
        )

    uri = f"file:{path.as_posix()}?mode=ro" if readonly else path.as_posix()
    conn = sqlite3.connect(uri, uri=readonly)
    conn.row_factory = sqlite3.Row
    return conn


def get_retraction(doi: str, db_path: Path | None = None) -> dict[str, Any] | None:
    """
    Look up a DOI in the local retraction snapshot.

    Returns:
        Dict with record details if retracted/flagged, or None.
    """
    canonical = normalize_doi(doi)
    if not canonical:
        return None

    try:
        with get_connection(readonly=True, db_path=db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT rw_record_id, original_doi, nature, reasons,
                       retraction_date, original_date, notice_urls
                FROM retraction_records
                WHERE lower(original_doi) = ?
                ORDER BY 
                    CASE nature
                        WHEN 'Retraction' THEN 1
                        WHEN 'Expression of concern' THEN 2
                        WHEN 'Correction' THEN 3
                        WHEN 'Reinstatement' THEN 4
                        ELSE 5
                    END,
                    retraction_date DESC
                LIMIT 1
                """,
                (canonical,),
            )
            row = cursor.fetchone()
            if not row:
                return None

            reasons_raw = row["reasons"]
            reasons_list = (
                [r.strip() for r in reasons_raw.split(";") if r.strip()] if reasons_raw else []
            )

            return {
                "rw_record_id": row["rw_record_id"],
                "doi": row["original_doi"],
                "nature": row["nature"],
                "reasons": reasons_list,
                "retraction_date": row["retraction_date"],
                "original_date": row["original_date"],
                "notice_urls": [row["notice_urls"]] if row["notice_urls"] else [],
            }
    except FileNotFoundError:
        raise
    except Exception:
        # Gracefully handle query errors
        return None


def check_reference_dois(dois: list[str], db_path: Path | None = None) -> dict[str, dict[str, Any]]:
    """
    Batch check a list of reference DOIs against the local retraction dataset.

    Returns:
        Mapping of {doi: retraction_info} for DOIs that have retractions recorded.
        Prioritizes full 'Retraction' notices over earlier 'Correction' or 'Expression of concern'.
    """
    cleaned_dois = [normalize_doi(d) for d in dois if d]
    valid_dois = [d for d in cleaned_dois if d is not None]
    if not valid_dois:
        return {}

    retracted: dict[str, dict[str, Any]] = {}
    try:
        with get_connection(readonly=True, db_path=db_path) as conn:
            cursor = conn.cursor()
            # SQLite parameters limit is safely handled by chunking
            chunk_size = 500
            for i in range(0, len(valid_dois), chunk_size):
                chunk = valid_dois[i : i + chunk_size]
                placeholders = ",".join("?" for _ in chunk)
                query = f"""
                    SELECT rw_record_id, original_doi, nature, reasons,
                           retraction_date, original_date
                    FROM retraction_records
                    WHERE lower(original_doi) IN ({placeholders})
                    ORDER BY 
                        CASE nature
                            WHEN 'Retraction' THEN 1
                            WHEN 'Expression of concern' THEN 2
                            WHEN 'Correction' THEN 3
                            WHEN 'Reinstatement' THEN 4
                            ELSE 5
                        END,
                        retraction_date DESC
                """
                cursor.execute(query, chunk)
                for row in cursor.fetchall():
                    doi_key = row["original_doi"].lower()
                    if doi_key in retracted:
                        continue  # Already captured higher-priority notice
                    reasons_raw = row["reasons"]
                    reasons_list = (
                        [r.strip() for r in reasons_raw.split(";") if r.strip()]
                        if reasons_raw
                        else []
                    )
                    retracted[doi_key] = {
                        "rw_record_id": row["rw_record_id"],
                        "nature": row["nature"],
                        "reasons": reasons_list,
                        "retraction_date": row["retraction_date"],
                        "original_date": row["original_date"],
                    }
    except Exception:
        pass

    return retracted

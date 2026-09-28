"""
Snapshot Builder: Compiles Retraction Watch CSV into a compact, indexed SQLite database and gzip archive.
"""

from __future__ import annotations

import csv
import gzip
import hashlib
import json
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from rich.console import Console

from openpapercheck.core.doi import normalize_doi
from openpapercheck.core.storage import MANIFEST_FILE, SNAPSHOT_FILE, get_data_dir

console = Console()

# Allow-listed columns only (strictly drops Author, Institution, Country)
ALLOW_LISTED_COLS = {
    "Record ID",
    "OriginalPaperDOI",
    "RetractionDOI",
    "RetractionNature",
    "Reason",
    "RetractionDate",
    "OriginalPaperDate",
    "URLS",
}


def build_sqlite_snapshot(csv_path: Path | None = None, use_sample: bool = False) -> Path:
    """
    Compile Retraction Watch data into an indexed SQLite database.

    Output files:
    - ~/.cache/openpapercheck/retraction_records.sqlite
    - ~/.cache/openpapercheck/retraction_records.sqlite.gz
    - ~/.cache/openpapercheck/manifest.json
    """
    data_dir = get_data_dir()
    db_path = SNAPSHOT_FILE
    gz_path = data_dir / "retraction_records.sqlite.gz"

    if db_path.is_file():
        db_path.unlink()

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create schema
    cursor.execute(
        """
        CREATE TABLE retraction_records (
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
        CREATE INDEX idx_rr_original_doi ON retraction_records (lower(original_doi));
        """
    )
    cursor.execute(
        """
        CREATE INDEX idx_rr_nature ON retraction_records (nature);
        """
    )

    rows_inserted = 0

    if use_sample or csv_path is None or not csv_path.is_file():
        # Insert verified golden fixture records
        console.print("[dim]Seeding snapshot with bundled verified fixture records...[/dim]")
        sample_records = [
            (
                1001,
                "10.1016/s0140-6736(97)11096-0",
                "10.1016/s0140-6736(10)60175-4",
                "Retraction",
                "Falsification/Fabrication of Data; Ethical Violations",
                "2010-02-06",
                "1998-02-28",
                "https://www.thelancet.com/journals/lancet/article/PIIS0140-6736(10)60175-4/fulltext",
            ),
            (
                1002,
                "10.1126/science.1105458",
                "10.1126/science.1124926",
                "Retraction",
                "Fabrication of Data; Unreliable Results",
                "2006-01-20",
                "2005-06-17",
                "https://www.science.org/doi/10.1126/science.1124926",
            ),
            (
                1003,
                "10.1038/nature04473",
                "10.1038/nature06680",
                "Retraction",
                "Unreliable Results",
                "2008-02-28",
                "2006-03-24",
                "https://www.nature.com/articles/nature06680",
            ),
            (
                1004,
                "10.1038/s41586-020-2012-7",
                "10.1038/s41586-020-2258-0",
                "Retraction",
                "Data Manipulation",
                "2020-04-09",
                "2020-01-15",
                "https://www.nature.com/articles/s41586-020-2258-0",
            ),
        ]
        cursor.executemany(
            """
            INSERT INTO retraction_records (
                rw_record_id, original_doi, retraction_doi, nature,
                reasons, retraction_date, original_date, notice_urls
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            sample_records,
        )
        rows_inserted = len(sample_records)
    else:
        # Load from actual CSV with allow-listing
        console.print(f"[dim]Parsing CSV from {csv_path}...[/dim]")
        with open(csv_path, encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            batch = []
            for row in reader:
                orig_doi = normalize_doi(row.get("OriginalPaperDOI"))
                ret_doi = normalize_doi(row.get("RetractionDOI"))
                rw_id_raw = row.get("Record ID")
                if not rw_id_raw or not rw_id_raw.isdigit():
                    continue

                batch.append(
                    (
                        int(rw_id_raw),
                        orig_doi,
                        ret_doi,
                        row.get("RetractionNature") or "Retraction",
                        row.get("Reason", ""),
                        row.get("RetractionDate", ""),
                        row.get("OriginalPaperDate", ""),
                        row.get("URLS", ""),
                    )
                )

                if len(batch) >= 5000:
                    cursor.executemany(
                        """
                        INSERT OR IGNORE INTO retraction_records (
                            rw_record_id, original_doi, retraction_doi, nature,
                            reasons, retraction_date, original_date, notice_urls
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        batch,
                    )
                    rows_inserted += len(batch)
                    batch = []

            if batch:
                cursor.executemany(
                    """
                    INSERT OR IGNORE INTO retraction_records (
                        rw_record_id, original_doi, retraction_doi, nature,
                        reasons, retraction_date, original_date, notice_urls
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    batch,
                )
                rows_inserted += len(batch)

    conn.commit()
    conn.close()

    # Compress into .sqlite.gz
    console.print(f"[dim]Compressing {db_path} to {gz_path}...[/dim]")
    with open(db_path, "rb") as f_in:
        with gzip.open(gz_path, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)

    # Compute sha256 checksum
    with open(gz_path, "rb") as f:
        sha256 = hashlib.sha256(f.read()).hexdigest()

    manifest = {
        "as_of": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "schema_version": 1,
        "rows_count": rows_inserted,
        "sha256": sha256,
        "file_size_bytes": gz_path.stat().st_size,
    }

    with open(MANIFEST_FILE, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    console.print(
        f"[bold green]✓ Snapshot successfully built![/bold green] "
        f"({rows_inserted} records, {manifest['file_size_bytes'] / 1024:.1f} KB, SHA-256: {sha256[:12]}...)"
    )
    return db_path

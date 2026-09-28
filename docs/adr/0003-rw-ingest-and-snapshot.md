# ADR-0003: Retraction Watch Ingest, Allow-List, and Snapshot Distribution

## Status
Accepted (2026-09-28)

## Context
Retraction Watch publishes its database through Crossref's GitLab repository. The raw CSV contains 20 columns including author names, institutions, and countries.
OpenPaperCheck has a strict ethical non-negotiable: **zero people features**. We must guarantee that author names, institutions, or countries are never stored, indexed, or surfaced.
Furthermore, downloading and parsing the full 15MB+ raw CSV and compiling it into a database on every user machine is slow, wasteful, and error-prone.

## Decision
1. **Column Allow-Listing at Ingest:**
   - The ingest pipeline parses the CSV using an explicit allow-list:
     `{"Record ID", "OriginalPaperDOI", "RetractionDOI", "RetractionNature", "Reason", "RetractionDate", "OriginalPaperDate", "URLS"}`.
   - Any other column (including Author, Institution, Country, Subject) is completely discarded before any row reaches disk or memory storage.
   - A dedicated unit test (`test_fairness_allowlist.py`) and pre-commit check enforce this invariant.
2. **Snapshot Compilation:**
   - A builder script (`opc snapshot build`) creates an indexed SQLite file:
     `retraction_records.sqlite` with indices on `lower(original_doi)` and `nature`.
   - The file is compressed using gzip into `retraction_records.sqlite.gz` (~12–15 MB).
   - A `manifest.json` file is produced containing:
     - `as_of` (ISO UTC date)
     - `schema_version` (integer)
     - `rows_count` (integer)
     - `sha256` (checksum string)
     - `file_size_bytes` (integer)
3. **Distribution Mechanism:**
   - Daily automated GitHub Action workflow runs the ingest and updates the floating release tag `data-latest` on GitHub Releases.
   - The CLI command `opc update` fetches only `manifest.json` (~200 bytes) first. If the local checksum matches, no download occurs. If the checksum differs, it streams and decompresses the gzip archive.
   - A monthly frozen snapshot is archived on Zenodo for permanent DOI citation.

## Consequences
- Guaranteed compliance with fairness ethics.
- Ultra-fast `opc update` without compiling SQLite on user laptops.
- Offline lookups are immediately functional after a single download.

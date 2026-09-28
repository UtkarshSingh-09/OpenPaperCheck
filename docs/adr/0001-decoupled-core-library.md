# ADR-0001: Decoupled Core Library with Zero Heavy Database Dependencies

## Status
Accepted (2026-09-28)

## Context
Initial drafts considered using PostgreSQL and SQLAlchemy across the entire stack. However, requiring PostgreSQL locally creates massive onboarding friction for command-line users (`pip install openpapercheck`). CLI users want an instantaneous, zero-setup answer to: *"Is this DOI or any of its cited works retracted?"*

Furthermore, adding Polars or DuckDB introduces 30–50MB binary wheels for what is fundamentally a simple keyed lookup (`SELECT * FROM retraction_records WHERE original_doi = ?`).

## Decision
1. **Decouple the architecture into two clean tiers:**
   - **Tier 1 (Core & CLI):** `openpapercheck.core` has zero PostgreSQL, FastAPI, or SQLAlchemy dependencies. It relies purely on Python standard library `sqlite3` to query a local indexed snapshot (`retraction_records.sqlite`).
   - **Tier 2 (Server & Web):** FastAPI service runs on PostgreSQL for relational queries, review crowdsourcing, moderation, and consensus computation.
2. **Standard library `sqlite3` for CLI:**
   - Database size is ~15 MB compressed (~40 MB uncompressed) containing ~55,000 retraction records.
   - An index on `lower(original_doi)` guarantees sub-2ms query execution.
   - Zero additional C/C++ compilation or heavy third-party driver dependencies.

## Consequences
- **Positive:** `pip install openpapercheck` remains tiny, lightning fast, cross-platform, and runs completely offline once the snapshot is downloaded.
- **Positive:** Server and CLI share the same data contract and schemas without forcing database dependencies into the pip package.
- **Negative:** Lookups requiring trigram fuzzy matching or complex joins remain server-only (CLI does direct DOI lookups).

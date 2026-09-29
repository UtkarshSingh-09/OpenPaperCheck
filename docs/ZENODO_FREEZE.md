# Zenodo Monthly Freeze Protocol

**Status:** Living Protocol  
**Frequency:** 1st of every month at 00:00 UTC  
**Target:** Zenodo Academic Community Dataset  

---

## 1. Purpose
While GitHub Releases provides daily floating snapshots via `data-latest` for fast CLI updates, academic citations and reproducible scientific studies require an **immutable, persistent DOI**.

On the 1st of each month, a frozen copy of the Retraction Watch SQLite database snapshot and consensus labels is deposited into Zenodo.

---

## 2. Monthly Freeze Checklist

1. **Verify Integrity**:
   ```bash
   opc snapshot build --sample
   make bench
   make check
   ```

2. **Generate Frozen Archive**:
   Compress the database with the month timestamp:
   ```bash
   cp ~/.cache/openpapercheck/retraction_records.sqlite.gz \
      data/snapshots/openpapercheck-retractions-$(date +%Y-%m-01).sqlite.gz
   ```

3. **Compute SHA-256**:
   ```bash
   shasum -a 256 data/snapshots/openpapercheck-retractions-*.sqlite.gz
   ```

4. **Deposit to Zenodo**:
   - Title: `OpenPaperCheck Retraction Database Snapshot (YYYY-MM-01)`
   - Creators: OpenPaperCheck Community
   - License: Creative Commons Attribution 4.0 International (CC-BY 4.0)
   - Keywords: `retractions`, `crossref`, `academic-integrity`, `open-science`
   - Description:
     > Monthly immutable snapshot of the OpenPaperCheck verified retraction database. All personal attributes (authors, institutions, countries) are strictly excluded at ingest to enforce non-profiling fairness.

5. **Log Deposit DOI**:
   Record the new persistent DOI in `docs/licenses/LOG.md`.

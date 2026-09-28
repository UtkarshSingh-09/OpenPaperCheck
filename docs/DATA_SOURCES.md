# DATA_SOURCES.md — Where every fact in OpenPaperCheck comes from

Status: living document · Last verified: 2026-09-28 · Owner: maintainer
Anything marked **VERIFY** must be re-checked on Day 1 and the result written into `brain.md` (Decision log).

---

## 0. Ground rules for data

1. **Retraction status is computed from a local copy of Retraction Watch (RW) data, refreshed nightly.** We do not call an API per reference. A reference list with 80 entries is one SQL join, not 80 HTTP calls.
2. **Two independent retraction sources are merged:** the RW CSV (Crossref GitLab) and Crossref's own `updated-by` / update metadata. They disagree sometimes (see 2.4). We store both and show which source said what.
3. **OpenAlex's `is_retracted` flag is a convenience, not a primary source.** One published study found not every record OpenAlex marked as a retraction was accurate. We log disagreements between OpenAlex and RW/Crossref instead of trusting either blindly.
4. **Every stored fact carries `source`, `source_version` and `fetched_at`.** No orphan facts.
5. **Allow-list columns on ingest.** RW rows contain author, institution and country columns. We drop them at load time. See section 2.5 and the fairness rule in `SIGNALS_AND_ML.md`.
6. **Abstracts are not redistributed.** Crossref says abstracts stay under publisher or author copyright. Our open dataset ships DOIs, labels, signals and derived numbers. It does not ship abstracts. Users re-fetch text themselves.
7. **Respect rate limits by reading response headers, not hard-coding numbers.** Crossref changed its limits on 1 Dec 2025 and reportedly again in July 2026. OpenAlex changed everything in Feb 2026. Numbers in this file will go stale; headers will not.
8. **Log the license of every source in `docs/licenses/LOG.md`** the day it is added (template in section 9).
9. **CLI Data Snapshot Distribution:** Rather than forcing every local user to ingest raw CSVs, a GitHub Action compiles an indexed SQLite snapshot (`retraction_records.sqlite.gz`, ~5MB compressed) and publishes it to a floating `data-latest` release tag with `manifest.json` (`as_of_date`, `schema_version`, `sha256`). `opc update` uses conditional checks against the manifest. Monthly frozen snapshots are archived on Zenodo for permanent scientific citation.
10. **OpenAlex is strictly optional in the CLI:** The CLI functions out of the box with Crossref (polite pool via `mailto:`) and the local SQLite snapshot. OpenAlex is an optional fallback that only activates if an `OPENALEX_API_KEY` is provided.

---

## 1. Source registry (one-page view)

| ID | Source | What we use it for | Access | License / terms | Status |
|---|---|---|---|---|---|
| DS-01 | Retraction Watch database (via Crossref) | Retraction, correction, expression of concern, reinstatement, reasons | Git repo of CSV, updated on working days | Crossref states its metadata is public domain (CC0) apart from abstracts; **VERIFY** the repo's own LICENSE file | Core, v0.1 (Server DB & CLI SQLite snapshot) |
| DS-02 | Crossref REST API | Paper metadata, reference lists, publisher-registered updates | HTTPS, no key, `mailto` for polite pool | Metadata CC0 except abstracts | Core, v0.1 (CLI and Server) |
| DS-03 | OpenAlex API | Optional fallback metadata and references; `is_retracted` cross-check | HTTPS with **API key required** | Data CC0; API is usage-priced | Optional fallback (requires user key) |
| DS-04 | OpenAlex snapshot | Bulk data for ML later | Public S3 bucket, no key | CC0 | Later, v0.4 |
| DS-05 | PubPeer | Discussion links | Site terms restrict automated access; API by request | **Restricted** | Outbound link only until written permission |
| DS-06 | Problematic Paper Screener (PPS) | Inspiration and possible collaboration on tortured-phrase fingerprints | Public website; no bulk license found | **VERIFY**; ask the maintainers | Do not scrape |
| DS-07 | Paper-mill research datasets (Zenodo etc.) | Seed examples for signals and ML | Download | Per-dataset | Case by case, v0.3+ |
| DS-08 | PubMed E-utilities | PMID to DOI mapping, if needed | HTTPS | NCBI usage policy, **VERIFY** | Optional |
| DS-09 | Semantic Scholar API | Optional second opinion on references | Key needed, low default limits | **VERIFY** | Optional, not planned |

---

## 2. Retraction Watch via Crossref (DS-01)

### 2.1 What it is
Crossref acquired the RW database in September 2023 and publishes it openly. The full database is a CSV in a public git repository (GitLab: `crossref/retraction-watch-data`). It is refreshed on working days. Since January 2025 the RW retractions and corrections also appear in Crossref's REST API responses, and the CSV stays available.

At acquisition time the RW database had about 43k records and Crossref's own retraction metadata about 14k, with overlap, for roughly 50k total. Treat "about 50k and growing" as the scale; do not hard-code counts in the UI.

### 2.2 How we ingest it
```
opc ingest rw
  1. git pull the repo (or download the CSV) into data/raw/rw/<date>/
  2. record sha256 + file size + git commit hash in ingest_runs
  3. if sha256 unchanged from last run -> log "no change", exit 0
  4. parse CSV (encoding note below), keep ONLY allow-listed columns
  5. COPY into staging table retraction_records_stage
  6. validate (row count within +-5% of previous, required columns present, DOI format rate)
  7. upsert into retraction_records in one transaction
  8. recompute derived flags for papers touched by changed records
  9. write ingest_runs row (rows_in, rows_new, rows_changed, rows_rejected, duration)
 10. on any failure: keep old data, send alert
```

### 2.3 Columns
Expected RW columns (**VERIFY** against the real header on Day 1 and freeze in `tests/fixtures/rw_header.txt`):
`Record ID, Title, Subject, Institution, Journal, Publisher, Country, Author, URLS, ArticleType, RetractionDate, RetractionDOI, RetractionPubMedID, OriginalPaperDate, OriginalPaperDOI, OriginalPaperPubMedID, RetractionNature, Reason, Paywalled, Notes`

| Column | Keep? | Why |
|---|---|---|
| Record ID | yes | Stable link back to RW entry; cite it in the UI |
| Title, Journal, Publisher | yes | Display and context |
| Subject | yes | Routing tasks to reviewers by field |
| OriginalPaperDOI, RetractionDOI | yes | Join keys |
| OriginalPaperPubMedID, RetractionPubMedID | yes | Fallback join |
| RetractionNature | yes | Retraction / Correction / Expression of concern / Reinstatement |
| RetractionDate, OriginalPaperDate | yes | Needed for "cited after retraction" logic |
| Reason | yes | Shown verbatim, attributed to RW, never paraphrased into an accusation |
| URLS | yes | Link to notice |
| Paywalled | yes | Decides whether notice-reading tasks are possible |
| Notes | maybe | Free text; store but do not show publicly until reviewed |
| **Author** | **no** | Fairness rule; we never rank or profile people |
| **Institution** | **no** | Same |
| **Country** | **no** | Same |

### 2.4 Known problems (design for them)
- **Encoding.** Crossref's knowledge base says the file contains UTF-8 errors and can be read as latin-1 or as UTF-8 with errors ignored. We read as UTF-8 with `errors="replace"`, count replacement characters per run, and alert if the count jumps.
- **Lag and disagreement.** One 2026 user report on the Zotero forum describes an article marked retracted by the publisher in Crossref months before the RW CSV showed it. So: `status = retracted if (in RW CSV) OR (Crossref update says retraction)`. Store each source's verdict separately in `retraction_evidence`.
- **Records without a DOI.** A published analysis found hundreds of RW records lacking DOIs. These need fuzzy matching (title + journal + year) and human confirmation (task type `retraction_match`, see `REVIEW_SYSTEM.md`).
- **Multiple rows per paper.** A paper can have a correction and then a retraction. Model this as a timeline, not a boolean.
- **Retraction is not misconduct.** Many retractions are honest error or publisher error. The UI shows the reason list as RW words it and never says "fraud".
- **Closed-source export.** Crossref notes RW's export process is manual and clunky. Expect occasional malformed files. Ingest must be tolerant and loud.

### 2.5 Fairness at ingest
Author, Institution and Country are dropped in the CSV reader, before anything touches the database. There is a unit test that fails if a column outside the allow-list reaches the staging table. This is what makes the fairness rule enforceable rather than aspirational.

---

## 3. Crossref REST API (DS-02)

### 3.1 Use
- `GET /works/{doi}` for title, container title (journal), publisher, dates, DOI, `reference` list, `is-referenced-by-count`, update relations.
- Only when a DOI is not already fresh in our `papers` table (cache TTL: 7 days for metadata, 24 h for update relations).

### 3.2 Polite pool and limits
- Send a `mailto` parameter (and a `User-Agent` containing a contact). This moves requests to the better pool.
- The limits have changed more than once (announced revision effective 1 Dec 2025; third-party clients report further values in 2026). Sources disagree on exact numbers. **Do not hard-code.** Read `x-rate-limit-limit`, `x-rate-limit-interval` and `x-api-pool` from every response, start at the slowest documented tier, and only speed up when the response says so.
- Handle HTTP 429 with backoff and `Retry-After`.
- Paid **Metadata Plus** exists for production-scale use. Not needed at MVP scale.

### 3.3 References
Most Crossref members deposit references openly, but not all. When `reference` is missing or empty we fall back to OpenAlex (DS-03) and mark `references_source = "openalex"`. When both are empty the check says "reference list not available" — it never says "no retracted references".

Each Crossref reference entry may have a `DOI`, or only `unstructured` text, or partial fields. Entries without a DOI are stored with `ref_doi = NULL`, `ref_raw = <text>`. They are not matched by guesswork in v0.1. A later matcher (title + year + journal) produces candidate matches with `match_confidence`, and low-confidence candidates become `ref_match` review tasks.

### 3.4 Fixture discipline
Field names for retraction updates inside Crossref works (`update-to`, `updated-by`, relation blocks) should be confirmed against real responses in Week 1. Save 10 real JSON responses to `tests/fixtures/crossref/` and write parsers against those, not against memory.

---

## 4. OpenAlex (DS-03, DS-04)

### 4.1 What changed in 2026 (the first plan was out of date on this)
- API keys became **mandatory on 13 February 2026**. The old "polite pool" and `mailto` approach is gone for OpenAlex.
- A free account gives a key with about **$1 of usage per day**. Without a key you get about $0.10/day, then errors.
- Pricing is per operation: single-record lookups are free; list/filter calls are roughly $0.10 per 1,000; search calls roughly $1 per 1,000; PDF downloads roughly $10 per 1,000. **VERIFY** current prices on the pricing page.
- The full dataset snapshot stays free and CC0 on a public S3 bucket.

### 4.2 How we use it
- **Single lookup by DOI** for fallback metadata and `referenced_works` (free per the current model, VERIFY).
- **Never** run per-reference list queries in the request path.
- A daily budget guard: call the rate-limit endpoint at startup and hourly; if remaining budget is under 20%, stop optional OpenAlex calls and serve cached data with a "data may be older" note.
- Key lives in `OPENALEX_API_KEY`. It is per-maintainer; contributors create their own free key. `CONTRIBUTING.md` explains how in three steps.

### 4.3 Snapshot (later)
For ML (v0.4) we will download only filtered slices (e.g. works in chosen journals and years) from the S3 snapshot with the AWS CLI, into Parquet, on a machine with enough disk. Do not try to ingest the full snapshot on a laptop or a small VPS.

### 4.4 Cross-check job
Weekly job `opc audit openalex-vs-rw`: sample 2,000 DOIs, compare `is_retracted` to our merged status, write mismatches to `data_quality_events`. Publish the mismatch rate in the release notes.

---

## 5. PubPeer (DS-05)

- PubPeer's terms of service prohibit robots/scrapers and using site content to populate a searchable database. Its FAQ describes an API that is available by request (keyed).
- Large integrity tools have arrangements with PubPeer (the PPS maintainer says it uses PubPeer metadata under a no-cost agreement; the STM Integrity Hub lists PubPeer among its integrated tools). So permission is obtainable, but it must be **asked for and written down**.
- **Decision:** v0.1–v0.3 use **no automated PubPeer data**. The paper page shows an outbound link "Search this DOI on PubPeer" that the user clicks. Linking is not scraping.
- **Action (Week 3):** email PubPeer requesting API access for a non-commercial open project; template in section 10. Record the answer in `docs/licenses/LOG.md`.
- If access is granted, PubPeer signals stay internal (review-queue priority only) until ETHICS moderation is in place, and we display only "has N public comments on PubPeer" with a link, never comment text.

---

## 6. Problematic Paper Screener (DS-06)

- PPS is an existing public platform that screens the literature weekly for tortured phrases and other detectors. Its maintainers report more than 5,000 known fingerprints (as of 2024) and use Dimensions and PubPeer metadata under no-cost agreements.
- We are **not** duplicating PPS. Our difference: reader-facing DOI check, open verified-label dataset, volunteer verification workflow with measured agreement.
- We do **not** scrape PPS. We (a) build our starter phrase list from the peer-reviewed papers that publish examples, checking each license, and (b) email the PPS maintainers to propose collaboration and ask whether a shared, licensed fingerprint list is possible.
- Our tortured-phrase module must be able to consume a list from any source with fields: `phrase`, `expected_term`, `source_citation`, `license`, `added_by`, `added_at`.

---

## 7. Paper-mill research datasets (DS-07)

Two references from the original plan are recorded here and **not re-verified in this pass**: a Nature news article on paper mills (d41586-025-00212-1) and a 2025 bioRxiv preprint (10.1101/2025.08.29.673016). Before using any dataset:
1. Read its license and its data card.
2. Record how its labels were made (who decided a paper was mill-produced?).
3. Note overlap with RW (circular labels cause leakage).
4. Write a one-paragraph summary in `docs/licenses/LOG.md`.

---

## 8. Data freshness and caching policy

| Data | Refresh | Cache TTL | If source down |
|---|---|---|---|
| RW CSV | Nightly job | n/a (local table) | Serve last good data; banner shows "retraction data last updated <timestamp>" |
| Crossref metadata for a DOI | On demand | 7 days | Serve cache; mark stale |
| Crossref update relations | On demand | 24 hours | Serve cache; mark stale |
| OpenAlex fallback | On demand | 7 days | Skip; say "fallback unavailable" |
| Derived signals | Recomputed when inputs change | n/a | n/a |

Every API response includes `data_as_of` timestamps per source. The UI shows them.

---

## 9. License log template (`docs/licenses/LOG.md`)

```
## <Source name>
- Date checked:
- URL of terms:
- License / terms summary (own words):
- What we store:
- What we redistribute in the open dataset (yes/no/what):
- Attribution text to show:
- Rate limits / key requirements:
- Contact / permission emails and dates:
- Decision and who made it:
- Re-check date:
```

---

## 10. Email templates

**To PubPeer (API access request)**
> Subject: API access request for an open, non-commercial paper-check project
> Hello, I maintain OpenPaperCheck, an open-source project that lets readers paste a DOI and see external evidence about a paper (retraction status, retracted references). Volunteers verify machine-generated evidence. We would like a PubPeer API key so that we can show "has N public comments" with a link to PubPeer, never comment text. We would follow your terms, rate limits and attribution rules. Repository: <link>. Policy document: <link to ETHICS.md>. Could you tell us what is possible and what you require?

**To PPS maintainers (collaboration)**
> Subject: Collaboration on tortured-phrase fingerprints (open verification workflow)
> Hello Prof. Cabanac and team, we are building an open reader-facing tool with a human verification queue and a CC-BY labelled dataset. We do not want to duplicate PPS. Would you be open to (1) telling us the licensing of your fingerprint list, (2) sharing verified fingerprints under an open license, or (3) receiving our volunteer-verified fingerprint candidates? Repository: <link>.

**To Retraction Watch / Center for Scientific Integrity (courtesy)**
> Subject: Using the Retraction Watch database in an open project
> Hello, we use the Retraction Watch data published via Crossref in an open-source reader tool. We attribute Retraction Watch on every page and link back to the record. Please tell us if you would like different attribution wording.

---

## 11. Failure modes table

| Failure | Detection | Response |
|---|---|---|
| RW CSV not updated for >4 working days | ingest_runs "no change" streak | Alert maintainer; banner on site |
| RW schema changed | header hash mismatch | Fail ingest, keep old data, open issue automatically |
| Crossref 429 storm | metrics on 429 rate | Slow to public-pool rate; serve cache |
| OpenAlex budget exhausted | rate-limit endpoint | Disable fallback for the day |
| DOI not found anywhere | 404 from all sources | Response state `insufficient_data`, never "no concerns" |
| Reference list empty | 0 refs parsed | State "reference list not available" |
| Source license changes | quarterly license re-check | Pause redistribution of affected fields; note in changelog |

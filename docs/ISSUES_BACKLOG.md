# ISSUES_BACKLOG.md — Starter issues (create these on GitHub in Week 0)

Status: draft v1 · Last updated: 2026-09-28
Every issue below is written so a newcomer can finish it in about 1–3 hours. Copy each block into a GitHub issue using the "good first issue" template (`FILE_COMPOSITION.md` 7.3).
Labels: `good first issue` + one area label (`backend`, `frontend`, `data`, `ml`, `docs`, `design`, `translation`, `community`) + `help wanted` where noted.

Note: the Good First Issue directory asks for at least 3 labelled issues, 10 contributors, a README with setup steps and a CONTRIBUTING file (from the first plan's sources; **VERIFY** current criteria before applying). Start collecting these now.

---

## Code issues (backend / frontend)

### #1 Add retraction status badge to the DOI page
- **Labels:** frontend, good first issue
- **Goal:** show a coloured banner at the top of `/paper/[doi]` for each public state.
- **Steps:** create `StateBanner` component with four variants (`retracted_external`, `needs_review`, `no_flags_found`, `insufficient_data`); text comes from API `headline`; add icons and an accessible label (not colour only).
- **Files:** `frontend/src/components/check/StateBanner.tsx`, `frontend/src/app/paper/[doi]/page.tsx`.
- **Test:** Vitest snapshot for each variant; Playwright: open a fixture DOI and see the banner.
- **Acceptance:** [ ] four variants [ ] passes axe check [ ] works at 360 px width [ ] wording copied from `ETHICS.md` section 4.
- **Time:** 2–3 h.

### #2 Parse reference lists from Crossref with 3-tier reporting
- **Labels:** backend, good first issue
- **Goal:** turn Crossref `reference` arrays into rows for `paper_references` and separate references with DOIs from unstructured ones.
- **Steps:** write `parse_references(work_json) -> list[ParsedRef]` handling entries with `DOI`, entries with only `unstructured`, and missing `reference`; normalise DOIs with `core/doi.py`; distinguish cited-before vs. cited-after retraction dates; ensure missing/restricted lists output an explicit warning rather than "0 retracted".
- **Files:** `backend/src/openpapercheck/core/crossref.py`, `backend/tests/unit/test_crossref_refs.py`, fixtures in `tests/fixtures/crossref/`.
- **Test:** 5 real fixture responses; property test that no output DOI is un-normalised; test for missing/restricted bibliographies.
- **Acceptance:** [ ] handles missing/restricted lists with explicit note [ ] preserves order (position) [ ] categorises into with-DOI and unstructured [ ] no exceptions on odd input.
- **Time:** 2–3 h.

### #3 Add OpenAlex fallback when Crossref has no references
- **Labels:** backend, help wanted
- **Goal:** if Crossref returns no `reference`, fetch the work from OpenAlex by DOI and map `referenced_works` to DOIs.
- **Steps:** implement `OpenAlexClient.get_work(doi)` with API key and budget guard; map OpenAlex IDs to DOIs (single batched lookups are priced, so cache; **VERIFY** cost on the pricing page); set `references_source='openalex'`.
- **Files:** `ingest/openalex.py`, tests with `respx`.
- **Acceptance:** [ ] key read from `OPENALEX_API_KEY` [ ] never logs the key [ ] stops calling when the budget guard says so [ ] clear error if key missing.
- **Time:** 3 h.

### #4 Unit tests for the consensus function
- **Labels:** backend, good first issue
- **Goal:** exhaustively test `decide()` (see `DATABASE.md` section 6).
- **Steps:** write example tests (3× yes, 2 yes + 1 no, 2 unsure + 1 yes, etc.) and Hypothesis tests (permutation invariance; never a label with < 2 agreeing votes).
- **Files:** `consensus/majority.py`, `backend/tests/property/test_consensus.py`.
- **Acceptance:** [ ] 100% branch coverage of `majority.py` [ ] property tests pass 1,000 examples.
- **Time:** 1–2 h.

### #5 Add rate limiting to the API
- **Labels:** backend
- **Goal:** anonymous check endpoint limited to 60/hour/IP with `Retry-After`.
- **Steps:** add `slowapi` (or middleware), configurable via env; return problem+json 429; document in `API_SPEC.md`.
- **Test:** 61st request returns 429; headers present.
- **Acceptance:** [ ] limit configurable [ ] health endpoint exempt [ ] works behind Caddy using `X-Forwarded-For` safely (trusted proxy list).
- **Time:** 2–3 h.

### #6 Dark mode for the review page
- **Labels:** frontend, design, good first issue
- **Goal:** respect `prefers-color-scheme`; add a manual toggle.
- **Files:** Tailwind config, `frontend/src/components/review/*`.
- **Acceptance:** [ ] contrast ≥ AA in both themes [ ] verdict buttons remain distinguishable without colour [ ] preference saved locally.
- **Time:** 2 h.

### #7 Add `docker compose up` health checks
- **Labels:** infra, good first issue
- **Goal:** `db`, `api`, `web`, `worker` each have a healthcheck; `depends_on: condition: service_healthy`.
- **Acceptance:** [ ] cold start reaches healthy in < 90 s [ ] `make up` waits for health [ ] README shows expected output.
- **Time:** 1–2 h.

### #8 Export labels as CSV and Parquet
- **Labels:** backend, data
- **Goal:** `opc release build --dry-run` writes `labels.csv` and `labels.parquet` from `consensus_labels`.
- **Steps:** implement `release/export.py`; add `validate.py` that fails if forbidden columns appear (author, country, institution, email, abstract).
- **Acceptance:** [ ] schema documented [ ] `decided_month` not exact timestamp [ ] checksums written [ ] tests use a small fixture DB.
- **Time:** 3 h.

### #9 DOI normaliser with property tests
- **Labels:** backend, good first issue
- **Goal:** implement `normalize_doi()` exactly as in `TECH_STACK.md` 3.4.
- **Acceptance:** [ ] handles `doi:`, `https://doi.org/`, `dx.doi.org`, URL-encoding, trailing punctuation [ ] returns `None` for invalid [ ] idempotent [ ] never raises.
- **Time:** 1–2 h.

### #10 Retraction Watch CSV loader with allow-list
- **Labels:** backend, data
- **Goal:** load the CSV keeping only allow-listed columns.
- **Steps:** UTF-8 with `errors="replace"`, count replacements, parse `Reason` into a list, parse dates, map `RetractionNature`.
- **Test:** unit test asserts that Author, Institution, Country never appear in the staging DataFrame/rows; header-drift test compares to `tests/fixtures/rw_header.txt`.
- **Acceptance:** [ ] 500-row fixture loads [ ] rejected rows counted and logged [ ] idempotent upsert.
- **Time:** 3 h.

### #11 Materialised view `retracted_dois`
- **Labels:** backend, data
- **Goal:** one row per DOI with first retraction date; refreshed after each ingest.
- **Acceptance:** [ ] view + refresh command [ ] index on `doi` [ ] test with fixtures [ ] query for a 100-reference paper < 20 ms.
- **Time:** 2 h.

### #12 Health endpoint and freshness banner
- **Labels:** backend, frontend
- **Goal:** `/v1/health` returns RW age; frontend shows a banner if the RW data is older than 4 working days.
- **Acceptance:** [ ] no secrets in output [ ] banner text reviewed [ ] Playwright test with faked age.
- **Time:** 2 h.

---

## Data / ML issues

### #13 Build the first list of tortured phrases (with sources)
- **Labels:** data, help wanted
- **Goal:** CSV with columns `phrase, expected_term, field, source_citation, license, added_by, added_at`.
- **Steps:** collect examples only from openly licensed papers (record each license); at least 50 entries across 3 fields; **do not scrape PPS**.
- **Files:** `backend/src/openpapercheck/signals/data/tortured_phrases.csv`, `docs/licenses/LOG.md` entry.
- **Acceptance:** [ ] every row has a citation and license [ ] duplicates removed [ ] CI validates format.
- **Time:** 3 h.

### #14 Write the dataset card
- **Labels:** docs, data
- **Goal:** `DATASET_CARD.md` template: what it is, how labels were made, license, agreement stats, limits, known biases, intended and out-of-scope uses.
- **Acceptance:** [ ] follows a recognised datasheet outline [ ] states "no abstracts, no reviewer identities, no author fields" [ ] reviewed by mentor.
- **Time:** 2 h.

### #15 Baseline TF-IDF classifier notebook
- **Labels:** ml, help wanted
- **Goal:** reproducible baseline on a small public sample; time-based split.
- **Acceptance:** [ ] README with how to run [ ] metrics PR-AUC + calibration [ ] notes on limitations; not merged into the app.
- **Time:** 3 h (needs data from a maintainer-provided sample).

### #16 Check for label leakage in the baseline
- **Labels:** ml
- **Goal:** implement leakage checklist items as code (token removal, journal-only/year-only baselines, top-feature dump).
- **Acceptance:** [ ] script outputs a report [ ] flags features containing banned bookkeeping tokens [ ] documented in `SIGNALS_AND_ML.md`.
- **Time:** 3 h.

### #17 Golden DOI fixture set
- **Labels:** data, good first issue
- **Goal:** `tests/fixtures/golden_dois.json` with 20 retracted and 20 non-retracted DOIs picked from real RW/Crossref data.
- **Steps:** pick from different publishers and years; record source URL for each; include 3 edge cases (correction only, EoC, reinstated).
- **Acceptance:** [ ] each entry has `expected_state` and `source_url` [ ] no invented DOIs [ ] used by CI test.
- **Time:** 2 h.

---

## Docs / design issues

### #18 Improve the README quick start
- **Labels:** docs, good first issue
- **Goal:** a stranger runs the project in 10 minutes.
- **Steps:** try the instructions on a clean machine/VM; fix every snag; add a screenshot and a 60-second demo GIF later.
- **Acceptance:** [ ] tested by someone who did not write it [ ] shows expected output for each step [ ] troubleshooting section.
- **Time:** 2 h.

### #19 Design the tutorial screens
- **Labels:** design, good first issue
- **Goal:** Figma or paper mock-ups of the 6 tutorial screens in `REVIEW_SYSTEM.md` 14.
- **Acceptance:** [ ] mobile-first (360 px) [ ] buttons ≥ 48 px [ ] accessible colours [ ] exported as PNG in `docs/design/`.
- **Time:** 3 h.

### #20 Translate the tutorial (Hindi, Spanish, others)
- **Labels:** translation, good first issue
- **Goal:** create `frontend/messages/<locale>.json` for the tutorial and card text.
- **Acceptance:** [ ] uses the message keys from `en.json` [ ] plain language, reading level ~ grade 8 [ ] reviewed by a second speaker [ ] one issue per language.
- **Time:** 2 h per language.

### #21 Write a "How to review a paper" guide with 10 examples
- **Labels:** docs, community
- **Goal:** `docs/community/how-to-review.md` for T1 and T4 tasks: 5 worked examples each with the right answer and why.
- **Acceptance:** [ ] examples use real but non-sensitive data [ ] includes "when to press Not sure" [ ] reviewed by two testers.
- **Time:** 3 h.

### #22 Accessibility audit of the review card
- **Labels:** frontend, design
- **Goal:** run axe + keyboard-only + screen-reader pass; file follow-ups.
- **Acceptance:** [ ] report in `docs/research/` [ ] all critical issues fixed.
- **Time:** 3 h.

### #23 Privacy notice draft (plain language)
- **Labels:** docs, ethics
- **Goal:** one-page notice based on `ETHICS.md` section 7 (what we collect, why, retention, rights, contact).
- **Acceptance:** [ ] reading level plain [ ] reviewed by the legal advisor before launch [ ] linked in footer and signup.
- **Time:** 2 h.

### #24 Issue and PR templates
- **Labels:** docs, infra, good first issue
- **Goal:** create `.github/ISSUE_TEMPLATE/*.yml` and `PULL_REQUEST_TEMPLATE.md` from `WORKFLOW.md` and `FILE_COMPOSITION.md`.
- **Acceptance:** [ ] bug, feature, data-source, signal-proposal templates [ ] config.yml links to Discussions and security page.
- **Time:** 1–2 h.

---

## Community issues

### #25 Recruit 5 reviewers from a biology class
- **Labels:** community
- **Goal:** ask an instructor for 10 minutes; share QR code to the tutorial; collect feedback.
- **Acceptance:** [ ] 5 completed tutorials [ ] 3 written feedback notes in `docs/research/`.
- **Time:** ongoing.

### #26 Draft the launch post
- **Labels:** community, docs
- **Goal:** Show-HN style post plus first comment: what it is, what it is not, how to help, ethics summary, honest limits.
- **Acceptance:** [ ] reviewed by mentor [ ] no claims beyond what the tool does [ ] links to methodology and appeal page.
- **Time:** 2 h.

### #27 Set up GitHub Discussions and labels
- **Labels:** community, good first issue
- **Goal:** categories (Q&A, Ideas, Policy, Show and tell), label set from `WORKFLOW.md` 9.1.
- **Acceptance:** [ ] welcome post [ ] pinned "How to help" [ ] label colours consistent.
- **Time:** 1 h.

### #28 SQLite snapshot builder and opc update
- **Labels:** backend, data, good first issue
- **Goal:** build a compact, indexed SQLite database from allow-listed RW data, and implement `opc update` with manifest verification.
- **Steps:** write `snapshot_builder.py` compiling `retraction_records` into `retraction_records.sqlite.gz` and generate `manifest.json`; implement `opc update` in `cli.py` checking the manifest sha256 to download only when changed; verify lookups take < 2ms using stdlib `sqlite3`.
- **Files:** `backend/src/openpapercheck/ingest/snapshot_builder.py`, `backend/src/openpapercheck/core/storage.py`, `backend/src/openpapercheck/cli.py`.
- **Acceptance:** [ ] builds SQLite file < 15MB [ ] generates manifest with sha256 and date [ ] `opc update` handles 304/skip correctly [ ] zero third-party dependencies in reader.
- **Time:** 3 h.

---

## Ordering
Week 0 creates all issues. Week 1 targets #9, #10, #11, #17, #28 (unblock ingest and snapshot builder). Week 2 targets #2, #3, and PyPI release. Week 3 targets #1, #5, #12. Week 4 targets #18 and Web deployment. Week 5–6 targets #4, #19, #20, #21. Week 7–9 targets #13, #14, #15, #16. Week 10 targets #22, #23. Week 11 targets #25, #26. #6, #7, #8, #24, #27 anytime.

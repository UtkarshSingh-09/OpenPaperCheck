# WEEKLY_PLAN.md — Week-by-week, day-by-day plan (Weeks 0–16)

Status: plan of record · Last updated: 2026-09-28
Assumptions: one part-time maintainer, 12–15 hours/week, one full day off. Days are **work sessions**, not calendar days; if you only have 4 sessions per week, stretch each week to 1.5 weeks and use the cut list.
How to use: every Sunday, tick what is done, move the rest, apply the **cut list** if you are behind, and update `brain.md` section 3.
Legend: **DoD** = definition of done for the week · **Cut list** = what to drop first if behind.

Milestones: **M0** repo and docs (Wk 0) · **M1** core CLI on PyPI (Wk 2) · **M2** public v0.1-web on Postgres (Wk 4) · **M3** review site alpha (Wk 6) · **M4** signals + evidence cards (Wk 8) · **M5** ML baseline (Wk 9) · **M6** policy + security (Wk 10) · **M7** soft launch (Wk 11) · **M8** public launch + dataset v0.1 (Wk 12).

---

## Week 0 — Decide, set up, verify (M0)
**Goal:** a repo that a stranger could understand, and the facts we depend on verified.
| Session | Tasks |
|---|---|
| 1 | Check the name: GitHub org/repo, PyPI (`openpapercheck`), npm, domain. Create the GitHub org and repo (public). Add `LICENSE` (Apache-2.0), `.gitignore`, `README` stub. Copy the doc pack into the repo. Commit `brain.md` and `problem.md`. |
| 2 | **Day-1 verification** (fill `brain.md` table): download the RW CSV via git, read the repo's LICENSE, freeze the header in `tests/fixtures/rw_header.txt`; make a free OpenAlex account and API key; make 5 Crossref calls with `mailto` and record the rate-limit headers; read OpenAlex pricing page; write findings in `docs/licenses/LOG.md`. |
| 3 | Dev environment: install `uv`, Docker, Node/pnpm; create `backend/` with `pyproject.toml`; decouple `core/` (zero Postgres dependencies, stdlib `sqlite3`); pre-commit (ruff, gitleaks); `.env.example`; `Makefile`. Pin versions in ADR 0002. |
| 4 | CI skeleton (GitHub Actions: lint, tests, build). Alembic set up; first migration: `ingest_runs`, `papers`, `paper_references`, `retraction_records`. |
| 5 | Governance files: `CODE_OF_CONDUCT.md` (Contributor Covenant), `GOVERNANCE.md`, `SECURITY.md` (GitHub private reporting), `CONTRIBUTING.md`, `DATA_LICENSE.md`. Read `ETHICS.md` again; book a slot with the mentor. |
| 6 | Create the GitHub Project board, enable Discussions, add labels and issue templates, create issues #1–#27 from `ISSUES_BACKLOG.md`. Write the roadmap issue (copy of this file's table). |
| 7 (light) | **Paper prototype** of the T1 review card; test with 3 people; write `docs/research/2026-xx-paper-prototype.md`. Update `brain.md`. |
**DoD:** repo public with all root files; CI green on an empty test; Day-1 table filled; 25+ issues created; paper-prototype notes written.
**Cut list:** issue creation beyond 15; the governance polish; paper prototype with only 2 people.
**Risks:** name clash; RW license text differs from expectation → stop and ask Crossref.

---

## Week 1 — Ingest Retraction Watch & SQLite Snapshot (start of M1)
**Goal:** the RW CSV is ingested with allow-list, and a compiled SQLite snapshot is generated.
| Session | Tasks |
|---|---|
| 1 | `core/doi.py` with `normalize_doi()` + property tests (#9). Core package boundary: zero PostgreSQL/FastAPI imports. |
| 2 | RW loader with allow-list, encoding handling, reasons parsing (#10). Unit tests using a 500-row sample. |
| 3 | Staging table + `COPY` + upsert into Postgres; `ingest_runs` bookkeeping; sha256 skip logic; `opc ingest rw` CLI. |
| 4 | SQLite snapshot builder (`opc snapshot build`): compiles allow-listed records into `retraction_records.sqlite.gz` with indexes; benchmark query time (verify < 2 ms on 50k rows). |
| 5 | `core/storage.py`: pure stdlib `sqlite3` reader for CLI lookups; validation rules (row count ±5%, DOI format rate). |
| 6 | Golden DOI set (#17): pick 20 + 20 real DOIs; test that status matches source on both SQLite and Postgres. |
| 7 (light) | Write `docs/adr/0003-rw-ingest.md`; update `brain.md`; triage community issues. |
**DoD:** `opc ingest rw` loads full RW file in < 5 min; `opc snapshot build` outputs verified SQLite file < 15 MB; golden set passes; no forbidden columns reach storage.
**Cut list:** alerting (log-only); ADR.
**Risks:** encoding errors; DOIs with odd characters → fixtures and property tests.

---

## Week 2 — Crossref Client, `opc check`, and PyPI v0.1 Release (M1 complete)
**Goal:** a working, installable Python library and CLI that checks DOIs offline in seconds.
| Session | Tasks |
|---|---|
| 1 | `core/crossref.py`: `SourceClient` with timeouts, retries, backoff, User-Agent, and `mailto:` polite pool. |
| 2 | Reference parsing with 3-tier honesty rule: (1) with DOIs checked against snapshot, (2) unstructured/without DOIs marked unchecked, (3) missing/restricted lists flagged explicitly. |
| 3 | `opc check <doi>`: terminal output with tree formatting, data-as-of date, and "cited after retraction" distinction. |
| 4 | `opc update`: fetches `manifest.json` from `data-latest` release tag; conditional download of `retraction_records.sqlite.gz` if sha256 changed. |
| 5 | GitHub Action workflow to build nightly snapshot and update `data-latest` floating tag. |
| 6 | Record terminal demo GIF; polish README quick start; **publish `openpapercheck` v0.1.0 to PyPI**. |
| 7 (light) | Email PubPeer and PPS maintainers; update license log; set up monthly Zenodo freeze reminder. |
**DoD:** `pip install openpapercheck && opc update && opc check <doi>` works on any machine in < 30 seconds with 0 database setup; golden tests pass; README has demo GIF.
**Cut list:** OpenAlex client (slip to Week 3/4); monthly Zenodo automation (manual for month 1).
**Risks:** Crossref rate limits → polite pool headers; PyPI name squatted.

---

## Week 3 — API and the first web page (start of M2)
**Goal:** a real HTTP API and a page anyone can open.
| Session | Tasks |
|---|---|
| 1 | FastAPI app factory, error handlers (problem+json), `GET /v1/check/{doi}` using the service layer; signals S-001, S-002, S-003, S-010, S-040 (rules only). |
| 2 | `paper_public_state` logic and wording templates; banned-words snapshot test; `GET /v1/sources`, `/v1/health`. |
| 3 | Rate limiting (#5) and caching headers; OpenAPI export; frontend types generation. |
| 4 | Next.js project; home page with DOI box; DOI parsing on the client (paste URL or DOI). |
| 5 | `/paper/[doi]` server-rendered page: banner (#1), facts list with evidence links, references table (retracted ones highlighted), coverage and "data as of" footer, PubPeer search link. |
| 6 | Mobile pass at 360 px; accessibility pass (axe); copy review against `ETHICS.md`. |
| 7 (light) | Ask 5 people (students, a librarian) to try 3 DOIs each; record confusion. |
**DoD:** `docker compose up` serves the site locally; 40 golden DOIs display correct states; p95 cached latency < 300 ms locally.
**Cut list:** batch endpoint; sources page; PubPeer link (add later).
**Risks:** wording; `no_flags_found` misunderstood → test copy with real users.

---

## Week 4 — Deploy v0.1-web (M2)
**Goal:** public web checker on PostgreSQL, monitored and backed up.
| Session | Tasks |
|---|---|
| 1 | Provision VPS; firewall; Docker; Caddy with HTTPS; domain + Cloudflare; `docker-compose.prod.yml`. |
| 2 | Deploy pipeline (GitHub Action → images → server). Migration step with pre-deploy backup. |
| 3 | Cron/`supercronic` worker with nightly ingest into PostgreSQL; alerts; uptime monitor; Sentry. |
| 4 | Backups to object storage with encryption; **run a restore drill**; document in `infra/README.md`. |
| 5 | README quick start tested on a clean machine (#18); screenshot; `docs/about/method` and `about/ethics` pages. |
| 6 | Security pass: headers, CORS, secrets, rate limits; run a basic scan (ZAP baseline or similar); fix findings. |
| 7 (light) | **Soft announcement** to 5–10 people; collect feedback; tag `v0.1.0-web`. |
**DoD:** public URL; `/v1/health` monitored; a PostgreSQL backup restored successfully; tag `v0.1.0-web`; the hide-a-page command works (moderation stub via CLI).
**Cut list:** Sentry; staging environment; about pages copy polish.
**Risks:** server misconfiguration; ingest failing silently → alert test (break it on purpose once).

---

## Week 5 — Accounts, tasks, consensus (start of M3)
**Goal:** reviewers can log in and the system can hold and decide tasks.
| Session | Tasks |
|---|---|
| 1 | Migrations: users, auth_identities, sessions, review_tasks, task_assignments, reviews, consensus_labels, reviewer_stats. |
| 2 | Google OIDC + email magic link; session cookies; CSRF; Turnstile; `/v1/me`. |
| 3 | Reference matching pipeline v1 (fuzzy) + sample 200 matches for hand-check (H3). |
| 4 | Task generator for T1; queue query with `SKIP LOCKED` and leases; `GET /v1/tasks/next`, `POST /v1/tasks/{id}/reviews`. |
| 5 | Consensus job (`decide()`), tests (#4), escalation queue, `reviewer_stats` updater. |
| 6 | Audit log for admin actions; account deletion and export endpoints. |
| 7 (light) | Update `brain.md`; measure fuzzy-match precision (write result to `docs/research/`). |
**DoD:** end-to-end via API: create task → 3 test users vote → consensus row written; unit and property tests green; fuzzy-match precision measured.
**Cut list:** email magic link (Google only first); account export.
**Risks:** auth bugs → second reviewer for auth PRs.

---

## Week 6 — Review website alpha, tutorial, gold, first 20 reviewers (M3)
**Goal:** friends can review on their phones.
| Session | Tasks |
|---|---|
| 1 | Review card UI (mobile-first), verdict buttons, undo, progress dots, keyboard shortcuts. |
| 2 | Tutorial with 3 gold tasks and feedback (#19 designs); `tutorial_done_at`; i18n scaffolding (`next-intl`). |
| 3 | Gold tasks: creation endpoint, mixing 10%, accuracy tracking; levels 1–2 rules. |
| 4 | `/me` page (weekly count, level, private accuracy); leaderboard opt-in (accuracy-weighted). |
| 5 | Anti-abuse: minimum time, pattern detection, rate limits; moderation stub for suspensions. |
| 6 | Recruit: 20 friends/classmates; short onboarding message; monitor. |
| 7 (light) | Debrief: what confused people; fix top 3 issues; write `docs/research/2026-xx-reviewer-pilot.md`. |
**DoD:** 20 people complete the tutorial; ≥ 300 T1 reviews collected; gold accuracy and agreement computed (H2).
**Cut list:** leaderboard; levels beyond 2; Hindi/Spanish translations (issue-driven, can trickle in).
**Risks:** low participation → recruit through a class visit; poor agreement → redesign card wording, not people.

---

## Week 7 — Signals v1 and job queue (start of M4)
**Goal:** more signals, safely, and the queue for agent work.
| Session | Tasks |
|---|---|
| 1 | S-012 "cited after retraction" with date handling; tests with mutated dates. |
| 2 | Tortured-phrase list v1 (#13) + matcher S-020 with quote/meta-paper exclusions; tests. |
| 3 | Task generators T2 (retraction match) and T4 (tortured phrase); routing by subject. |
| 4 | Procrastinate queue set up; job wrappers for signals recompute. |
| 5 | Journal context S-030 (internal); denominator source decided (OpenAlex counts or none). |
| 6 | Deny-list fairness test in CI; banned-words test across all templates. |
| 7 (light) | Email PPS if no answer; note in `brain.md`. |
**DoD:** S-012/S-020/S-030 computed for a 1,000-paper sample; fairness tests green; T2/T4 tasks generated and visible to level-2 reviewers.
**Cut list:** S-030; T2.
**Risks:** tortured-phrase false positives → keep internal.

---

## Week 8 — Evidence-card agent (M4)
**Goal:** LLM writes short, verifiable summaries; code verifies them; humans check.
| Session | Tasks |
|---|---|
| 1 | Evidence bundle builder (`evidence_id`s) and output schema. |
| 2 | Provider interface + two adapters (one hosted, one OpenAI-compatible/local). |
| 3 | Verifier: citation coverage, unknown ids, banned words, numbers-in-evidence, names. |
| 4 | Prompt v1, retry with repair, caching by evidence hash; budget cap env var. |
| 5 | Task T5 generator + card UI variant; store cards in `evidence_cards`. |
| 6 | Evaluate on 100 papers: verifier pass rate, hallucination rate (hand-check 50), cost. |
| 7 (light) | Pilot H7: 100 tortured-phrase hits × 3 reviewers; compute alpha. |
**DoD:** ≥ 95% of accepted cards have every sentence traced to evidence; cost per card documented; a local model path works (even if lower pass rate).
**Cut list:** second provider; T5 UI polish (use plain card).
**Risks:** hallucination → the verifier is the gate, not the model.

---

## Week 9 — ML baseline and benchmark (M5)
**Goal:** an honest baseline with leakage checks; benchmark repo skeleton.
| Session | Tasks |
|---|---|
| 1 | `ml/` project; dataset builder from filtered OpenAlex snapshot slice or API sample; store IDs and labels only. |
| 2 | Matched negative sampling; time and journal splits. |
| 3 | TF-IDF + logistic regression; metrics (PR-AUC, calibration). |
| 4 | Leakage script (#16): token removal, journal-only/year-only baselines, top features. |
| 5 | Embedding baseline; compare; per-subject breakdown; fairness note. |
| 6 | Benchmark folder: frozen split IDs, evaluator, submission schema, leaderboard generator. |
| 7 (light) | Write `MODEL_CARD.md`; second moderator recruited (Q6). |
**DoD:** baseline results table with intervals; leakage report; benchmark can score a dummy submission.
**Cut list:** embedding baseline; leaderboard page (JSON only).
**Risks:** RW-derived labels leak → stop and document; publish only what survives.

---

## Week 10 — Policy, legal, security (M6)
**Goal:** safe to go public with a wider audience.
| Session | Tasks |
|---|---|
| 1 | Finalise `ETHICS.md`; send to mentor and legal advisor; schedule feedback call. |
| 2 | Appeals: form, email flow, moderation queue, hide/unhide, takedown flow (`appeals`, `takedowns`). |
| 3 | **Wrong-flag drill**: hide a page in under 10 minutes; write the incident runbook. |
| 4 | Privacy notice (#23); deletion/export tested; data-retention jobs. |
| 5 | Security review: OWASP ASVS L1 checklist; dependency audit; secrets rotation test; SECURITY.md contact test. |
| 6 | Accessibility audit (#22) and fixes. |
| 7 (light) | Update docs; record decisions in `brain.md`; ask a security-minded friend to attack the site (with permission). |
**DoD:** advisor feedback incorporated; appeal path tested end to end; drill under 10 minutes; ASVS L1 checklist complete.
**Cut list:** takedown UI (CLI only); non-critical a11y fixes.
**Risks:** legal advisor unavailable → keep community flags off (already default).

---

## Week 11 — Soft launch (M7)
**Goal:** a small audience uses it; you fix what breaks.
| Session | Tasks |
|---|---|
| 1 | Invite 30–50 people (classes, librarians, integrity community); watch metrics daily. |
| 2 | Fix top 10 issues; load test (50 concurrent); performance tuning. |
| 3 | 60-second demo video, screenshots, README polish, launch post draft (#26). |
| 4 | Recruit more reviewers; run an office hour; recalibrate gold. |
| 5 | Monthly-call format trial (first community call). |
| 6 | Dry-run the dataset release with real consensus data (build, validate, no publish). |
| 7 (light) | Go/no-go checklist for launch (below). |
**DoD:** ≥ 30 reviewers invited, ≥ 20 active; queue depth healthy; no SEV1 open; dry-run release passes validation.
**Cut list:** video; call.

**Go/no-go checklist for public launch:** [ ] ETHICS reviewed [ ] appeal works [ ] hide drill done [ ] backups restored [ ] alerts fire [ ] README verified on a clean machine [ ] first 15 issues open and labelled [ ] launch post reviewed.

---

## Week 12 — Public launch and dataset v0.1 (M8)
**Goal:** launch calmly, answer everyone, release the first dataset.
| Session | Tasks |
|---|---|
| 1 | Final checks; freeze labels for release; build and validate `data-v0.1.0`; dataset card; changelog. |
| 2 | Publish to Hugging Face and Zenodo; tag release; update site `/datasets`. |
| 3 | Launch day: post "Show HN" with a detailed first comment (within 5 minutes); ~30 min later share in other communities; **answer every comment the same day**. |
| 4 | Fix urgent issues; update FAQ from questions. |
| 5 | Follow-up post on the dataset; thank contributors. |
| 6 | Retrospective; update `brain.md`, `WORKFLOW.md`; set the next quarter's plan. |
| 7 (light) | Rest. |
**DoD:** dataset public with DOI; launch post live; response time < 24 h on all issues; retrospective written.
**Risks:** traffic spike → Cloudflare caching; hostile comments → Code of Conduct; a genuine error found → SEV playbook.

---

## Weeks 13–16 — Stabilise and grow (buffer)
| Week | Focus |
|---|---|
| 13 | Bug backlog; respond to every issue/PR within 48 h; second and third external contributors mentored; refine tasks with low agreement. |
| 14 | Weighted consensus experiment (Dawid–Skene) offline; report vs majority; Hindi/Spanish tutorials merged. |
| 15 | Apply to mentoring programmes (GSoC/LFX/Outreachy) — **VERIFY** timelines and requirements; prepare 5 project ideas with mentors; ≥ 3 good-first-issues open, 10 contributors goal. |
| 16 | First quarterly review: metrics, ETHICS re-read, source license re-check, plan v0.2 public community flags if moderation ready. |

---

## Hours budget (approximate, per week)
| Week | Build | Ops/docs | Community | Total |
|---|---|---|---|---|
| 0 | 5 | 6 | 2 | 13 |
| 1–2 | 10 | 2 | 1 | 13 |
| 3–4 | 10 | 3 | 2 | 15 |
| 5–6 | 9 | 2 | 4 | 15 |
| 7–8 | 11 | 2 | 2 | 15 |
| 9 | 10 | 3 | 2 | 15 |
| 10 | 5 | 8 | 2 | 15 |
| 11–12 | 6 | 3 | 6 | 15 |

## If you fall behind (global rules)
1. Protect these in order: correctness of retraction data → ethics/appeal → mobile review card → docs → everything else.
2. Never skip backup restore drills or the wrong-flag drill.
3. Prefer shipping a smaller v0.1 on time over a bigger one late.
4. Ask for help publicly (issue with `help wanted`) instead of silently slipping.
5. Take the day off.

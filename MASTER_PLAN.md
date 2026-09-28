# MASTER_PLAN.md — OpenPaperCheck

Status: plan of record v2 · Last updated: 2026-09-28
Working name: **OpenPaperCheck** (check name availability in Week 0).
This file is the index. Each area has its own md file; this one says what exists, why, and in what order to build.

---

## Contents
1. Vision and one-line pitch
2. What changed from the first plan (and why)
3. Principles
4. Scope by version
5. Architecture
6. Tech stack (summary)
7. **The md files you must create (documentation system)**
8. Repository layout (summary)
9. Workflows (summary)
10. Data sources (summary)
11. Signals and public labels
12. Review system
13. Evidence-card agent
14. ML and benchmark
15. Ethics and safety
16. 12-week roadmap (summary) + weeks 13–16
17. Launch and community
18. Metrics
19. Risks
20. Costs
21. Governance and roles
22. Day-1 checklist
23. Definition of done per milestone
24. Sources

---

## 1. Vision and pitch
> **Paste a paper's DOI. See sourced facts about whether it has been retracted or leans on retracted work. Volunteers verify the evidence. Verified labels are open.**

Three products in one project:
1. **A DOI checker** for readers (student, librarian, researcher).
2. **A review website** where non-coders verify machine-found evidence in 1–2 minutes per card.
3. **An open dataset** of verified labels with published agreement statistics, plus a benchmark for developers.

Non-coders never need GitHub. GitHub is for developers only.

---

## 2. What changed from the first plan (and why)

| # | First plan | Now | Why |
|---|---|---|---|
| 1 | "OpenAlex is a free API; send a contact email" | OpenAlex API **requires a key** (since 2026-02-13), has usage-based pricing (small daily free allowance with a free key), and no longer has the email-based polite pool. Single-work lookups only in request paths; budget guard; snapshot for bulk | Verified in OpenAlex announcements and docs |
| 2 | "Crossref: respect rate limits" | Read `x-rate-limit-*` headers dynamically; limits were revised in Dec 2025 and reportedly again in 2026 and sources disagree on exact values | Don't hard-code stale numbers |
| 3 | "Retraction Watch via Crossref, check the license" | Local nightly copy of the RW CSV (updated on working days) **merged** with Crossref update data; keep each source's verdict; allow-list columns (drop Author, Institution, Country) | Sources lag and disagree; fairness rule needs enforcement at ingest |
| 4 | "PubPeer: verify terms, optional" | **No automated PubPeer use** until written permission (terms prohibit scraping and building databases; API is by request). Outbound link only | Terms of service |
| 5 | "Tortured phrases: build from published examples" | Keep that, but explicitly do **not** scrape the Problematic Paper Screener; contact its maintainers; the list format carries license and citation per row | PPS is an existing, respected effort; collaboration beats duplication |
| 6 | Volunteers press "Looks fine / Needs review / Not sure" on papers | Volunteers verify **evidence** (task types T1–T6). "Does the reference list contain a retracted paper?" is a database join, not a human task; the human value is checking matches, notices and phrases | Cleaner labels, less legal risk, no accusations |
| 7 | Labels: "No concerns found / Needs review / Confirmed" | `retracted_external` (credit the authority), `needs_review`, `no_flags_found` ("in the sources we check"), `insufficient_data` | "Confirmed" implies we investigated; "No concerns" reads as endorsement; missing data must be visible |
| 8 | Reference retracted count | Separate "cited after retraction" from "later retracted" | Citing something retracted afterwards is not the citing authors' fault |
| 9 | Dataset with title/abstract for ML | No abstracts in the release; DOIs + labels + signals | Crossref: abstracts remain under publisher/author copyright |
| 10 | Celery-style jobs | Cron + CLI first; Postgres-backed queue only when agent jobs arrive | Fewer moving parts |
| 11 | Leaderboard by activity | Accuracy-weighted, opt-in, team-friendly | Volume rewards rushing |
| 12 | Plan lists | Plan is now a **documentation system**: brain.md, problem.md, workflow, file composition, per-area specs | Requested; makes work repeatable for humans and AI agents |
| 13 | Monolithic backend requiring PostgreSQL | Decoupled core library: `pip install openpapercheck` uses stdlib `sqlite3` and downloads pre-indexed snapshot (`opc update`); zero Postgres dependency for CLI | Developers and researchers need instant local lookups without Docker or DB administration |
| 14 | Local manual ingest on every machine | Snapshot distribution via floating tag `data-latest` with `manifest.json`; monthly immutable copy on Zenodo with DOI | Ingesting 50k rows on a laptop is bad UX; Zenodo gives researchers citable snapshots |
| 15 | OpenAlex required for fallback | OpenAlex strictly optional in CLI (Crossref `mailto:` + local snapshot default) | Mandatory API keys create onboarding friction for casual users |
| 16 | Single count for retracted references | 3-tier reference breakdown: checked with DOIs (cited before vs after), unchecked without DOIs, explicit notice if missing/restricted | Saying "0 retracted" when publisher omitted references is a false reassurance bug |

---

## 3. Principles
1. Working prototype before big plans.
2. Evidence over opinion; attribute, don't accuse.
3. No people features, ever.
4. Contribution tasks take 1–2 minutes and are validated by others.
5. Small scope; boring technology; one maintainer must be able to run it.
6. Docs first for policy, code first for behaviour.
7. Data releases on a schedule, with agreement statistics.
8. Be patient: early growth is slow.
9. Cost-aware and license-aware by design.
10. Take a day off.

---

## 4. Scope by version

| Version | Contents | Public? |
|---|---|---|
| **v0.1-cli** (Week 2) | Core Python library + CLI (`opc check`, `opc update` via SQLite snapshot); Crossref client; PyPI release | Yes, PyPI |
| **v0.1-web** (Week 4) | DOI checker web page + FastAPI on PostgreSQL: retraction/EoC/correction status, 3-tier reference check, coverage notes, monitoring, backups | Yes, external facts only |
| **v0.2** (Week 6) | Review website: login, tutorial, T1 tasks, gold, consensus, levels, leaderboard (opt-in) | Reviewers only |
| **v0.3** (Week 8–10) | Signals v1 (S-012, S-020, S-030 internal), T2/T4/T5, evidence-card agent, appeals, moderation, ethics finalised | Public output still external facts; volunteer outcomes improve accuracy |
| **v0.4** (Week 9, continues) | ML baseline + public benchmark | Repo + dataset |
| **v1.0** (Week 12) | Public launch; dataset release `data-v0.1.0` (CC-BY) | Yes |
| **v1.1+** | Community-derived flags public (only after moderation ready); weighted consensus; browser extension; T6 citation-context | Gradual |

**Not in scope (for now):** image forensics, author rankings, judging individuals, paid features, PubPeer scraping, "fake probability".

---

## 5. Architecture

```
[ Sources: Retraction Watch CSV via Crossref | Crossref REST API | OpenAlex API (optional) ]
                             │
       ┌─────────────────────┴──────────────────────┐
       ▼                                            ▼
[ Nightly Ingest Job ]                       [ Crossref REST API ]
  │ builds compiled snapshot                   │ (polite pool mailto:)
  ▼                                            │
GitHub Releases (tag: data-latest)             │
  ├── retraction_records.sqlite.gz             │
  └── manifest.json                            │
  (Monthly copy to Zenodo with DOI)            │
       │                                       │
       │ (opc update)                          │
       ▼                                       ▼
┌────────────────────────────────────────────────────────┐
│  openpapercheck Core (pip library, stdlib sqlite3)      │
│  - DOI Normalizer (core/doi.py)                        │
│  - Local Snapshot Reader (core/storage.py)             │
│  - Crossref Client (core/crossref.py)                  │
│  - CLI (opc check, opc update)                         │
└──────────────────────────┬─────────────────────────────┘
                           │ imported by
                           ▼
┌────────────────────────────────────────────────────────┐
│  Server Platform (FastAPI + PostgreSQL + Next.js web)  │
│  - PostgreSQL: papers, references, review_tasks, auth   │
│  - Task generators (T1–T5) ──► 3 independent reviewers │
│  - Consensus job ──► consensus_labels                  │
│  - Release job ──► Hugging Face + Zenodo (CC-BY)       │
└────────────────────────────────────────────────────────┘
```
Key design points: Core CLI runs anywhere with zero database dependencies using stdlib `sqlite3` and pre-compiled snapshots; Server uses PostgreSQL for transactional review tasks and auth; every fact carries source and date; humans decide; public output is external facts only until moderation exists.

---

## 6. Tech stack (summary; full detail in `docs/TECH_STACK.md`)

| Layer | Choice |
|---|---|
| Core library / CLI | Python 3.10+, stdlib `sqlite3`, httpx, Typer CLI (zero Postgres/SQLAlchemy dependency for `pip install openpapercheck`) |
| Backend Server | Python 3.13, FastAPI, Pydantic v2, SQLAlchemy 2, Alembic, psycopg 3, httpx + tenacity, structlog |
| Database (Server) | PostgreSQL (with pg_trgm and citext) |
| CLI Data Storage | Local SQLite snapshot downloaded via `opc update` from GitHub Releases `data-latest` |
| Jobs | cron/supercronic + `opc` commands; Procrastinate (Postgres queue) from Week 7 |
| Frontend | Next.js (App Router), TypeScript, Tailwind, shadcn/ui, TanStack Query, next-intl |
| Auth | FastAPI-owned: Google OIDC + email magic link, cookie sessions in Postgres, Turnstile |
| LLM agent | Provider-agnostic (`LLMProvider`), tools only, JSON schema output, code verifier |
| ML | scikit-learn, sentence-transformers, Polars, Parquet; separate `ml/` project |
| Deploy | Docker Compose on a small VPS, Caddy, Cloudflare, GitHub Actions |
| Ops | Sentry, uptime monitor, encrypted nightly backups + monthly restore drill |
| Data release | Hugging Face + Zenodo (DOI) |

---

## 7. The md files you must create (documentation system)

Create these in Week 0. Together they are the project's memory and rulebook. **Every md file starts with Status, Last updated, and a purpose line.** Facts live in exactly one file; others link.

| File | Location | Purpose | Update cadence |
|---|---|---|---|
| **`brain.md`** | root | The project's living memory: mission, non-negotiables, current state, **decision log**, open questions, glossary. First file any human or AI agent reads | Weekly + at every decision |
| **`problem.md`** | root | Problem statement, personas, evidence, gap analysis, goals, non-goals, testable hypotheses | When evidence changes |
| **`MASTER_PLAN.md`** | root | This file: plan of record and index | Monthly |
| **`AGENTS.md`** | root | Rules and commands for coding agents and newcomers (≤ 60 lines) | When rules change |
| **`ETHICS.md`** | root | Wording, appeals, privacy, moderation, safety checklist | Quarterly |
| `docs/TECH_STACK.md` | docs | Exact stack, versions policy, alternatives, exit plans, costs | On stack change (ADR) |
| **`docs/WORKFLOW.md`** | docs | Every process: weekly rhythm, dev flow, data pipeline, review pipeline, dataset release, incidents, AI-assisted development, community | With any process change |
| **`docs/FILE_COMPOSITION.md`** | docs | Map of every file and folder, naming conventions, templates | With any file/folder change |
| `docs/DATABASE.md` | docs | Schema DDL, key queries, consensus algorithm | Each migration |
| `docs/API_SPEC.md` | docs | Endpoints and examples | Each endpoint change |
| `docs/SIGNALS_AND_ML.md` | docs | Signal catalogue, fairness rules, ML plan, leakage checklist | Each signal change |
| `docs/REVIEW_SYSTEM.md` | docs | Task types, card design, levels, gold, anti-abuse, recruiting, tutorial script | With task design changes |
| `docs/DATA_SOURCES.md` | docs | Source registry, licenses, limits, failure modes, email templates | Quarterly + on source change |
| `docs/WEEKLY_PLAN.md` | docs | Week-by-week, day-by-day plan with DoD and cut lists | Every Sunday |
| `docs/ISSUES_BACKLOG.md` | docs | 27 starter issues with acceptance criteria | Until issues live on GitHub |
| `docs/adr/NNNN-*.md` | docs/adr | One decision per file | As needed |
| `docs/licenses/LOG.md` | docs/licenses | License and permission log per source | On every new source |
| `docs/research/*.md` | docs/research | Prototype tests, pilots, measurements (dated) | Never edited afterwards |
| `docs/incidents/*.md` | docs/incidents | Blameless post-mortems | After incidents |
| `docs/community/*.md` | docs/community | Call notes, reviewer guides | Monthly |
| Standard OSS files | root | `README.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `GOVERNANCE.md`, `SECURITY.md`, `LICENSE` (Apache-2.0), `DATA_LICENSE.md` (CC-BY 4.0 + upstream) | As needed |

Rules for the documentation system:
1. `brain.md` is short (< ~300 lines). It points; it does not duplicate.
2. A decision that is hard to reverse gets an ADR; a small decision gets one row in `brain.md`.
3. Docs are changed in PRs like code; CI checks links.
4. Uncertain facts are marked `VERIFY` until checked; the check is recorded in `brain.md` Day-1 table or the license log.
5. AI agents must read `AGENTS.md` → `brain.md` → the area doc before changing anything (`docs/WORKFLOW.md` section 8).
6. No secrets, personal data, or reviewer identities in any md file.

---

## 8. Repository layout (summary; full tree in `docs/FILE_COMPOSITION.md`)

```
openpapercheck/
  AGENTS.md README.md brain.md problem.md MASTER_PLAN.md ETHICS.md CONTRIBUTING.md
  CODE_OF_CONDUCT.md GOVERNANCE.md SECURITY.md LICENSE DATA_LICENSE.md Makefile
  docker-compose.yml docker-compose.prod.yml .env.example
  backend/   frontend/   ml/   infra/   docs/   tests/   data/   scripts/   .github/
```
Backend package areas: `api`, `core`, `ingest`, `signals`, `tasks`, `consensus`, `agent`, `release`, `cli`.

---

## 9. Workflows (summary; full detail in `docs/WORKFLOW.md`)
- **Weekly rhythm:** Mon triage · Tue–Thu build · Fri health check · Sat community · Sun update `brain.md`; one day off.
- **Dev:** trunk-based, conventional commits, PR template, CI gates (lint, types, tests, fairness/wording tests, docker build, security scans).
- **Data:** nightly ingest → signals → task generation → backup; every job idempotent and logged; failure alerts.
- **Review:** signal → task → 3 reviewers → consensus (or senior) → labels → recompute signals.
- **Release:** quarterly dataset release checklist (freeze, validate, dataset card, Zenodo DOI, Hugging Face).
- **Incidents:** contain within 1 hour for wrong flags; blameless post-mortem.
- **AI-assisted dev:** read `AGENTS.md` and `brain.md` first; small diffs; log decisions.

---

## 10. Data sources (summary; full detail in `docs/DATA_SOURCES.md`)
| Source | Use | Key facts (verified 2026-09-28) |
|---|---|---|
| Retraction Watch via Crossref | Core retraction data | CSV in a public git repo, updated on working days; also in Crossref API; Crossref treats its metadata as public domain except abstracts (VERIFY repo license) |
| Crossref REST API | Metadata + references | Polite pool via `mailto`; limits changed and vary by source; read headers |
| OpenAlex | Fallback + cross-check + later bulk | Key required since 2026-02-13; free key gives a small daily allowance; snapshot CC0 and free |
| PubPeer | Outbound link only | Terms restrict automated access; ask for API permission |
| Problematic Paper Screener | Collaboration, not scraping | Existing weekly detector platform; ask about fingerprint licensing |
| Paper-mill datasets | Seeds for ML | License and label origin recorded per dataset |

---

## 11. Signals and public labels (summary; `docs/SIGNALS_AND_ML.md`)
- Signals v1 (rules only): S-001 retracted, S-002 expression of concern, S-003 correction/reinstatement, S-010/S-011 cites-retracted count/share, S-012 cited-after-retraction, S-020 tortured phrases (internal), S-030 journal context, S-040 data coverage.
- Fairness rule enforced by ingest allow-list and CI deny-list tests.
- Public states: `retracted_external`, `needs_review`, `no_flags_found`, `insufficient_data`.

## 12. Review system (summary; `docs/REVIEW_SYSTEM.md`)
- Tasks T1 reference match, T2 retraction match, T3 notice-reason check, T4 tortured phrase, T5 evidence check, T6 citation context (later).
- 3 independent reviewers, majority of the same verdict, senior for disagreement, ~10% gold tasks, levels 1–4, anti-abuse controls, accuracy-weighted opt-in leaderboard, mobile-first card, 2-minute tutorial.

## 13. Evidence-card agent
Tools fetch facts; the model writes only sentences that cite evidence ids; a code verifier enforces citations, banned words, and number checks; cards are drafts checked by volunteers (T5); the agent never publishes.

## 14. ML and benchmark
Baseline first (TF-IDF + logistic regression, then embeddings), time and journal splits, leakage checklist, PR-AUC and calibration, model card, benchmark with frozen split IDs and PR-based leaderboard. Output means "similar to previously retracted papers", never "fake probability".

## 15. Ethics and safety
Attribute-not-accuse wording, banned words, appeals with time targets, hide-in-1-hour drill, privacy minimisation, second moderator before any community flag is public, mentor and legal review of `ETHICS.md`.

---

## 16. 12-week roadmap (summary; day-by-day in `docs/WEEKLY_PLAN.md`)

| Week | Deliverable | Milestone |
|---|---|---|
| 0 | Name, repo, doc pack, governance files, Day-1 verification, 25+ issues, paper prototype | M0 |
| 1 | RW allow-list ingest, DOI normaliser, stdlib `sqlite3` snapshot builder, golden set | — |
| 2 | Crossref client (`mailto:`), `opc check`, `opc update` (snapshot + manifest), **Ship PyPI v0.1.0 (CLI)** | **M1** |
| 3 | API `/v1/check` (FastAPI), signals v0, Next.js web DOI page | — |
| 4 | **Deploy v0.1-web** (PostgreSQL, Caddy, monitoring, backups, restore drill) | **M2** |
| 5 | Auth, tasks, leases, consensus, fuzzy match precision | — |
| 6 | Review card, tutorial, gold, levels; **first 20 reviewers** | **M3** |
| 7 | Signals v1, tortured-phrase matcher, T2/T4, job queue | — |
| 8 | Evidence-card agent + verifier + T5 | **M4** |
| 9 | ML baseline + benchmark repo | **M5** |
| 10 | Ethics final, appeals, moderation, security and accessibility review | **M6** |
| 11 | Soft launch, load test, dry-run release | **M7** |
| 12 | **Public launch + dataset v0.1.0** | **M8** |
| 13–16 | Stabilise, mentor contributors, weighted consensus experiment, mentoring-programme prep, first quarterly review | — |

---

## 17. Launch and community
- **Before launch (Weeks 8–11):** share progress in small communities; ask 10–20 reviewers to test; prepare a 60-second demo and screenshots.
- **Launch day:** post "Show HN" and add a detailed comment within 5 minutes; share elsewhere ~30 minutes later; answer every comment the same day.
- **First 30 days:** reply to issues/PRs in 24–48 h; keep `good first issue` and `help wanted` stocked; monthly call; first dataset write-up.
- **Where to find reviewers:** classes (biology, medicine, engineering), PhD students, librarians, research-integrity communities.
- **Later:** GSoC, LFX Mentorship, Outreachy (VERIFY current rules); Good First Issue directory once ≥ 3 labelled issues, 10 contributors, README setup steps and CONTRIBUTING exist.
- **Lessons copied from Open Food Facts and Common Voice:** tiny contributions, validation by others, fixed release schedule, one community per subject area, progress feedback.

---

## 18. Metrics
| Area | Metric |
|---|---|
| Product | Checks per week; p95 latency; share of `insufficient_data` results |
| Data quality | RW/Crossref/OpenAlex mismatch rate; fuzzy-match precision; ingest freshness |
| Reviewers | Weekly active; tasks/week; gold accuracy; alpha per task type; escalation rate |
| Community | External contributors; merged PRs; time to first response |
| Dataset | Downloads; citations; releases on schedule |
| Safety | Appeals received/resolved in time; hide-drill time; SEV1 count |
| Sustainability | Maintainer hours per week (target ≤ 15) |

---

## 19. Risks (summary; more in `problem.md` section 8)
| Risk | Fix |
|---|---|
| Wrong or misread flag | External facts only; attribution; appeals; hide drill |
| Low-quality labels | 3 reviewers, gold, levels, task redesign |
| Too few reviewers | Classroom adoption; tiny tasks; recognition |
| Source terms/prices change | Local data, caching, license log, quarterly re-check |
| Label leakage in ML | Checklist; time and journal splits |
| Bias | No people features; deny-list tests; audits |
| Duplication of existing tools | Position as complementary; contact PPS |
| Burnout | Small scope; cut lists; co-maintainers early; day off |

---

## 20. Costs (MVP, verify current prices)
Roughly $0–15/month plus a domain: small VPS, object storage for backups, free tiers for Cloudflare/Sentry/GitHub/Hugging Face/Zenodo, free OpenAlex key, free Crossref polite pool. LLM cost is $0 with a local model or capped by an env variable. Details in `docs/TECH_STACK.md` section 10.

---

## 21. Governance and roles
- Maintainer (you): decisions, admin. Mentor: reviews ethics/scope. Second moderator (needed before community flags are public). Senior reviewers (Level 4): escalations, gold authoring.
- Maintainers are added after 10+ merged PRs and sustained review help; decisions by lazy consensus in GitHub Discussions, ADR for big ones; details in `GOVERNANCE.md`.
- No payment can change, hide or add a flag.

---

## 22. Day-1 checklist
- [ ] Check the name; create the GitHub repo (public)
- [ ] Add LICENSE, README, CONTRIBUTING, CODE_OF_CONDUCT, GOVERNANCE, SECURITY, ETHICS
- [ ] Copy this doc pack into the repo; commit `brain.md` and `problem.md` first
- [ ] Download the RW data; read the repo license; freeze the CSV header
- [ ] Create a free OpenAlex key; record Crossref rate-limit headers
- [ ] Create the Postgres schema (first migration from `docs/DATABASE.md`)
- [ ] Build the first DOI lookup script (`opc check`)
- [ ] Create the roadmap issue and 15+ starter issues
- [ ] Sketch the review card on paper; show it to 3 people
- [ ] Book time with your mentor for the ethics review

---

## 23. Definition of done per milestone
| Milestone | Done when |
|---|---|
| M0 | Repo public; doc pack committed; Day-1 table filled; issues created; prototype notes written |
| M1 | Full RW ingest idempotent; Crossref/OpenAlex clients tested; `opc check` matches golden set |
| M2 | Public v0.1 site; monitored; backup restored once; tag `v0.1.0` |
| M3 | 20 reviewers done tutorial; ≥ 300 reviews; alpha computed |
| M4 | Signals v1 + evidence cards behind verifier; fairness tests in CI |
| M5 | Baseline + leakage report + benchmark skeleton |
| M6 | ETHICS reviewed; appeals and hide drill tested; security/accessibility checklists done |
| M7 | 30+ reviewers invited, no SEV1 open, dry-run release validated |
| M8 | Public launch; dataset v0.1.0 with DOI; retrospective written |

---

## 24. Sources
Checked 2026-09-28: Crossref (Retraction Watch acquisition, CSV/GitLab, REST API inclusion, metadata licensing, rate-limit announcement); OpenAlex (API keys and usage-based pricing, docs, snapshot); PubPeer (terms, FAQ); Problematic Paper Screener (Cabanac et al., The Conversation, Science); STM Integrity Hub (Science Editor, Scholarly Kitchen, STM); Zotero forum; arXiv study of retractions in OpenAlex. Background from the first plan (not re-verified): Open Food Facts, Mozilla Common Voice, launch guides for small open-source projects, Good First Issue criteria, Nature and bioRxiv paper-mill items. Full list with notes: `problem.md` section 11 and `docs/DATA_SOURCES.md`.

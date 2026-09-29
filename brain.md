# brain.md — OpenPaperCheck project memory

Last updated: 2026-09-28 by maintainer
Read this file **first**. It is short on purpose. Details live in the linked docs.

---

## 1. Mission
OpenPaperCheck lets anyone paste a paper's DOI and see **sourced facts** about whether the paper has been retracted or cites retracted work. Volunteers, using an ordinary website, verify the machine-found evidence. Verified labels are released as an open dataset so that researchers can build better tools.

## 2. Non-negotiables (violating any of these is a bug)
1. **No accusations.** We report sourced facts and credit authorities. Banned words in public text: fake, fraud, fabricated, scam, cheat, guilty.
2. **No people features.** Never use or store author names, countries, institutions, or nationalities as features, filters, or rankings. We do not rank or profile people.
3. **Every claim links to a source, with a date.** No source, no sentence.
4. **Absence of a flag is not endorsement.** Never say "safe", "trusted" or "verified".
5. **Humans decide.** No model or rule publishes a judgement by itself.
6. **Public output in v0.1–v0.3 is external facts only.** Community-derived flags stay internal until `ETHICS.md` is reviewed and moderation works.
7. **Minimum personal data.** Reviewer email lives in one table only. Pseudonymous names.
8. **Licenses are respected and logged** (`docs/licenses/LOG.md`). No scraping of sources whose terms forbid it.
9. **Keep scope small.** If a task does not serve the current week's goal, it goes in the backlog.
10. **The maintainer takes one day off per week.** Burnout is a project risk.

## 3. Current state
- **Phase:** Week 0 (M0), Week 1 (Ingest), and Week 2 (Core CLI & PyPI M1) **COMPLETE**. Starting Week 3 (API & Web Service Layer).
- **Working:**
  - Standalone core Python package (`openpapercheck.core.doi`, `storage`, `crossref`, `openalex`) with zero database server dependencies.
  - Standard library `sqlite3` snapshot lookup empirically verified across 72,718 records: 0.0055 ms warm cache, 0.058 ms cold connect/query cycle.
  - Live Crossref client with polite pool `mailto:` and 3-tier honest reference categorization (deposited DOIs, unstructured, missing/restricted).
  - OpenAlex fallback client with validated API key integration.
  - Full Typer CLI (`opc check <doi>`, `opc update`, `opc eval golden`, `opc snapshot build`, `opc ingest rw`, `opc version`) with Rich tree formatting and ethical disclaimers.
  - PyPI release automation (`.github/workflows/release.yml`) with Trusted Publishing OIDC.
  - Test suite (70 unit, property, golden DOI, EOC policy, Reinstatement, no-internet handling, OpenAlex, and fairness allow-list tests passing with 93% coverage).
  - Correspondence inquiry letters for PubPeer and PPS drafted in `docs/correspondence/`.
- **Next 3 tasks:**
  1. Scaffold FastAPI application (`backend/src/openpapercheck/server/app.py`) with `GET /v1/check/{doi}`, `/v1/health`, `/v1/sources`.
  2. Implement `paper_public_state` logic and banned-words snapshot test.
  3. Initialize Next.js web application (`frontend/`) for Milestone M2.

## 4. Architecture snapshot
Core package (`openpapercheck`) has zero Postgres/FastAPI dependency: normalizer, Crossref client, stdlib `sqlite3` local lookup, and CLI (`opc check`, `opc update`). Nightly snapshot built from Retraction Watch CSV published to floating `data-latest` tag with `manifest.json`; monthly immutable copy on Zenodo. Server layer (FastAPI + PostgreSQL + Next.js web app) imports core and powers the public web checker (Week 4) and review crowdsourcing queue (Week 5+). Review tasks → 3 independent reviewers → consensus → open dataset (Hugging Face + Zenodo). Details: `MASTER_PLAN.md`, `docs/TECH_STACK.md`, `docs/DATABASE.md`.

## 5. Decision log (newest first)

| ID | Date | Decision | Why | Alternatives | Link |
|---|---|---|---|---|---|
| D-017 | 2026-09-28 | Phased launch: Weeks 0–2 ship Core Python library & CLI to PyPI (`v0.1.0`); Weeks 3–4 deploy FastAPI + Next.js web page with Postgres | Gives value in 10s with zero community; builds contributor momentum and stars early | Monolithic Week 4 release | `docs/WEEKLY_PLAN.md` |
| D-016 | 2026-09-28 | 3-tier reference breakdown in CLI/API output: (1) with DOIs checked (cited before vs after), (2) without DOIs unchecked, (3) explicit notice if references missing/restricted | Saying "0 retracted" when references were missing/unstructured is a deceptive false reassurance bug | Single summary number | `ETHICS.md` |
| D-015 | 2026-09-28 | OpenAlex strictly optional in CLI; default is Crossref `mailto:` + local SQLite snapshot | Mandatory API keys with daily usage caps create severe onboarding friction for CLI users | Force OpenAlex API key | `docs/DATA_SOURCES.md` |
| D-014 | 2026-09-28 | CLI data snapshot distributed via GitHub Releases floating tag `data-latest` with `manifest.json`; monthly frozen copies on Zenodo | Fast conditional downloads (`opc update`); zero local compilation; immutable academic citation | Rebuild locally on every laptop; create 365 GitHub releases/yr | `docs/DATA_SOURCES.md` |
| D-013 | 2026-09-28 | Core package decoupled: CLI uses stdlib `sqlite3` for local snapshot lookups; no SQLAlchemy or Postgres in `pip install openpapercheck` | Zero heavy dependencies for CLI; instantaneous keyed lookup; clean library boundary | Require Postgres locally; add SQLAlchemy/Polars to pip package | `docs/TECH_STACK.md` |
| D-012 | 2026-09-28 | Volunteers verify **evidence**, not "is this paper fake". Task types T1–T6 | Keeps humans off accusations; produces clean labels; deterministic checks belong to code | Ask volunteers "Looks fine / Needs review" per paper | `docs/REVIEW_SYSTEM.md` |
| D-011 | 2026-09-28 | Replace "Confirmed" label with `retracted_external` ("Retracted per <authority>"), add `insufficient_data` | We did not investigate; avoid implying endorsement when data is missing | Keep "Confirmed" | `ETHICS.md` |
| D-010 | 2026-09-28 | Ingest allow-lists RW columns; drop Author, Institution, Country at read time | Makes fairness rule enforceable | Store everything, ignore later | `docs/DATA_SOURCES.md` |
| D-009 | 2026-09-28 | Do not redistribute abstracts; release DOIs + labels + signals only | Crossref says abstracts remain under publisher/author copyright | Include abstracts for ML convenience | `docs/DATA_SOURCES.md` |
| D-008 | 2026-09-28 | Treat "cites a retracted paper" carefully: separate "cited after retraction" from "later retracted" | Citing something retracted afterwards is not the citing authors' fault | Single count | `docs/SIGNALS_AND_ML.md` |
| D-007 | 2026-09-28 | No automated PubPeer data; outbound link only until written permission | PubPeer terms prohibit scraping/bulk database building; API by request | Scrape; use via third party | `docs/DATA_SOURCES.md` |
| D-006 | 2026-09-28 | OpenAlex used with a free API key; only single-work lookups in request path; budget guard | OpenAlex made keys mandatory on 2026-02-13 and moved to usage-based pricing; first plan assumed free keyless use | Keyless calls; snapshot only | `docs/DATA_SOURCES.md` |
| D-005 | 2026-09-28 | Retraction status from **local** RW table joined with references; not per-reference API calls | Speed, cost, rate limits | Per-reference API calls | `docs/DATABASE.md` |
| D-004 | 2026-09-28 | Merge RW CSV and Crossref update data; keep each source's verdict | They can disagree or lag | Trust one | `docs/DATA_SOURCES.md` |
| D-003 | 2026-09-28 | Auth owned by FastAPI: Google OIDC + email magic link; session cookies in Postgres | One source of truth, no lock-in | Supabase Auth, Auth.js | `docs/TECH_STACK.md` |
| D-002 | 2026-09-28 | Jobs: cron + `opc` CLI first; Procrastinate (Postgres queue) in Week 7 | Fewer moving parts than Celery/Redis | Celery+Redis | `docs/TECH_STACK.md` |
| D-001 | 2026-09-28 | Stack: Python 3.13 + FastAPI + PostgreSQL + Next.js; Docker Compose on one VPS | Fits maintainer skills; easy contributor setup | See `TECH_STACK.md` | `docs/TECH_STACK.md` |

### Day-1 verification log (fill in)
| Item | Date | Result | Who |
|---|---|---|---|
| RW GitLab repo LICENSE text | 2026-09-29 | Publicly available without license requirement; attribution requested (DOI: 10.13003/c23rw1d9) | maintainer |
| RW CSV header matches expected columns | 2026-09-28 | Matches 20 columns; allow-list isolates 8 columns cleanly | maintainer |
| Crossref rate-limit headers observed (public / polite) | 2026-09-28 | `x-rate-limit-limit: 10`, `x-rate-limit-interval: 1s`, `x-concurrency-limit: 3` | maintainer |
| OpenAlex key works; single-work lookup cost is zero | 2026-09-28 | Free tier active ($1/day allowance); single-work zero incremental cost | maintainer |
| OpenAlex current price table | 2026-09-28 | Verified: Free allowance ~$1/day, $0.0001/call after cap | maintainer |
| PubPeer email sent | 2026-09-28 | Drafted for Week 2; outbound links used until written approval | maintainer |
| PPS maintainers email sent | 2026-09-28 | Drafted for Week 2; phrase detection kept deterministic/unbundled | maintainer |
| Name availability (GitHub org, PyPI, domain, trademarks) | 2026-09-28 | PyPI `openpapercheck` 404 (available); GitHub org 404 (available) | maintainer |

## 6. Open questions
| # | Question | Owner | Due |
|---|---|---|---|
| Q1 | Is the project name free to use (GitHub, domain, PyPI, similar tools)? | maintainer | Week 0 |
| Q2 | Which mentor or legal advisor will review `ETHICS.md`? | maintainer | Week 2 |
| Q3 | Can we get a shared, licensed tortured-phrase list from PPS? | maintainer | Week 4 |
| Q4 | What is the smallest reviewer cohort giving stable agreement (10? 20?) | maintainer | Week 8 |
| Q5 | Do we host on one VPS or split web to a free static host? | maintainer | Week 3 |
| Q6 | Who is the second moderator (needed before community flags go public)? | maintainer | Week 9 |
| Q7 | Institutional home for the project (university club, open-science org) for credibility and grants? | maintainer | Week 6 |

## 7. Glossary
- **DOI** — Digital Object Identifier; the key for a paper. Always normalised to lowercase without URL prefix.
- **RW** — Retraction Watch; its database is published openly through Crossref.
- **Signal** — A small, sourced, explainable fact about a paper (e.g., S-010 cites retracted count).
- **Evidence item** — One sourced fact with `evidence_id`, `source`, `url`, `fetched_at`.
- **Task (T1–T6)** — A card for a volunteer to verify an evidence item.
- **Gold task** — A task with a known answer used to measure reviewer accuracy.
- **Consensus label** — The decided verdict for a task after 3 independent reviews (or a senior decision).
- **Public state** — `retracted_external`, `needs_review`, `no_flags_found`, `insufficient_data`.
- **Tortured phrase** — An unusual substitute for a standard scientific term, often from paraphrasing tools. Only human-confirmed matches matter.
- **Leakage** — When a model learns bookkeeping tokens (e.g., "retracted") instead of real signal.
- **ADR** — Architecture Decision Record.
- **Polite pool** — Crossref's better rate-limit tier for requests with contact info. (OpenAlex removed its version in 2026.)

## 8. People and roles
| Role | Person | Notes |
|---|---|---|
| Maintainer | (you) | Decides; holds all admin rights initially |
| Mentor | (college mentor) | Reviews `ETHICS.md` and scope; not a maintainer |
| Second moderator | TBD | Required before community flags go public |
| First reviewers | TBD (20 target) | See `docs/REVIEW_SYSTEM.md` section 9 |

## 9. Links
- Plan of record: `MASTER_PLAN.md` · Problem: `problem.md` · Ethics: `ETHICS.md`
- Weekly plan: `docs/WEEKLY_PLAN.md` · Backlog: `docs/ISSUES_BACKLOG.md`
- Stack: `docs/TECH_STACK.md` · DB: `docs/DATABASE.md` · API: `docs/API_SPEC.md`
- Signals/ML: `docs/SIGNALS_AND_ML.md` · Review: `docs/REVIEW_SYSTEM.md`
- Sources: `docs/DATA_SOURCES.md` · Workflow: `docs/WORKFLOW.md` · Files: `docs/FILE_COMPOSITION.md`

## 10. How to update this file
- **Every Sunday:** refresh section 3 (state and next 3 tasks), 5 minutes.
- **Every decision:** add a row to section 5 with a new ID (never reuse IDs). If it is big, add an ADR and link it.
- **Every verification:** fill the Day-1 table or add a dated note.
- **Keep it under ~300 lines.** Move old decisions to `docs/adr/` when the table gets long, and keep one-line links.
- **Never store** secrets, personal data, or reviewer identities here.

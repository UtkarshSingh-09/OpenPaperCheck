# TECH_STACK.md — Exactly what we use, why, and how to leave it

Status: decided for v0.1–v0.3 · Last updated: 2026-09-28
Rule: **boring beats clever.** One maintainer, part-time, must be able to run and fix everything.
Version rule: on Week 0 Day 3, pin the **latest stable** of each tool, write the versions in `docs/adr/0002-pinned-versions.md`, then upgrade only by Dependabot PR.

---

## 1. Decision table

| Layer | Choice | Why this | Rejected alternatives | Exit plan |
|---|---|---|---|---|
| Language (backend) | Python 3.13 (move to 3.14 when all deps support it) | Your ML and agent skills; best data-library ecosystem | Node/TS backend (would split skills), Go (slower to iterate) | n/a |
| Web framework | FastAPI + Pydantic v2 | Typed, auto OpenAPI, async, huge community | Django (heavier; admin is nice but we want a typed API), Flask | OpenAPI file lets any framework replace it |
| Core Library / CLI | Python 3.10+, stdlib `sqlite3`, httpx, Typer | Zero heavy dependencies; instant pip install; keyed lookups run in <2ms | SQLAlchemy in CLI (adds bloat), Polars/DuckDB (extra dependencies) | Pure Python stdlib sqlite3 |
| Database (Server) | PostgreSQL (latest stable your host offers) | Reliable, JSONB, arrays, full-text, pg_trgm, `COPY` for fast ingest | SQLite (concurrent writes from reviewers), MongoDB (we need joins) | Standard SQL dumps |
| Database (CLI) | Local SQLite snapshot (`retraction_records.sqlite.gz`) | Self-contained, zero-configuration, downloaded via `opc update` | Local Postgres (unacceptable onboarding barrier for CLI users) | Swap snapshot URL |
| ORM / migrations (Server) | SQLAlchemy 2.x (typed) + Alembic | Standard for multi-table server data model | SQLModel (thin, less control), raw SQL only | Plain SQL migrations are readable |
| Storage (CLI) | Python stdlib `sqlite3` | C-level speed, zero extra pip dependencies, handles 50k rows in <15MB | SQLAlchemy (unnecessary overhead for single SELECT ... WHERE doi = ?) | SQLite stdlib |
| DB driver (Server) | psycopg 3 (async) | Modern, supports `COPY` | asyncpg (fine, but no COPY helper parity) | n/a |
| CLI tool | Typer (`opc` command) | Fast, typed CLI: `opc check`, `opc update`, and server ingest commands | Click directly | n/a |
| HTTP client | httpx + tenacity retries | Async, timeouts, HTTP/2 | requests (sync) | n/a |
| Frontend | Next.js (App Router) + TypeScript + Tailwind + shadcn/ui | Mobile-friendly, SSR for shareable paper pages, huge ecosystem | SvelteKit (smaller community for contributors), plain React SPA (weak SEO for DOI pages) | Static export possible for public pages |
| API client | OpenAPI -> `openapi-typescript` (types) + TanStack Query | Frontend types come from the backend, cannot drift | Hand-written fetchers | n/a |
| i18n | `next-intl` | Tutorial translations (Hindi, Spanish, others) | i18next | JSON message files are portable |
| Auth | FastAPI owns auth: Google OIDC (Authlib) + email magic link; HttpOnly session cookie; sessions in Postgres | One source of truth; no vendor lock-in; no passwords | Supabase Auth (fast start but couples DB and auth), Auth.js (splits auth from API), Clerk (paid, closed) | Auth is an interface (`AuthProvider`); swap later |
| Background jobs | v0.1–0.3: cron/supercronic running `opc` commands in a `worker` container. Add **Procrastinate** (Postgres-backed queue) in Week 7 for agent jobs | No Redis, no Celery, nothing extra to run | Celery + Redis (two more services), RQ, Arq | Commands are plain functions |
| LLM access | `LLMProvider` protocol with adapters: Anthropic SDK, OpenAI-compatible HTTP (covers Ollama, vLLM, llama.cpp, hosted), optional LiteLLM | No vendor lock-in; local models allowed | Hard-wiring one vendor | Adapter swap |
| Structured output | JSON Schema + Pydantic validation + automatic repair retry (max 2) | Deterministic schema stored with each card | Free-form text | n/a |
| ML | scikit-learn (TF-IDF + logistic regression), then sentence-transformers embeddings; Polars/Pandas; Parquet | Baseline first; explainable | Fine-tuning big models first | n/a |
| Container | Docker + Docker Compose | Contributors run everything with one command | Kubernetes (overkill), Nix (steep) | Compose files are readable by any host |
| Reverse proxy / TLS | Caddy (automatic HTTPS) | Two-line config | Nginx + certbot | n/a |
| CDN / WAF | Cloudflare free tier in front | DDoS shield, caching for public paper pages | none | Remove DNS proxy |
| Hosting (recommended) | One small VPS running Compose (Hetzner or similar; check current price) | Cheapest predictable cost; no cold starts | Vercel + Fly + Neon/Supabase (works, more accounts, free-tier limits) | Compose runs anywhere |
| Object storage | S3-compatible bucket (Cloudflare R2 or Backblaze B2) | Backups and dataset staging | local disk only | rclone |
| Dataset hosting | Hugging Face Datasets + Zenodo (DOI) | Discoverability plus a citable DOI | GitHub releases only (size limits) | n/a |
| Error tracking | Sentry (free tier for open source) | Stack traces with context | Logs only | n/a |
| Uptime | Uptime Kuma (self-hosted) or a free hosted monitor | Alerts to Telegram/email | none | n/a |
| Logs | structlog JSON to stdout; Docker logs; Loki later if needed | Simple | ELK | n/a |
| CI/CD | GitHub Actions | Free for public repos | GitLab CI, Jenkins | Compose files remain |

---

## 2. Repository shape (monorepo)

```
backend/     Python package `openpapercheck` (api, ingest, signals, consensus, agent, cli)
frontend/    Next.js app
ml/          Separate pyproject (heavy deps stay out of backend image)
infra/       docker-compose files, Caddyfile, backup scripts
docs/        all planning and policy docs, ADRs
tests/       cross-cutting fixtures (golden DOIs, real API responses)
```
Details in `FILE_COMPOSITION.md`.

---

## 3. Backend details

### 3.1 Python tooling
| Need | Tool |
|---|---|
| Env + deps + lockfile | `uv` (fast, one tool); commit `uv.lock` |
| Lint + format | `ruff` (both) |
| Types | `pyright` (strict on `consensus/` and `signals/`, standard elsewhere) |
| Tests | `pytest`, `pytest-asyncio`, `hypothesis`, `respx` (mock httpx), `testcontainers` or a Compose Postgres in CI |
| Coverage | `pytest-cov`; gate: 80% overall, 95% on `consensus/` |
| Security | `pip-audit`, `bandit` (light), `gitleaks` in pre-commit and CI |

### 3.2 Key libraries
`fastapi`, `uvicorn` (with `gunicorn` workers in prod), `pydantic`, `pydantic-settings`, `sqlalchemy`, `alembic`, `psycopg[binary]`, `httpx`, `tenacity`, `typer`, `structlog`, `orjson`, `authlib`, `itsdangerous`, `slowapi` (rate limiting; Caddy/Cloudflare do the first line), `python-multipart` (only if uploads appear), `procrastinate` (Week 7).

### 3.3 Package layout
```
backend/src/openpapercheck/
  core/           doi.py, crossref.py (client), storage.py (stdlib sqlite3 snapshot reader)
  cli.py          Typer app: `opc check <doi>`, `opc update`, and server jobs
  # Server-specific packages (used by FastAPI / Celery / workers):
  api/            routers, dependencies, error handlers, schemas
  server/         settings.py, db.py (Postgres/SQLAlchemy session), logging.py, security.py
  ingest/         rw.py, crossref.py, openalex.py, references.py, snapshot_builder.py
  signals/        registry.py, retraction.py, references.py, tortured.py, context.py
  tasks/          generators per task type, assignment, gold
  consensus/      majority.py, weighted.py (later), metrics.py
  agent/          tools.py, prompts/, schema.py, verifier.py, providers/
  release/        export_csv.py, export_parquet.py, dataset_card.py, checksums.py
```
Rule: **core/ has ZERO PostgreSQL or FastAPI dependencies.** It is the standalone library published to PyPI. `api/` and `server/` packages import `core/`.

### 3.4 DOI normalisation (single function, heavily tested)
`normalize_doi(s)`: trim whitespace; strip `doi:` and `https://(dx.)?doi.org/` prefixes; URL-decode; lowercase; strip trailing punctuation `.,;)`; validate `^10\.\d{4,9}/\S+$`; return `None` if invalid. Property tests with Hypothesis: idempotent, never raises. Every DOI in the database goes through it. Case-insensitivity matters because DOIs are case-insensitive but sources differ in case.

### 3.5 HTTP client rules
- Timeouts: connect 3 s, read 10 s.
- Retries: 3 with exponential backoff and jitter on 429/5xx/timeouts; honor `Retry-After`.
- Circuit breaker per source (open after 5 consecutive failures for 60 s).
- One shared `SourceClient` base class that adds User-Agent, `mailto`, and reads rate-limit headers.
- Never log API keys; redact query params named `api_key`.

### 3.6 Configuration
All config via environment variables through `pydantic-settings`. `.env.example` committed; `.env` git-ignored. Required variables:

```
OPC_ENV=dev|staging|prod
DATABASE_URL=postgresql+psycopg://opc:opc@db:5432/opc
SECRET_KEY=<32+ random bytes>
PUBLIC_BASE_URL=https://example.org
CROSSREF_MAILTO=you@example.org
OPENALEX_API_KEY=<free key>
GOOGLE_CLIENT_ID= / GOOGLE_CLIENT_SECRET=
SMTP_HOST= / SMTP_PORT= / SMTP_USER= / SMTP_PASSWORD= / MAIL_FROM=
TURNSTILE_SITE_KEY= / TURNSTILE_SECRET=
SENTRY_DSN=
LLM_PROVIDER=anthropic|openai_compat|none
LLM_BASE_URL= / LLM_API_KEY= / LLM_MODEL=
BACKUP_S3_ENDPOINT= / BACKUP_S3_BUCKET= / BACKUP_S3_KEY= / BACKUP_S3_SECRET=
```

---

## 4. Frontend details

| Need | Tool |
|---|---|
| Framework | Next.js (App Router), TypeScript strict |
| Package manager | pnpm |
| Styling | Tailwind CSS + shadcn/ui components |
| Data fetching | TanStack Query, types generated from `openapi.json` |
| Forms | React Hook Form + Zod |
| i18n | next-intl, message files in `frontend/messages/<locale>.json` |
| Tests | Vitest + Testing Library (units); Playwright (end-to-end, mobile viewport included) |
| Lint | ESLint + Prettier |
| Accessibility | eslint-plugin-jsx-a11y; axe checks in Playwright; keyboard-only review flow must work |
| Charts | Recharts or plain SVG (small) |

Design constraints:
- **Mobile first.** Review card fits a 360 px wide screen; buttons at least 48 px high; thumb-reachable.
- **Pages:** `/` (DOI box), `/paper/[doi]` (result; server-rendered, shareable), `/review` (queue), `/review/tutorial`, `/me` (stats), `/about/method`, `/about/ethics`, `/appeal`, `/datasets`.
- **No dark patterns** on the leaderboard (see `REVIEW_SYSTEM.md`).
- Every flag on `/paper/[doi]` shows its evidence link, source name, and timestamp.

---

## 5. Auth design (small but critical)

- Google OIDC via Authlib; email magic link (signed, single-use, 15-minute token, stored hashed).
- Session: random 256-bit id in HttpOnly, Secure, SameSite=Lax cookie; row in `sessions` table; 30-day sliding expiry.
- CSRF: double-submit token on state-changing routes.
- Signup protections: Cloudflare Turnstile, per-IP and per-email rate limits, disposable-email domain blocklist (updateable file).
- Roles: `reviewer`, `senior_reviewer`, `moderator`, `admin`. Role checks live in one dependency (`require_role`).
- Data minimisation: email stored only in `auth_identities`; never returned by any API; display name is pseudonymous; delete-account endpoint removes identity and pseudonymises reviews (keeps vote, drops link).

---

## 6. Jobs and scheduling

| Job | Command | Schedule | Notes |
|---|---|---|---|
| RW ingest | `opc ingest rw` | daily 02:30 UTC | idempotent; alerts on failure |
| Signal recompute | `opc signals recompute --changed` | after ingest | only touched papers |
| Task generation | `opc tasks generate` | every 6 h | keeps queue between min and max size |
| Gold audit | `opc tasks gold-audit` | weekly | reviewer accuracy update |
| OpenAlex cross-check | `opc audit openalex-vs-rw` | weekly | quality metric |
| Consensus finalise | `opc consensus run` | every 15 min | closes tasks with enough votes |
| Backup | `infra/backup.sh` | daily 03:30 UTC | dump, encrypt, upload, prune |
| Restore drill | manual checklist | monthly | restore into scratch DB and count rows |
| Release build | `opc release build --version X.Y.Z` | quarterly | see `WORKFLOW.md` |

Scheduler: `supercronic` in the `worker` container reading `infra/crontab`. All jobs write to `job_runs` (name, started, finished, status, message).

---

## 7. LLM evidence-card agent

- **Tools only, model writes prose.** Tools: `get_metadata(doi)`, `get_retraction_records(doi)`, `get_reference_stats(doi)`, `get_signals(doi)`. The agent cannot browse the web.
- **Input:** a JSON bundle of evidence items, each with `evidence_id`, `source`, `url`, `fetched_at`, `fact`.
- **Output schema:** `{ "summary_sentences": [ {"text": str, "evidence_ids": [str, ...]} ], "not_available": [str] }`.
- **Verifier (code, not model):** rejects the card if any sentence has no `evidence_ids`, any id is unknown, any sentence contains banned words (`fake`, `fraud`, `fabricated`, `scam`, `cheat`, `guilty`) or a person's name from the metadata, or numbers not present in evidence.
- Stored with `model`, `model_version`, `prompt_hash`, `schema_version`, `created_at`.
- Cards are drafts. They enter the review queue as task type `evidence_check` and are public only after consensus.
- Provider is pluggable; a small local model must work well enough to pass the verifier, otherwise the card is not generated and the page shows the raw evidence list (which is always shown anyway).
- Cost control: cache per (doi, evidence_hash); monthly budget env var; hard stop.

---

## 8. ML stack (v0.4)

- Separate `ml/` project with its own `pyproject.toml` so the API image stays small.
- Data: Parquet files built by `opc release build --ml-view`; text fields fetched on the researcher's machine, not shipped.
- Baseline 1: TF-IDF (word 1–2 grams + char 3–5 grams) + logistic regression.
- Baseline 2: sentence-transformer embeddings + logistic regression.
- Metrics: PR-AUC, precision@k, recall@k, calibration curve and ECE, per-journal breakdown.
- Splits: **time-based** (train earlier years, test later) and **journal-held-out**. Report both.
- Leakage tests: remove retraction-notice words ("retracted", "withdrawn"), strip publisher boilerplate, check top features manually, run a "title-only" and "journal-only" baseline as sanity floors.
- Tracking: a `results/` folder with JSON per run and a model card; MLflow optional later.
- Leaderboard: static site generated from `benchmark/submissions/*.json` validated by a script; submitted by PR.

---

## 9. Infrastructure and deployment

### 9.1 Compose services (production)
```
caddy    ports 80/443, reverse proxy to web and api
web      Next.js (standalone output)
api      FastAPI (gunicorn + uvicorn workers)
worker   supercronic + opc commands (same image as api)
db       postgres with a named volume
```
Optional later: `uptime-kuma`, `pgadmin` (never exposed publicly).

### 9.2 Environments
| Env | Purpose | Data |
|---|---|---|
| local | Contributor laptops; `docker compose up` | Small sample fixtures (500 RW rows, 50 papers) |
| staging | Optional, same VPS second Compose project | Copy of prod with reviewer emails scrubbed |
| prod | Public | Real |

### 9.3 Backups
Nightly `pg_dump` (custom format), encrypted with `age`, uploaded to object storage, retention 7 daily + 4 weekly + 6 monthly. **A backup is real only after a restore test.** Monthly drill in the workflow calendar.

### 9.4 Security baseline (OWASP ASVS Level 1 as checklist)
HTTPS only + HSTS; secure cookies; CSRF; strict CORS (only our web origin); input validation with Pydantic; output encoding by React; parameterised queries only; rate limits; dependency scanning (Dependabot, `pip-audit`, `pnpm audit`); secret scanning (gitleaks, GitHub push protection); CodeQL; least-privilege DB roles (`opc_api` cannot drop tables; migrations run as `opc_migrator`); admin actions in `audit_log`; `SECURITY.md` with private reporting via GitHub Security Advisories.

### 9.5 Observability
- Request logs with request id; never log emails or cookies.
- Metrics that matter: check latency p50/p95, cache hit rate, source error rates, ingest freshness, queue depth, reviews per day.
- Alerts: ingest failed, backup failed, disk > 80%, API 5xx rate, source 429 rate.

---

## 10. Cost estimate (MVP, verify current prices)

| Item | Estimate |
|---|---|
| VPS (2 vCPU, 4 GB) | low single-digit to about $10 / month |
| Domain | about $10–15 / year |
| Object storage (backups, dataset staging) | free tier to about $2 / month |
| Cloudflare, Sentry OSS tier, GitHub, Hugging Face, Zenodo | $0 |
| OpenAlex | $0 with free key at our volumes if we use single lookups and caching |
| Crossref | $0 |
| LLM for evidence cards | $0 with local model; otherwise cap by env var (start at a few dollars/month) |
| Email (magic links) | free tier of a transactional email provider |

Possible funding later: GitHub Sponsors, Open Collective, small grants for open science infrastructure.

---

## 11. Deliberately not used (and when we would reconsider)

| Not used | Reconsider when |
|---|---|
| Kubernetes, microservices | Never for this scale |
| Redis, Celery | Queue depth or fan-out that Postgres queue cannot handle |
| Kafka / streaming | Never |
| Vector database | Only if similarity search is needed; try `pgvector` first |
| GraphQL | Never; REST + OpenAPI is enough |
| Server-side accounts with passwords | Never |
| Third-party analytics with cookies | Use privacy-friendly, cookieless analytics (e.g., self-hosted Plausible/Umami) if any |
| Image forensics | Out of scope; commercial tools exist |

---

## 12. Quick start (goes into README)

### 12.1 End-User CLI (instant, zero Docker / zero Postgres)
```bash
pip install openpapercheck
opc update                     # downloads latest verified SQLite snapshot (~5MB) in 2 seconds
opc check 10.1038/nature12373  # instant local check with 3-tier reference breakdown
```

### 12.2 Full-Stack Platform Development (Docker Compose)
```bash
git clone https://github.com/<org>/openpapercheck && cd openpapercheck
cp .env.example .env            # add your contact email (OpenAlex optional)
docker compose up --build       # db, api, web, worker
docker compose exec api opc db migrate
docker compose exec api opc ingest rw --sample   # loads the small sample
open http://localhost:3000
```
Acceptance: a new contributor gets the CLI running in **under 30 seconds**, and the web DOI page working in **under 10 minutes**, measured on a clean machine by someone who did not write the docs.

---

## 13. Upgrade and deprecation policy

- Dependabot weekly; merge patch/minor when CI is green.
- Major upgrades (Python, Postgres, Next.js) get their own ADR and a branch.
- Postgres major upgrades: dump/restore in a staging Compose project first.
- If a source API changes terms (as OpenAlex did in 2026), open an issue labelled `data-source-change`, update `DATA_SOURCES.md`, and log an ADR the same day.

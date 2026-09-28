# WORKFLOW.md — How work moves through OpenPaperCheck

Status: draft v1 · Last updated: 2026-09-28
This file answers: "How do I do X here?" for every kind of work. If a workflow changes, change this file in the same PR.

Contents: 1 Weekly maintainer rhythm · 2 Developer workflow · 3 Data pipeline workflow · 4 Review pipeline · 5 Dataset release · 6 Signal/feature change · 7 Incidents · 8 AI-assisted development · 9 Community workflow · 10 Decision records · 11 Definition of done

---

## 1. Weekly maintainer rhythm (assumes 12–15 hours/week, part-time)

| Day | Time-box | Activity |
|---|---|---|
| Mon | 1 h | Triage: new issues/PRs, label them, reply to everyone (≤ 48 h rule); read `brain.md` "Current state" |
| Tue–Thu | 3 × 2.5 h | Build: pick the top item from the current week in `WEEKLY_PLAN.md` |
| Fri | 1.5 h | Review reviewer metrics (agreement, queue depth), check ingest/backup health, fix quick issues |
| Sat | 2 h | Community: recruit, write, answer questions, or reviewer office hour |
| Sun | 0.5 h | Update `brain.md` (state + decisions), plan next week; **one full day off per week** |

Rule: if the week slips by more than 25%, apply the "cut list" for that week (in `WEEKLY_PLAN.md`) rather than working nights.

---

## 2. Developer workflow

### 2.1 Branching and commits
- Trunk-based: `main` is always deployable. Short-lived branches: `feat/<topic>`, `fix/<topic>`, `docs/<topic>`, `data/<topic>`.
- Conventional Commits: `feat(api): add batch check`, `fix(ingest): handle latin-1 rows`. Changelog and version bump generated from them (release-please).
- No direct pushes to `main` once CI exists (branch protection).

### 2.2 Pull request checklist (PR template)
```
## What and why
## How I tested it
- [ ] Unit tests added/updated
- [ ] Ran `make check` locally (lint, types, tests)
- [ ] Migration included and reversible (if DB change)
- [ ] Docs updated (which file?)
- [ ] Touches signals, wording or public output? -> linked ETHICS checklist
- [ ] No author/country/institution used anywhere
## Screenshots (UI changes, mobile too)
```

### 2.3 CI on every PR (must pass to merge)
1. `ruff check` + `ruff format --check`
2. `pyright`
3. `pytest` with Postgres service, coverage gate
4. `pnpm lint`, `pnpm typecheck`, `pnpm test`
5. OpenAPI drift check (generated types up to date)
6. Deny-list test (fairness) + banned-words snapshot test
7. Docker build of api and web images
8. gitleaks, dependency review, CodeQL (scheduled + on PR)
9. Playwright smoke test on `main` and on labelled PRs

### 2.4 Local commands (`Makefile`)
```
make up          # docker compose up --build
make migrate     # alembic upgrade head
make seed        # load sample RW rows and 50 papers
make check       # ruff + pyright + pytest + frontend lint/types/tests
make fmt         # auto-format
make e2e         # Playwright
make openapi     # regenerate frontend API types
```

### 2.5 Code review rules
- Reviewer target: first response within 48 h; small PRs (< 400 lines) preferred.
- Maintainer merges after 1 approval (2 for anything in `consensus/`, `signals/` public wording, `auth/`).
- Be kind, be specific, suggest code. Follow the Code of Conduct.

### 2.6 Releases (software)
- SemVer. Tag on `main`. release-please opens a "Release PR"; merging it creates the GitHub release and changelog.
- Deploy: GitHub Action builds images → pushes to registry → SSH/`docker compose pull && up -d` on the server (or a pull-based updater). Migrations run first (`opc db migrate`), with a backup taken just before.
- Rollback: `docker compose` with previous image tag; migrations must be reversible or expand-then-contract.

---

## 3. Data pipeline workflow (daily)

```
02:30 UTC  opc ingest rw           -> retraction_records, retraction_evidence
02:40      opc snapshot build      -> builds retraction_records.sqlite.gz + manifest.json -> upload to data-latest
02:50      opc signals recompute --changed
03:00      opc tasks generate      (respect queue min/max)
03:30      infra/backup.sh
every 15m  opc consensus run
weekly     opc audit openalex-vs-rw ; opc tasks gold-audit
monthly    upload frozen snapshot copy to Zenodo (citable DOI)
```
Rules:
1. Every job is idempotent (safe to re-run).
2. Every job writes `job_runs`/`ingest_runs`.
3. Failure → alert (email/Telegram) with the job name and last log lines; old data stays live.
4. A "no change" ingest is a success, not an error (and skips snapshot re-upload).
5. Run jobs manually with `docker compose exec worker opc <command>`.

Ingest failure playbook:
1. Read the alert; open `ingest_runs` to see stage.
2. If the source file is malformed: keep old data, note in `brain.md`, open an issue with the sample lines, add a fixture and fix the parser.
3. If the source is unreachable: wait, retry next cycle; banner if > 4 working days stale.
4. If the schema changed: update parser and `DATA_SOURCES.md`; add ADR.

---

## 4. Review pipeline workflow

1. **Signal or matcher produces a candidate** (e.g., fuzzy reference match to a retracted DOI).
2. **Task generator** creates a `review_tasks` row (deduped by payload hash) with type, difficulty, subject, priority.
3. **Queue** serves it to eligible reviewers (see `DATABASE.md` 5.3), 3 reviewers max, leases 30 minutes.
4. **Reviewers answer** through the card. Gold tasks are mixed in.
5. **Consensus job** every 15 minutes: majority of 3, or escalates to senior queue.
6. **Outcome:** `consensus_labels` row. The signal engine reads it (e.g., a reference match confirmed or rejected) and recomputes the paper's signals.
7. **Quality loop (weekly):** update `reviewer_stats`, promote/demote levels, retire noisy gold tasks, review task types with low agreement, adjust wording.
8. **Public effect** only through the rules in `ETHICS.md` (v0.1–v0.3: only external facts are public; volunteer outcomes improve *accuracy* of those facts).

---

## 5. Dataset release workflow (every 3 months)

Release version `MAJOR.MINOR.PATCH` (labels schema change = MAJOR, new task types/fields = MINOR, data refresh = PATCH).

| Step | Who | Detail |
|---|---|---|
| T-14 days | maintainer | Open a "Release X.Y.Z" issue with this checklist; announce freeze date |
| T-7 | maintainer | Freeze: mark `consensus_labels` rows eligible (n_reviews ≥ 3, not superseded, no takedown) |
| T-7 | maintainer | Run `opc release build --version X.Y.Z --dry-run`; read the report |
| T-5 | maintainer | Validation: schema check, row counts vs previous, duplicates, DOI validity, no forbidden columns (deny-list), no abstracts, no emails |
| T-5 | maintainer | Compute agreement stats (alpha per task type), gold accuracy distribution, class balance |
| T-4 | maintainer + one reviewer | Write dataset card (what, how labelled, license, limits, known biases, intended and out-of-scope uses) and changelog |
| T-3 | maintainer | Legal/license check: upstream attributions in `DATA_LICENSE.md`; takedowns applied |
| T-2 | maintainer | Build final: CSV + Parquet + `checksums.json`; upload to Hugging Face (dataset repo) and Zenodo (new version, get DOI) |
| T-0 | maintainer | Tag Git release, insert `dataset_releases` row, publish blog post, share in communities |
| T+7 | maintainer | Retrospective: what broke, update this file |

Files in a release:
```
labels.parquet / labels.csv         (doi, task_type, label, n_reviews, agreement, method, decided_month)
signals.parquet                     (doi, signal_key, value, computed_month)   # no abstracts
tasks_stats.json                    (agreement per task type)
DATASET_CARD.md   CHANGELOG.md   checksums.json   LICENSE (CC-BY-4.0)   ATTRIBUTIONS.md
```
Privacy in the release: `decided_month` instead of exact timestamps; no reviewer ids (aggregate stats only).

---

## 6. Signal / public-wording change workflow
1. Issue with "signal proposal" template.
2. 7-day discussion.
3. ADR.
4. ETHICS checklist (`ETHICS.md` section 13).
5. Implementation behind a feature flag (`signals.public.<key>`).
6. Test on 200 papers, measure false positives, review outputs by hand.
7. Enable for a soft-launch cohort; then everyone.
8. Note in changelog and methodology page.

---

## 7. Incident workflow

| Severity | Examples | First response | Owner |
|---|---|---|---|
| SEV1 | Wrong public flag on a real paper; data breach; leaked secret | Hide page / rotate secrets **within 1 hour**; then investigate | maintainer |
| SEV2 | Site down, ingest failing > 2 days, backup failing | Fix within 24 h; status note if user-visible | maintainer |
| SEV3 | Minor bugs, slow pages | Normal issue flow | anyone |

Steps: 1) Contain (hide page, disable feature flag, rotate keys). 2) Communicate (status page/banner; notify the affected person for wrong flags). 3) Fix. 4) Post-mortem within 5 days, blameless, in `docs/incidents/YYYY-MM-DD-title.md` (timeline, cause, fix, prevention). 5) Update tests/checklists.

Wrong-flag drill (do once before launch): pretend a page shows a wrong flag → confirm you can hide it in under 10 minutes.

---

## 8. AI-assisted development workflow (Claude, Codex or any coding agent)

Purpose: keep an AI helper consistent with the project and prevent it from drifting or breaking rules.

### 8.1 Files the agent must read first
1. `AGENTS.md` (short: rules and commands, points to the rest)
2. `brain.md` (mission, non-negotiables, current state, decisions)
3. The specific doc for the area (`docs/DATABASE.md`, `docs/SIGNALS_AND_ML.md`, …)
4. The issue text

### 8.2 Session protocol
1. State the task in one sentence and list the files you will touch.
2. Read `brain.md` "Non-negotiables" and the relevant doc.
3. Write or update tests first when the behaviour is clear.
4. Make the smallest change that passes; run `make check`.
5. If you make a decision (library, schema, wording), add an entry to `brain.md` Decision log or an ADR.
6. Update the doc that describes what you changed.
7. Summarise: what changed, what to verify by hand, what you did **not** do.

### 8.3 Rules for agents (also in `AGENTS.md`)
- Never add author/country/institution fields or logic.
- Never write public wording containing banned words.
- Never hard-code API keys or numbers that come from headers/config.
- Never invent DOIs, API fields or license terms: fetch a real sample or mark `VERIFY`.
- Never delete or rewrite migrations that were merged.
- Ask a human before: changing `ETHICS.md`, adding a public signal, adding a dependency with a copyleft or unclear license, or touching auth.

### 8.4 Prompt template for a task
```
Context: OpenPaperCheck. Read AGENTS.md and brain.md first.
Task: <one sentence>. Issue: <link>.
Files likely involved: <paths>.
Acceptance: <bullets from the issue>.
Constraints: fairness rule, banned words, tests required, keep the diff small.
Output: patch + list of tests run + doc changes + any decision to log.
```

---

## 9. Community workflow

### 9.1 Issue triage labels
`good first issue`, `help wanted`, `bug`, `feature`, `data-source`, `data-source-change`, `docs`, `design`, `translation`, `signal-proposal`, `ethics`, `security` (private), `blocked`, `needs-info`, `wontfix`.

### 9.2 Response rules
- New issue or PR: first reply within 48 h (24 h target during launch month).
- `good first issue` must include: what to do, which files, how to test, expected time (< 3 h).
- Stale PR nudges at 14 days; close at 45 days with thanks and an invitation to reopen.

### 9.3 Onboarding a contributor
1. README quick start (10 minutes to run).
2. Pick a `good first issue`; comment "I'll take this"; get assigned.
3. Open a draft PR early.
4. Maintainer reviews within 48 h.
5. After 3 merged PRs, invite to the contributors team; after 10, discuss maintainer role (see `GOVERNANCE.md`).

### 9.4 Monthly community call (30 min)
Agenda: metrics (5), demo (5), roadmap and asks (10), open floor (10). Notes in `docs/community/YYYY-MM.md`. Record only with consent.

### 9.5 Communication channels
GitHub Issues (work), GitHub Discussions (ideas, Q&A, policy), one chat space (Discord or Matrix) for casual talk, `SECURITY.md` for private reports. Avoid more than three channels.

---

## 10. Decision records (ADR)
- Folder `docs/adr/NNNN-title.md`. Template: Context · Decision · Alternatives · Consequences · Status · Date.
- Write an ADR when a choice is hard to reverse or affects contributors (framework, schema shape, license, public wording, data source).
- `brain.md` keeps a one-line index of ADRs.

---

## 11. Definition of done (for any task)
- [ ] Code + tests + docs updated
- [ ] CI green
- [ ] No fairness/wording violations
- [ ] Works on a phone-size viewport (UI)
- [ ] Logged decisions in `brain.md` or an ADR
- [ ] Issue closed with a short note of what shipped

# AGENTS.md — Instructions for AI coding agents and automated tools

Status: active · Last updated: 2026-09-28

Read this file and `brain.md` BEFORE touching any code.

## 1. Non-negotiables
1. **Never use author names, institutions, countries, or nationalities** as features, filters, or rankings.
2. **Never use banned words** in UI, CLI, or LLM text: `fake`, `fraud`, `fabricated`, `scam`, `cheat`, `guilty`.
3. **No invented facts:** Never invent DOIs, API fields, or license terms. Use real fixtures from `tests/fixtures/`.
4. **Attribute, don't accuse:** State sourced external facts only.
5. **Decoupled Core:** `core/` has ZERO PostgreSQL/FastAPI imports. It must work using stdlib `sqlite3`.

## 2. Reading order
1. `AGENTS.md` (this file)
2. `brain.md` (Non-negotiables, current state, decisions)
3. Domain doc for the area you are touching (`docs/DATABASE.md`, `docs/TECH_STACK.md`, `docs/SIGNALS_AND_ML.md`, etc.)

## 3. Standard Commands
- `make check` — run linters, type checks, and tests (ruff, pyright, pytest)
- `make fmt` — auto-format code
- `make test` — run pytest test suite
- `make up` — run local docker compose stack

## 4. Constraints on Changes
- Ask a human before: modifying `ETHICS.md`, exposing a public signal, adding third-party dependencies, or altering authentication.
- Never edit or delete applied Alembic migrations; add a new migration instead.
- Keep diffs small and focused. Always log decisions in `brain.md` or an ADR.

## 5. Definition of Done
See `docs/WORKFLOW.md` section 11: code + unit/property tests + docs updated + CI passing.

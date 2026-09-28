# Contributing to OpenPaperCheck

Thank you for your interest in contributing to OpenPaperCheck! We are building open scholarly infrastructure that helps readers and researchers make careful, evidence-based citations.

---

## 1. Non-Code Ways to Help
You do not need to write code to make a massive impact:
- **Review Evidence Cards:** Use our web review queue on your phone (takes 1–2 minutes per card).
- **Translate the Tutorial:** Help translate tutorial strings into Hindi, Spanish, or other languages (`frontend/messages/`).
- **Audit Task Clarity:** Test the review tutorial and tell us which questions or examples are ambiguous.
- **Report Missing/Changed Sources:** Help monitor Crossref and Retraction Watch schema changes.

---

## 2. Setting Up Your Development Environment

### Prerequisites
- Python 3.10+ (Python 3.13 recommended)
- `uv` package manager (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- Docker and Docker Compose (if working on backend API or web UI)
- Node.js 20+ and `pnpm` (if working on frontend)

### Quick Start
```bash
git clone https://github.com/UtkarshSingh-09/OpenPaperCheck.git && cd OpenPaperCheck
cp .env.example .env

# Install Python backend dependencies in virtualenv
cd backend && uv sync && cd ..

# Run all local checks (lint, types, tests)
make check
```

---

## 3. Contribution Workflow

### Step 1: Pick an Issue
Look for issues labeled [`good first issue`](https://github.com/UtkarshSingh-09/OpenPaperCheck/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22) or [`help wanted`](https://github.com/UtkarshSingh-09/OpenPaperCheck/issues?q=is%3Aissue+is%3Aopen+label%3A%22help+wanted%22). Comment on the issue to get assigned before starting work.

### Step 2: Branching & Commits
- Use short-lived feature branches: `feat/<topic>`, `fix/<topic>`, `docs/<topic>`.
- We use **Conventional Commits**:
  - `feat(cli): add update progress bar`
  - `fix(ingest): handle latin-1 replacement characters`
  - `docs(api): document 3-tier reference response`

### Step 3: CI Gates & Testing
Every Pull Request must pass the following CI checks:
1. `ruff check` and `ruff format --check`
2. `pyright` strict type checking
3. `pytest` test suite with coverage
4. **Deny-list Fairness Check:** Greps code for author/country/institution variables.
5. **Banned Words Snapshot Check:** Ensures no UI text uses banned words (`fake`, `fraud`, `scam`, etc.).

Run `make check` locally before opening your PR.

---

## 4. Pull Request Checklist

When submitting a PR, ensure:
- [ ] Tests have been added or updated covering your changes.
- [ ] `make check` passes cleanly.
- [ ] No author, institution, or country features are used.
- [ ] Banned words are not present in any user-facing text.
- [ ] Relevant documentation has been updated.

---

## 5. Community and Support
- **Discussions:** Use GitHub Discussions for questions, ideas, and architecture proposals.
- **Code of Conduct:** All contributors must adhere to our [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

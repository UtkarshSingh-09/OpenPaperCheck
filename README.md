# OpenPaperCheck

> **Paste a paper's DOI. See sourced facts about whether it has been retracted or leans on retracted work. Volunteers verify the evidence. Verified labels are open.**

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Data License: CC-BY 4.0](https://img.shields.io/badge/Data_License-CC--BY_4.0-green.svg)](DATA_LICENSE.md)
[![PyPI version](https://img.shields.io/badge/PyPI-v0.1.0.dev2-blue.svg)](https://pypi.org/project/openpapercheck/)
[![Status: Milestone M2](https://img.shields.io/badge/Status-Milestone_M2_Ready-emerald.svg)](docs/WEEKLY_PLAN.md)

---

## What is OpenPaperCheck?

Retracted and problematic papers continue to circulate, deceive readers, and get cited in new scientific work. OpenPaperCheck is an open-source, evidence-first scholarly integrity ecosystem:

1. **A Fast DOI Checker:** Gives students, librarians, and researchers an honest, sourced breakdown of a paper's retraction status and its reference list.
2. **A Crowdsourced Verification Queue:** A mobile-friendly micro-review platform where non-technical volunteers verify machine-found evidence (not paper quality) in 20–60 seconds per card.
3. **An Open Labelled Dataset & Benchmark:** Quarterly CC-BY 4.0 releases on Hugging Face and Zenodo with inter-rater agreement statistics ($\alpha$) to help developers build better open detection tools.

---

## 30-Second Quick Start (CLI)

Install the standalone Python client (requires zero database setup and uses Python's standard library):

```bash
# 1. Install the core package
pip install openpapercheck

# 2. Download the latest verified Retraction Watch snapshot (~5MB)
opc update

# 3. Check any paper's DOI
opc check 10.1038/nature12373
```

### Example Terminal Output

```text
$ opc check "10.1016/s0140-6736(97)11096-0"

╭──────────────────── Paper: 10.1016/s0140-6736(97)11096-0 ────────────────────╮
│ RETRACTED: Ileal-lymphoid-nodular hyperplasia, non-specific colitis, and     │
│ pervasive developmental disorder in children                                 │
│ The Lancet • Published: 1998-02-01                                           │
│                                                                              │
│  RETRACTED EXTERNAL                                                          │
│  RETRACTED  according to Retraction Watch (Record #4036, 2010-02-06)         │
│ Reasons: Falsification/Fabrication of Data, Investigation by                 │
│ Company/Institution, Investigation by Third Party, Lack of Approval from     │
│ Company/Institution, Lack of IRB/IACUC Approval and/or Compliance,           │
│ Manipulation of Results, Upgrade/Update of Prior Notice(s)                   │
╰──────────────────────────────────────────────────────────────────────────────╯
References (26 total listed):
├── ✓ 16 checked via deposited DOIs
│   └── 16 no flags recorded in Retraction Watch
└── ℹ 10 without DOIs (Unstructured text; could not be checked offline)

Data as of: 2026-09-29 (72,718 records) • Sources: Crossref API, Retraction Watch
Disclaimer: This tool reports external facts. Absence of a flag is not endorsement. Every claim links to an authority.
```

---

## Non-Negotiables & Ethical Principles

1. **Attribute, Don’t Accuse:** We report sourced external facts (*"according to Retraction Watch record #..."*). Banned words in public text: `fake`, `fraud`, `fabricated`, `scam`, `cheat`, `guilty`.
2. **Zero People Features:** We never store, profile, rank, or feature author names, institutions, countries, or nationalities.
3. **No False Reassurance:** Absence of a flag is never called "safe", "trusted", or "verified". If a publisher omits reference data, we report *"References not deposited by publisher"*, never *"0 retracted references"*.
4. **Humans in the Loop:** Automated models and rules only generate candidate evidence; humans verify before public flags are produced.

Read our full [ETHICS.md](ETHICS.md) and [brain.md](brain.md) for details.

---

## Full-Stack Local Development (Docker Compose)

For contributors working on the web application, FastAPI backend, or background worker:

```bash
# Clone the repository
git clone https://github.com/UtkarshSingh-09/OpenPaperCheck.git && cd OpenPaperCheck

# Configure environment (add your email for Crossref polite pool)
cp .env.example .env

# Start PostgreSQL, API, Web, and Worker containers
docker compose up --build

# Run database migrations
docker compose exec api opc db migrate

# Load small local sample data
docker compose exec api opc ingest rw --sample

# Open local web app
open http://localhost:3000
```

---

## Documentation System

Every part of OpenPaperCheck is specified in detail:

- **Scientific Methodology:** [docs/about/method.md](docs/about/method.md)
- **Ethics & Banned Words:** [docs/about/ethics.md](docs/about/ethics.md)
- **Infrastructure & Restore Runbook:** [infra/README.md](infra/README.md)
- **Living Project Memory:** [brain.md](brain.md)
- **Problem Statement & Users:** [problem.md](problem.md)
- **Master Plan of Record:** [MASTER_PLAN.md](MASTER_PLAN.md)
- **Ethics, Appeals & Privacy:** [ETHICS.md](ETHICS.md)
- **Tech Stack & Architecture:** [docs/TECH_STACK.md](docs/TECH_STACK.md)
- **Database Schema & Consensus:** [docs/DATABASE.md](docs/DATABASE.md)
- **Data Sources & Freshness:** [docs/DATA_SOURCES.md](docs/DATA_SOURCES.md)
- **Review System & UX:** [docs/REVIEW_SYSTEM.md](docs/REVIEW_SYSTEM.md)
- **Signals & ML Benchmark:** [docs/SIGNALS_AND_ML.md](docs/SIGNALS_AND_ML.md)
- **Weekly Execution Plan:** [docs/WEEKLY_PLAN.md](docs/WEEKLY_PLAN.md)
- **Starter Issues Backlog:** [docs/ISSUES_BACKLOG.md](docs/ISSUES_BACKLOG.md)

---

## Contributing

We love contributions! Please read [CONTRIBUTING.md](CONTRIBUTING.md) to get started with our workflow, testing discipline, and starter issues.

All participants must abide by our [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## License

- **Code:** [Apache-2.0](LICENSE)
- **Verified Labels & Datasets:** [CC-BY 4.0](DATA_LICENSE.md)

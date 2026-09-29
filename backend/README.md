# OpenPaperCheck (`opc`)

[![PyPI version](https://img.shields.io/pypi/v/openpapercheck.svg)](https://pypi.org/project/openpapercheck/)
[![Python versions](https://img.shields.io/pypi/pyversions/openpapercheck.svg)](https://pypi.org/project/openpapercheck/)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://github.com/UtkarshSingh-09/OpenPaperCheck/blob/main/LICENSE)
[![Tests](https://img.shields.io/badge/Tests-74%20passed-brightgreen.svg)](https://github.com/UtkarshSingh-09/OpenPaperCheck)
[![Coverage](https://img.shields.io/badge/Coverage-93%25-brightgreen.svg)](https://github.com/UtkarshSingh-09/OpenPaperCheck)

> **Paste a paper's DOI. See sourced facts about whether it has been retracted or leans on retracted work. Fast, offline-first, and evidence-backed.**

---

## Who is this for?

- 🎓 **Authors & Researchers:** Check your bibliography before submitting a manuscript to avoid citing retracted literature.
- 🔍 **Peer Reviewers & Editors:** Audit reference lists of submitted manuscripts in seconds.
- 📚 **Librarians & Research Integrity Officers:** Verify retractions and expressions of concern across collections.
- 💻 **Developers & Data Scientists:** Query Crossref reference metadata and Retraction Watch snapshots via a clean CLI or Python API.

---

## 30-Second Quick Start

### 1. Install via pip

```bash
pip install openpapercheck
```

### 2. Download the latest verified snapshot

```bash
opc update
```

*(For developers testing without network download, run `opc snapshot build --sample` to seed bundled test fixtures).*

### 3. Check any paper's DOI

```bash
opc check 10.1038/nature12373
```

---

## Terminal Output Examples

### Example 1: Clean Paper (`NO FLAGS FOUND`)

```text
$ opc check 10.1038/nature12373

╭───────────────────────── Paper: 10.1038/nature12373 ─────────────────────────╮
│ Nanometre-scale thermometry in a living cell                                 │
│ Nature • Published: 2013-08-01                                               │
│                                                                              │
│  NO FLAGS FOUND                                                              │
│ No retractions or flagged references recorded                                │
╰──────────────────────────────────────────────────────────────────────────────╯
References (30 total listed):
├── ✓ 29 checked via deposited DOIs
│   └── 29 no flags recorded in Retraction Watch
└── ℹ 1 without DOIs (Unstructured text; could not be checked offline)

Data as of: 2026-09-29 (72,718 records) • Sources: Crossref API, Retraction Watch
Disclaimer: This tool reports external facts. Absence of a flag is not 
endorsement. Every claim links to an authority.
```

### Example 2: Retracted Paper (`RETRACTED EXTERNAL`)

```text
$ opc check 10.1016/s0140-6736(97)11096-0

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
Disclaimer: This tool reports external facts. Absence of a flag is not 
endorsement. Every claim links to an authority.
```

---

## CLI Commands

| Command | Description |
| :--- | :--- |
| `opc check <DOI>` | Inspect a paper and its reference list for retractions and editorial notices. |
| `opc update` | Download or refresh the local Retraction Watch SQLite database snapshot. |
| `opc eval` | Run accuracy and latency benchmark against the golden evaluation set. |
| `opc snapshot build` | Build or manage local SQLite snapshots (supports `--sample` for offline testing). |
| `opc version` | Display current installed OpenPaperCheck version. |

---

## Ethical Non-Negotiables

1. **Attribute, Don't Accuse:** We report sourced external facts (*"according to Retraction Watch record #..."*). Banned subjective words in public text: `fake`, `fraud`, `fabricated`, `scam`, `cheat`, `guilty`.
2. **Zero People Features:** We never store, profile, rank, or feature author names, institutions, or countries.
3. **No False Reassurance:** Absence of a flag is never called "safe", "trusted", or "verified". If a publisher omits reference metadata, we report *"References not deposited by publisher"*, never *"0 retracted references"*.
4. **Humans in the Loop:** Automated pipelines report candidate facts; humans verify evidence before public consensus flags are finalized.

---

## Links & Community

- **GitHub Repository:** [https://github.com/UtkarshSingh-09/OpenPaperCheck](https://github.com/UtkarshSingh-09/OpenPaperCheck)
- **Issue Tracker:** [https://github.com/UtkarshSingh-09/OpenPaperCheck/issues](https://github.com/UtkarshSingh-09/OpenPaperCheck/issues)
- **License:** [Apache-2.0](https://github.com/UtkarshSingh-09/OpenPaperCheck/blob/main/LICENSE)

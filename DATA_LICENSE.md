# DATA_LICENSE.md — Licensing and attributions for OpenPaperCheck datasets

Status: active · Last updated: 2026-09-28

This document defines the licensing, attribution, and redistribution terms for data produced and utilized by the OpenPaperCheck project.

---

## 1. Verified Labels Dataset (Our Work)
All consensus-verified labels, task agreement statistics, signal computations, and evaluation splits produced by OpenPaperCheck are licensed under:

**Creative Commons Attribution 4.0 International (CC-BY 4.0)**
https://creativecommons.org/licenses/by/4.0/

When using, redistributing, or citing OpenPaperCheck datasets, please cite:
```bibtex
@dataset{openpapercheck2026,
  title        = {OpenPaperCheck: Verified Scholarly Retraction and Reference Integrity Dataset},
  author       = {OpenPaperCheck Contributors},
  year         = 2026,
  publisher    = {Zenodo},
  doi          = {10.5281/zenodo.xxxxxx}
}
```

## 2. Upstream Data Sources and Attributions

OpenPaperCheck aggregates and cross-references data from open scholarly infrastructure. Upstream sources retain their respective licenses and terms:

1. **Retraction Watch Database (via Crossref):**
   - Retraction, correction, and expression of concern records are accessed via the public GitLab repository (`crossref/retraction-watch-data`) published by Crossref.
   - Crossref states that its bibliographic metadata is in the public domain under **Creative Commons CC0 1.0 Universal**.
   - Attribution: *"Retraction data provided by the Retraction Watch database, published by Crossref."*

2. **Crossref REST API:**
   - Work metadata, update relationships, and reference lists are queried under Crossref's open metadata terms (CC0 for metadata).
   - Abstracts remain under the copyright of their respective publishers and authors and are **NOT** redistributed in OpenPaperCheck datasets.

3. **OpenAlex API and Snapshots:**
   - Scholarly graph and fallback work metadata are licensed under **Creative Commons CC0 1.0 Universal**.

## 3. What We Do NOT Distribute
To respect copyright and privacy:
- **No paper abstracts or full texts:** Researchers and users fetch text directly from publisher or open-access APIs.
- **No author personal data:** Author names, affiliations, countries, and institutions are explicitly excluded from data releases.
- **No reviewer personal data:** Reviewer email addresses are never released. Consensus labels list anonymized reviewer counts and agreement metrics only.

## 4. Takedowns and Corrections
If a retraction notice or reference match in our published dataset is found to be in error, please submit an appeal via `/appeal` or email `security@openpapercheck.org`. Corrected or retracted entries will be excluded from the next dataset release and logged in `CHANGELOG.md`.

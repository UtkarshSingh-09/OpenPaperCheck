# OpenPaperCheck Methodology

This document outlines the scientific methodology, data models, and verification algorithms used by **OpenPaperCheck** to evaluate scholarly paper retractions and citation integrity.

---

## 1. DOI Normalization & Verification

Scholarly DOIs (Digital Object Identifiers) can be cited or pasted in numerous formats. Before any database query or API request is executed, DOIs undergo rigorous canonical normalization:

1. **Protocol & URL Stripping:** Strips `https://doi.org/`, `http://dx.doi.org/`, and formatting prefixes.
2. **Identifier Prefix Stripping:** Strips leading `doi:` or `doi: ` labels.
3. **Punctuation Trimming:** Removes trailing periods, commas, or semicolons frequently captured when copying from printed bibliography lists.
4. **Case Normalization:** DOI directory registrant prefixes are case-insensitive; all DOIs are converted to canonical lowercase.
5. **Syntax Validation:** Verified against regular expression `^10\.\d{4,9}/[-._;()/:a-z0-9]+$`.

---

## 2. Upstream Citation Graphs & Polite Pool

To fetch deposited reference lists without abusing public scholarly infrastructure:
- **Crossref REST API:** Queried using the polite pool header `mailto:` specified via `CROSSREF_MAILTO`.
- **Timeouts & Exponential Backoff:** Network queries enforce a 5-second timeout with jittered retry backoff.
- **Fail-Safe Provenance:** If an upstream registry times out or fails, OpenPaperCheck reports this failure explicitly via `coverage.sources_failed` rather than assuming zero citations or retractions.

---

## 3. The 3-Tier Reference Honesty Rule

Reference lists in academic publishing are heterogeneous. Many publishers do not deposit references, or deposit only unstructured OCR text without persistent identifiers.

To avoid creating dangerous **false negatives**, OpenPaperCheck partitions reference audits into 3 strict tiers:

| Tier | Category | Treatment |
|---|---|---|
| **Tier 1** | **Checked (With DOI)** | Verified directly against the indexed Retraction Watch database snapshot. |
| **Tier 2** | **Unchecked (No DOI)** | Unstructured references lacking persistent identifiers are explicitly labeled as **Unchecked**. |
| **Tier 3** | **Restricted / Missing** | If a publisher closes reference access, OpenPaperCheck reports `deposit_status: restricted` rather than returning a clean bill of health. |

---

## 4. Deterministic Signals (S-001 to S-040)

OpenPaperCheck uses transparent, deterministic rules. Every signal is verifiable and links directly to authoritative public records:

### `S-001`: Target Paper Retracted
- **Definition:** The queried DOI matches an official retraction record in the Retraction Watch database.
- **Evidence:** Retraction Watch Record ID, notice date, notice nature (`Retraction`), and verbatim notice reasons.

### `S-002`: Expression of Concern
- **Definition:** The queried DOI matches an indexed Expression of Concern (EoC) notice.
- **Evidence:** Retraction Watch Record ID, notice date, and publisher reasons.

### `S-003`: Reinstated or Corrected
- **Definition:** A formal correction, erratum, or reinstatement notice has been published.
- **Evidence:** Notice nature and official dates.

### `S-010`: Cites Retracted References
- **Definition:** Identifies any reference in the paper's bibliography that has been retracted or received an expression of concern.
- **Breakdown:** Evaluates citation timing:
  - `cited_after_retraction`: Cited after the formal retraction notice was published.
  - `cited_before_retraction`: Cited before the retraction notice was issued.
  - `unknown`: Publication dates could not be verified.

### `S-040`: Data Coverage & Reference Deposit Honesty
- **Definition:** Reports the ratio of references with persistent DOIs versus total references listed by the publisher.

---

## 5. Public Integrity States

Every paper audit concludes with one of four unambiguous public states:

1. `retracted_external`: Target paper was retracted by an official publisher or editorial notice.
2. `needs_review`: Target paper cites retracted literature or has an active Expression of Concern.
3. `no_flags_found`: No retraction notices or retracted references were found in the current snapshot.
4. `insufficient_data`: Reference list is closed, missing, or unavailable.

# ADR-0004: Notice Severity Hierarchy and Authoritative Citation Timing Anchor

## Status
Accepted (2026-09-29)

## Context
In scholarly publishing, papers often accumulate multiple integrity notices over several years. For example:
- **Wakefield et al. (The Lancet, 1998):** On 2004-03-06, 10 of the 12 co-authors published a partial notice titled "Retraction of an interpretation" (Crossref / Retraction Watch Record 17269, categorized as `Correction`). The paper itself was **not** retracted by the journal editors at that time. Six years later, on 2010-02-06, the editors of The Lancet issued a formal full retraction notice (Record 4036, categorized as `Retraction`).
- Other publications often receive an *Expression of Concern* while an institutional investigation is pending, followed months or years later by a full *Retraction*.
- Occasionally, papers are reinstated after a flawed publisher procedure.

When OpenPaperCheck evaluates a bibliography to determine whether a citation occurred before or after retraction, a core architectural and ethical question arises: **Which notice date serves as the comparative anchor point?**

## Decision
1. **Notice Severity Priority Ordering:**
   In `storage.py` (`get_retraction` and `check_reference_dois`), notice records for a DOI are sorted deterministically by notice severity:
   ```sql
   ORDER BY 
       CASE nature
           WHEN 'Retraction' THEN 1
           WHEN 'Expression of concern' THEN 2
           WHEN 'Correction' THEN 3
           WHEN 'Reinstatement' THEN 4
           ELSE 5
       END,
       retraction_date DESC
   LIMIT 1
   ```
2. **Authoritative Citation Timing Anchor:**
   - Citation timing (`cited_after_retraction` vs. `cited_before_retraction`) is evaluated against the formal **full Retraction** notice date whenever a full retraction exists.
   - A paper published between a partial notice/correction and the full retraction (e.g., a paper published in 2007 citing Wakefield) is classified as `(Cited BEFORE retraction occurred)` relative to the full retraction date (2010-02-06).
3. **Transparency of Prior History:**
   The full retraction entry preserves the controlled vocabulary reasons from Retraction Watch, including `Upgrade/Update of Prior Notice(s)`. This informs the reader that previous notices existed without misrepresenting the date of the formal retraction.
4. **Correction and Reinstatement Policy (Erratum / Corrigendum / Reinstated Works):**
   - **Bibliographic Reference Filtering:** Routine corrections (`nature == 'Correction'`) and official journal reinstatements (`nature == 'Reinstatement'`) do not invalidate research. A reinstatement signifies that a prior notice was overturned or the author/work was formally cleared. Therefore, `check_reference_dois()` explicitly filters `AND nature IN ('Retraction', 'Expression of concern')`. Citing a corrected or reinstated paper NEVER triggers `NEEDS_REVIEW` on the citing paper.
   - **Target Paper Evaluation:** A target paper with *only* a Correction or Reinstatement notice is not discredited; `determine_paper_state()` evaluates its status based on its references (`NO_FLAGS_FOUND` if references are clean). The CLI transparently displays an informational notice regarding the non-retracting notice (e.g. `Note: Target paper has a non-retracting 'Reinstatement' notice`) without displaying a retraction badge.

## Ethics and Policy Rationale
1. **Avoid Defamatory Misattribution:**
   Under OpenPaperCheck's core principle *"Evidence over opinion; attribute, don't accuse"*, accusing an author of "citing after retraction" based on a partial notice (which explicitly was not a formal journal retraction) or flagging bibliographies due to an erratum is factually incorrect and introduces reputational risk for innocent researchers.
2. **Conservative Anchor Rule:**
   When ambiguity exists, the system defaults to the formal legal/editorial act of full retraction.
3. **Alignment with Upstream Crossref Taxonomy:**
   Crossref REST API distinguishes between `type: "correction"` (Record 17269) and `type: "retraction"` (Record 4036). OpenPaperCheck respects this distinction directly.

## Consequences
- **Positive:** Deterministic, legally defensible, and reproducible benchmark across all boundary cases.
- **Positive:** Real-world citing papers from 2004–2010 (such as `10.1111/j.1467-9566.2007.00544.x`) pass validation without arbitrary manual overrides.
- **Positive:** Authors who cite papers that published a standard erratum/corrigendum are never falsely flagged as citing discredited research.
- **Negative:** Users who want to know specifically if a paper was cited after an *Expression of Concern* must inspect the notice reasons and external authority links, as the primary comparative anchor prioritizes the final retraction.


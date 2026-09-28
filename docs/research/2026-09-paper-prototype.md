# Research Note: T1 Evidence Card Paper Prototype Testing

**Date:** 2026-09-28  
**Author:** Maintainer  
**Status:** Complete  
**Scope:** Usability test of the Task Type T1 ("Verify Retraction Notice") card prototype.

---

## 1. Prototype Overview & Card Design
The T1 evidence card asks a reviewer to confirm whether a specific external notice applies to a given paper. It is intentionally designed to prevent subjective accusations:

```text
┌────────────────────────────────────────────────────────────────────────────┐
│ EVIDENCE VERIFICATION: Task #T1-1042                                       │
│                                                                            │
│ Target DOI: 10.1016/s0140-6736(97)11096-0                                  │
│ Target Title: Ileal-lymphoid-nodular hyperplasia, non-specific colitis...  │
│ Journal: The Lancet (1998)                                                 │
│                                                                            │
│ Extracted Notice Fact:                                                     │
│ - Retraction Notice DOI: 10.1016/s0140-6736(10)60175-4                     │
│ - External Source: Retraction Watch (Record #1001)                         │
│ - External Date: 2010-02-06                                                │
│ - Notice URL: [Open Official Notice Link in New Tab ↗]                     │
│                                                                            │
│ Question for Reviewer:                                                     │
│ "Does the linked notice explicitly declare that the target paper is        │
│ retracted, withdrawn, or subject to an expression of concern?"             │
│                                                                            │
│ [ (A) Yes - Confirms Retraction / Withdrawal ]                             │
│ [ (B) Yes - Confirms Expression of Concern / Erratum Only ]                │
│ [ (C) No - Notice does not refer to target paper ]                         │
│ [ (D) Unclear / Paywalled Notice (Need Senior Review) ]                    │
│                                                                            │
│ Optional Notes (max 140 chars, no accusations): [                        ] │
│                                                [ Submit Review ]           │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Tester Profiles & Testing Protocol
We presented printed mockups of the card across 3 distinct test scenarios (Clear Retraction, Erratum/Correction, and Broken/Paywalled Link) to three volunteers:
1. **Tester 1 (PhD Student in Biomedical Sciences):** Frequent paper reader; checks references before citing.
2. **Tester 2 (Academic Science Librarian):** Expert in bibliographic metadata and persistent identifiers.
3. **Tester 3 (Post-Doctoral Fellow in CS):** Regular peer reviewer and preprint reader.

---

## 3. Observations & Tester Feedback

### Tester 1 (PhD Student)
- **Positive:** Loved that the question is strictly factual (*"Does the linked notice explicitly declare..."*) rather than asking *"Is this paper fraudulent?"*
- **Friction:** Initially asked: *"What if the link doesn't open or requires an institutional proxy?"*
- **Action taken:** Added Option D: *"Unclear / Paywalled Notice"* so reviewers never guess when an external link fails.

### Tester 2 (Librarian)
- **Positive:** Appreciated the distinction between full retraction and erratum/expression of concern.
- **Friction:** Pointed out that sometimes a notice is titled "Correction" but in the body says "The authors retract...".
- **Action taken:** Emphasized in instructions that the operative wording inside the notice governs the label.

### Tester 3 (Post-Doc)
- **Positive:** Liked the character limit on optional notes to prevent essay writing and personal attacks.
- **Friction:** Asked: *"Will my name show on the public page if I review this?"*
- **Action taken:** Added explicit reassurance: *"Reviews are pseudonymous. Your email is never public."* (Enforcing non-negotiable #7).

---

## 4. Key Decisions & Next Steps
1. The 4-option breakdown (Retraction, Expression of Concern, Mismatch, Unclear/Paywalled) was accepted by all 3 participants with zero confusion.
2. The card wording satisfies `ETHICS.md` non-negotiable #1 (attribute, don't accuse) and #5 (humans decide).
3. Wireframe finalized for frontend implementation in Milestone M3 (Week 5).

"""
Core Data Models and State Enums for OpenPaperCheck.
Shared between CLI and Server runtimes.
"""

from __future__ import annotations

from enum import Enum
from typing import Any


class PaperPublicState(str, Enum):
    """
    Standard 4 public states for paper integrity facts.
    Strictly defined in TECH_STACK.md and MASTER_PLAN.md.
    """

    RETRACTED_EXTERNAL = "retracted_external"
    NEEDS_REVIEW = "needs_review"
    NO_FLAGS_FOUND = "no_flags_found"
    INSUFFICIENT_DATA = "insufficient_data"


def determine_paper_state(
    paper_retraction: dict[str, Any] | None,
    references_data: dict[str, Any] | None,
    retracted_refs_map: dict[str, dict[str, Any]],
) -> PaperPublicState:
    """
    Deterministically evaluate a paper's public state based on sourced facts.

    Logic:
    1. If the target paper itself is retracted by an external authority -> RETRACTED_EXTERNAL
    2. If any cited reference is retracted -> NEEDS_REVIEW
    3. If reference deposits were restricted or missing -> INSUFFICIENT_DATA
    4. If references were deposited and zero retractions found -> NO_FLAGS_FOUND
    """
    if paper_retraction is not None:
        nature = paper_retraction.get("nature", "Retraction")
        if nature == "Retraction":
            return PaperPublicState.RETRACTED_EXTERNAL
        elif nature == "Expression of concern":
            return PaperPublicState.NEEDS_REVIEW
        # If nature is 'Correction' or 'Reinstatement', target paper is not discredited;
        # proceed to check its references.

    if len(retracted_refs_map) > 0:
        return PaperPublicState.NEEDS_REVIEW

    if references_data is None:
        return PaperPublicState.INSUFFICIENT_DATA

    deposit_status = references_data.get("deposit_status", "missing")
    if deposit_status in ("restricted", "missing"):
        return PaperPublicState.INSUFFICIENT_DATA

    return PaperPublicState.NO_FLAGS_FOUND


class CitationTiming(str, Enum):
    """
    Per-reference timing classification.
    Determined per-flagged reference rather than at the paper level,
    to prevent invalid state collapse when a paper cites multiple
    retracted references with conflicting timelines.
    """

    CITED_AFTER_RETRACTION = "cited_after_retraction"
    CITED_BEFORE_RETRACTION = "cited_before_retraction"
    UNKNOWN = "unknown"


def evaluate_citation_timing(
    pub_date: str | None,
    retraction_date: str | None,
) -> CitationTiming:
    """
    Evaluate the citation timing for an individual reference.

    Args:
        pub_date: ISO date or partial date of citing paper (e.g. '2021-06-25', '2007-03-01', '2015')
        retraction_date: ISO date of retraction notice (e.g. '2010-02-06')

    Returns:
        CitationTiming: CITED_AFTER_RETRACTION, CITED_BEFORE_RETRACTION, or UNKNOWN
    """
    if (
        not pub_date
        or not retraction_date
        or retraction_date.strip().lower() in ("date unknown", "unknown", "")
    ):
        return CitationTiming.UNKNOWN

    clean_pub = pub_date.strip()
    clean_ret = retraction_date.strip()

    # Compare up to the shared precision length (e.g. YYYY vs YYYY or YYYY-MM vs YYYY-MM)
    # If comparing full ISO dates YYYY-MM-DD
    if len(clean_pub) >= 10 and len(clean_ret) >= 10:
        if clean_pub[:10] > clean_ret[:10]:
            return CitationTiming.CITED_AFTER_RETRACTION
        return CitationTiming.CITED_BEFORE_RETRACTION

    # Partial date comparison (e.g. year-only '2021' vs '2020-06-05')
    comp_len = min(len(clean_pub), len(clean_ret), 10)
    if clean_pub[:comp_len] > clean_ret[:comp_len]:
        return CitationTiming.CITED_AFTER_RETRACTION
    elif clean_pub[:comp_len] < clean_ret[:comp_len]:
        return CitationTiming.CITED_BEFORE_RETRACTION

    # If prefixes match (e.g. both start with '2020'), but one is more specific,
    # default to before retraction to prevent falsely accusing authors without full day proof
    return CitationTiming.CITED_BEFORE_RETRACTION

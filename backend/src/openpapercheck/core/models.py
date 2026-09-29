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
        return PaperPublicState.RETRACTED_EXTERNAL

    if len(retracted_refs_map) > 0:
        return PaperPublicState.NEEDS_REVIEW

    if references_data is None:
        return PaperPublicState.INSUFFICIENT_DATA

    deposit_status = references_data.get("deposit_status", "missing")
    if deposit_status in ("restricted", "missing"):
        return PaperPublicState.INSUFFICIENT_DATA

    return PaperPublicState.NO_FLAGS_FOUND

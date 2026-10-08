"""
Deterministic Majority-of-3 Consensus Algorithm for OpenPaperCheck.
Strictly implements the specification in docs/DATABASE.md Section 6.
"""

from __future__ import annotations

from collections import Counter
from typing import Any


def decide(votes: list[str], required: int = 3) -> dict[str, Any]:
    """
    Decide outcome from a list of votes ('yes', 'no', 'unsure').

    Rules:
    - If total votes < required: returns {"status": "waiting"}
    - If 2 or more votes agree on 'yes' or 'no': returns {"status": "decided", "label": ...}
    - 'unsure' NEVER becomes a public label by itself.
    - If no majority or 2+ votes are 'unsure': returns {"status": "needs_senior"}
    - Fully deterministic and permutation-invariant.
    """
    if len(votes) < required:
        return {
            "status": "waiting",
            "votes_count": len(votes),
            "required": required,
        }

    clean_votes = [v.lower().strip() for v in votes]
    counts = Counter(clean_votes)
    top_verdict, n_top = counts.most_common(1)[0]

    # Majority requires at least 2 votes on 'yes' or 'no'
    if top_verdict in ("yes", "no") and n_top >= 2:
        return {
            "status": "decided",
            "label": top_verdict,
            "n_agree": n_top,
            "agreement": round(n_top / len(clean_votes), 3),
            "method": "majority_3",
        }

    # Tie (e.g. 1 yes, 1 no, 1 unsure) or majority unsure (>=2 unsure) escalates to senior
    return {
        "status": "needs_senior",
        "votes_count": len(clean_votes),
        "breakdown": dict(counts),
        "reason": "no_conclusive_majority" if top_verdict != "unsure" else "unsure_majority",
    }

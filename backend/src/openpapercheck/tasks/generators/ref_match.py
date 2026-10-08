"""
Task Generator for T1: Reference Match (ref_match).
"Is the reference text the same paper as the matched record?"
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from sqlalchemy.orm import Session as DBSession

from openpapercheck.core.doi import normalize_doi
from openpapercheck.server.models import GoldTask, ReviewTask


def compute_payload_hash(payload: dict[str, Any]) -> str:
    """Compute deterministic SHA-256 hash of task payload."""
    serialized = json.dumps(payload, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def create_ref_match_task(
    db: DBSession,
    citing_paper_doi: str,
    raw_reference: str,
    candidate_title: str,
    candidate_doi: str,
    candidate_year: int | str | None = None,
    candidate_journal: str | None = None,
    subject: str | None = None,
    priority: int = 0,
    is_gold: bool = False,
    gold_correct_verdict: str | None = None,
    gold_explanation: str | None = None,
) -> ReviewTask:
    """
    Generate and persist a T1 (ref_match) review task in the database.
    Idempotent: returns existing task if identical payload_hash exists.
    """
    clean_citing_doi = normalize_doi(citing_paper_doi) or citing_paper_doi.lower()
    clean_cand_doi = normalize_doi(candidate_doi) or candidate_doi.lower()

    payload = {
        "question": "Is the reference text the same paper as the matched record?",
        "task_type": "ref_match",
        "raw_reference": raw_reference.strip(),
        "matched_record": {
            "title": candidate_title.strip(),
            "doi": clean_cand_doi,
            "year": str(candidate_year) if candidate_year else None,
            "journal": candidate_journal.strip() if candidate_journal else None,
            "url": f"https://doi.org/{clean_cand_doi}",
        },
        "citing_paper_doi": clean_citing_doi,
        "options": [
            {"verdict": "yes", "label": "Same paper"},
            {"verdict": "no", "label": "Different paper"},
            {"verdict": "unsure", "label": "Not sure"},
        ],
    }

    p_hash = compute_payload_hash(payload)

    # Check for existing duplicate task
    existing = (
        db.query(ReviewTask)
        .filter(ReviewTask.task_type == "ref_match", ReviewTask.payload_hash == p_hash)
        .first()
    )
    if existing:
        return existing

    task = ReviewTask(
        paper_doi=clean_citing_doi,
        task_type="ref_match",
        payload=payload,
        payload_hash=p_hash,
        difficulty=1,
        subject=subject,
        language="en",
        status="open",
        required_reviews=3,
        priority=priority,
        is_gold=is_gold,
    )
    db.add(task)
    db.flush()

    if is_gold and gold_correct_verdict and gold_explanation:
        gold = GoldTask(
            task_id=task.id,
            correct_verdict=gold_correct_verdict,
            explanation=gold_explanation,
        )
        db.add(gold)

    db.commit()
    db.refresh(task)
    return task

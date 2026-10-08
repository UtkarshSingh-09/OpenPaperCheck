"""
Review recording and consensus evaluation engine.
Orchestrates reviewer vote recording, consensus triggers, and statistics updates.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session as DBSession

from openpapercheck.consensus.majority import decide
from openpapercheck.server.models import (
    ConsensusLabel,
    Review,
    ReviewerStats,
    ReviewTask,
    TaskAssignment,
    User,
)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def submit_review(
    db: DBSession,
    task_id: str,
    reviewer_id: str,
    verdict: str,
    note: str | None = None,
    duration_ms: int | None = None,
) -> dict[str, Any]:
    """
    Record an independent vote on a task, evaluate gold feedback,
    and trigger consensus calculation if threshold is met.
    """
    clean_verdict = verdict.strip().lower()
    if clean_verdict not in ("yes", "no", "unsure"):
        raise ValueError(f"Invalid verdict: '{verdict}'. Must be 'yes', 'no', or 'unsure'.")

    task = db.query(ReviewTask).filter(ReviewTask.id == task_id).first()
    if not task:
        raise ValueError(f"Task '{task_id}' not found.")

    reviewer = db.query(User).filter(User.id == reviewer_id).first()
    if not reviewer:
        raise ValueError(f"Reviewer '{reviewer_id}' not found.")

    # 1. Update lease assignment to 'done'
    assignment = (
        db.query(TaskAssignment)
        .filter(
            TaskAssignment.task_id == task_id,
            TaskAssignment.reviewer_id == reviewer_id,
        )
        .first()
    )
    if assignment:
        assignment.status = "done"

    # 2. Check for duplicate review
    existing_review = (
        db.query(Review)
        .filter(Review.task_id == task_id, Review.reviewer_id == reviewer_id)
        .first()
    )
    if existing_review:
        raise ValueError("Reviewer has already submitted a review for this task.")

    # 3. Create Review record
    review = Review(
        task_id=task.id,
        reviewer_id=reviewer.id,
        verdict=clean_verdict,
        note=note[:500] if note else None,
        duration_ms=duration_ms,
        reviewer_level_at_time=reviewer.level,
        created_at=utcnow(),
    )
    db.add(review)

    # 4. Update ReviewerStats
    stats = db.query(ReviewerStats).filter(ReviewerStats.user_id == reviewer.id).first()
    if not stats:
        stats = ReviewerStats(user_id=reviewer.id)
        db.add(stats)

    stats.reviews_total += 1
    stats.weekly_count += 1
    stats.updated_at = utcnow()

    # 5. Handle Gold Task feedback if applicable
    gold_feedback = None
    if task.is_gold and task.gold:
        is_correct = clean_verdict == task.gold.correct_verdict
        stats.gold_seen += 1
        if is_correct:
            stats.gold_correct += 1

        gold_feedback = {
            "is_gold": True,
            "correct_verdict": task.gold.correct_verdict,
            "was_correct": is_correct,
            "explanation": task.gold.explanation,
        }

    db.commit()

    # 6. Check Consensus
    all_reviews = db.query(Review).filter(Review.task_id == task.id).all()
    votes = [r.verdict for r in all_reviews]

    consensus_result = decide(votes, required=task.required_reviews)

    if consensus_result["status"] == "decided":
        task.status = "decided"
        task.decided_at = utcnow()

        # Write or update consensus label
        label = db.query(ConsensusLabel).filter(ConsensusLabel.task_id == task.id).first()
        if not label:
            label = ConsensusLabel(
                task_id=task.id,
                paper_doi=task.paper_doi,
                task_type=task.task_type,
                label=consensus_result["label"],
                n_reviews=len(votes),
                n_agree=consensus_result["n_agree"],
                agreement=consensus_result["agreement"],
                method=consensus_result["method"],
                decided_at=utcnow(),
            )
            db.add(label)

        # Update agreement stats for participating reviewers
        for r in all_reviews:
            if r.reviewer_id:
                r_stats = (
                    db.query(ReviewerStats).filter(ReviewerStats.user_id == r.reviewer_id).first()
                )
                if r_stats:
                    r_stats.decided_seen += 1
                    if r.verdict == consensus_result["label"]:
                        r_stats.agree_with_consensus += 1
                    r_stats.updated_at = utcnow()

        db.commit()

    elif consensus_result["status"] == "needs_senior":
        task.status = "needs_senior"
        db.commit()

    return {
        "status": "success",
        "review_id": review.id,
        "task_status": task.status,
        "consensus": consensus_result,
        "gold_feedback": gold_feedback,
    }

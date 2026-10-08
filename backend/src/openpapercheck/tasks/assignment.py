"""
Task leasing and queue assignment for OpenPaperCheck.
Enforces reviewer independence, 30-minute leases, and level matching.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session as DBSession

from openpapercheck.server.models import Review, ReviewTask, TaskAssignment, User
from openpapercheck.server.settings import settings


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def cleanup_expired_leases(db: DBSession) -> int:
    """Flip active leases that have passed their deadline to 'expired'."""
    now = utcnow()
    expired = (
        db.query(TaskAssignment)
        .filter(TaskAssignment.status == "assigned", TaskAssignment.expires_at < now)
        .all()
    )
    for a in expired:
        a.status = "expired"
    if expired:
        db.commit()
    return len(expired)


def get_next_task_for_reviewer(db: DBSession, user: User) -> tuple[ReviewTask | None, TaskAssignment | None]:
    """
    Find and lease the highest-priority pending task suitable for this reviewer.

    Rules:
    - Reviewer has not already reviewed or been assigned this task
    - Task difficulty <= user level
    - Task status is 'open' or 'in_review'
    - Total valid assignments/reviews < required_reviews
    """
    cleanup_expired_leases(db)
    now = utcnow()

    # Find tasks where user has no active or done assignment
    subquery_assigned = select(TaskAssignment.task_id).filter(
        TaskAssignment.reviewer_id == user.id,
        TaskAssignment.status.in_(["assigned", "done", "skipped"]),
    )

    candidate_tasks = (
        db.query(ReviewTask)
        .filter(
            ReviewTask.status.in_(["open", "in_review"]),
            ReviewTask.difficulty <= user.level,
            ~ReviewTask.id.in_(subquery_assigned),
        )
        .order_by(ReviewTask.priority.desc(), ReviewTask.created_at.asc())
        .limit(20)
        .all()
    )

    for task in candidate_tasks:
        # Check active non-expired assignments + completed reviews
        active_assignments_count = (
            db.query(TaskAssignment)
            .filter(
                TaskAssignment.task_id == task.id,
                or_(
                    TaskAssignment.status == "done",
                    and_(TaskAssignment.status == "assigned", TaskAssignment.expires_at > now),
                ),
            )
            .count()
        )

        if active_assignments_count < task.required_reviews:
            # Create a 30-minute lease for this user
            lease_expires = now + timedelta(minutes=settings.DEFAULT_LEASE_MINUTES)
            assignment = TaskAssignment(
                task_id=task.id,
                reviewer_id=user.id,
                assigned_at=now,
                expires_at=lease_expires,
                status="assigned",
            )
            db.add(assignment)
            task.status = "in_review"
            db.commit()
            db.refresh(task)
            db.refresh(assignment)
            return task, assignment

    return None, None


def skip_assigned_task(db: DBSession, task_id: str, user_id: str) -> bool:
    """Mark an assigned task as skipped by the reviewer."""
    assignment = (
        db.query(TaskAssignment)
        .filter(
            TaskAssignment.task_id == task_id,
            TaskAssignment.reviewer_id == user_id,
            TaskAssignment.status == "assigned",
        )
        .first()
    )
    if assignment:
        assignment.status = "skipped"
        db.commit()
        return True
    return False

"""
Reviewer Profile, Stats, and Data Privacy Endpoints (v1).
Provides GET /v1/me, POST /v1/me/tutorial-complete, DELETE /v1/me, GET /v1/me/export.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from openpapercheck.api.deps import get_current_user
from openpapercheck.server.db import get_db
from openpapercheck.server.models import AuditLog, AuthIdentity, Review, ReviewerStats, Session as UserSession, User
from openpapercheck.server.settings import settings

router = APIRouter(prefix="/me", tags=["Reviewer Profile"])


class ReviewerStatsResponse(BaseModel):
    reviews_total: int
    weekly_count: int
    gold_seen: int
    gold_correct: int
    gold_accuracy: float | None
    agree_with_consensus: int
    decided_seen: int
    consensus_agreement_rate: float | None


class MeProfileResponse(BaseModel):
    id: str
    display_name: str
    role: str
    level: int
    languages: list[str]
    fields: list[str]
    tutorial_done: bool
    joined_at: str
    stats: ReviewerStatsResponse


@router.get(
    "",
    response_model=MeProfileResponse,
    summary="Get current reviewer profile and private statistics",
)
def get_me(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MeProfileResponse:
    stats = db.query(ReviewerStats).filter(ReviewerStats.user_id == user.id).first()
    if not stats:
        stats = ReviewerStats(user_id=user.id)
        db.add(stats)
        db.commit()
        db.refresh(stats)

    gold_acc = None
    if stats.gold_seen > 0:
        gold_acc = round((stats.gold_correct / stats.gold_seen) * 100, 1)

    agree_rate = None
    if stats.decided_seen > 0:
        agree_rate = round((stats.agree_with_consensus / stats.decided_seen) * 100, 1)

    return MeProfileResponse(
        id=user.id,
        display_name=user.display_name,
        role=user.role,
        level=user.level,
        languages=user.languages or ["en"],
        fields=user.fields or [],
        tutorial_done=bool(user.tutorial_done_at),
        joined_at=user.joined_at.isoformat(),
        stats=ReviewerStatsResponse(
            reviews_total=stats.reviews_total,
            weekly_count=stats.weekly_count,
            gold_seen=stats.gold_seen,
            gold_correct=stats.gold_correct,
            gold_accuracy=gold_acc,
            agree_with_consensus=stats.agree_with_consensus,
            decided_seen=stats.decided_seen,
            consensus_agreement_rate=agree_rate,
        ),
    )


@router.post(
    "/tutorial-complete",
    summary="Mark reviewer onboarding tutorial as completed",
)
def complete_tutorial(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    if not user.tutorial_done_at:
        user.tutorial_done_at = datetime.now(timezone.utc)
        db.commit()
    return {"status": "ok", "tutorial_done_at": user.tutorial_done_at.isoformat()}


@router.delete(
    "",
    summary="Delete reviewer account and personal contact data (GDPR/Privacy compliant)",
)
def delete_account(
    response: Response,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    Deletes email and sessions. Anonymizes past review submissions.
    """
    # 1. Log audit action
    audit = AuditLog(
        actor_id=user.id,
        action="account_deletion",
        target_type="user",
        target_id=user.id,
        details={"display_name": user.display_name},
    )
    db.add(audit)

    # 2. Anonymize user reviews
    db.query(Review).filter(Review.reviewer_id == user.id).update(
        {"reviewer_id": None}, synchronize_session=False
    )

    # 3. Delete auth identity (email) and sessions
    db.query(AuthIdentity).filter(AuthIdentity.user_id == user.id).delete()
    db.query(UserSession).filter(UserSession.user_id == user.id).delete()

    # 4. Mark user deleted
    user.status = "deleted"
    user.display_name = f"deleted_user_{user.id[:8]}"
    db.commit()

    response.delete_cookie(settings.SESSION_COOKIE_NAME)
    return {"status": "ok", "message": "Account successfully deleted"}


@router.get(
    "/export",
    summary="Export all stored personal and review data in JSON format",
)
def export_data(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    identities = db.query(AuthIdentity).filter(AuthIdentity.user_id == user.id).all()
    stats = db.query(ReviewerStats).filter(ReviewerStats.user_id == user.id).first()
    reviews = db.query(Review).filter(Review.reviewer_id == user.id).all()

    return {
        "user": {
            "id": user.id,
            "display_name": user.display_name,
            "role": user.role,
            "level": user.level,
            "joined_at": user.joined_at.isoformat(),
        },
        "identities": [
            {"provider": i.provider, "email": i.email} for i in identities
        ],
        "stats": {
            "reviews_total": stats.reviews_total if stats else 0,
            "gold_correct": stats.gold_correct if stats else 0,
        },
        "reviews": [
            {
                "task_id": r.task_id,
                "verdict": r.verdict,
                "created_at": r.created_at.isoformat(),
            }
            for r in reviews
        ],
    }

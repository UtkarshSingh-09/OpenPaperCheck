"""
Review Tasks Endpoints for OpenPaperCheck REST API (v1).
Provides GET /v1/tasks/next, POST /v1/tasks/{id}/reviews, POST /v1/tasks/{id}/skip
"""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from openpapercheck.api.deps import get_current_user
from openpapercheck.consensus.evaluator import submit_review
from openpapercheck.server.db import get_db
from openpapercheck.server.models import ReviewTask, User
from openpapercheck.tasks.assignment import get_next_task_for_reviewer, skip_assigned_task
from openpapercheck.tasks.generators.ref_match import create_ref_match_task

router = APIRouter(prefix="/tasks", tags=["Review Tasks"])


class TaskCardResponse(BaseModel):
    task_id: str
    paper_doi: str
    task_type: str
    difficulty: int
    payload: dict[str, Any]
    expires_at: str


class SubmitReviewRequest(BaseModel):
    verdict: str = Field(..., description="'yes' | 'no' | 'unsure'")
    note: str | None = Field(None, max_length=500)
    duration_ms: int | None = Field(None, ge=0)


class CreateSampleTaskRequest(BaseModel):
    citing_paper_doi: str
    raw_reference: str
    candidate_title: str
    candidate_doi: str
    candidate_year: int | None = None
    candidate_journal: str | None = None
    is_gold: bool = False
    gold_correct_verdict: str | None = None
    gold_explanation: str | None = None


@router.get(
    "/next",
    response_model=TaskCardResponse | None,
    summary="Fetch and lease the next verification task card for the logged-in reviewer",
)
def get_next_task(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TaskCardResponse | None:
    task, assignment = get_next_task_for_reviewer(db, user)
    if not task or not assignment:
        return None

    return TaskCardResponse(
        task_id=task.id,
        paper_doi=task.paper_doi,
        task_type=task.task_type,
        difficulty=task.difficulty,
        payload=task.payload,
        expires_at=assignment.expires_at.isoformat(),
    )


@router.post(
    "/{task_id}/reviews",
    summary="Submit an independent review verdict on a task card",
)
def submit_task_review(
    task_id: str,
    req: SubmitReviewRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    try:
        result = submit_review(
            db=db,
            task_id=task_id,
            reviewer_id=user.id,
            verdict=req.verdict,
            note=req.note,
            duration_ms=req.duration_ms,
        )
        return result
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.post(
    "/{task_id}/skip",
    summary="Skip an assigned task card and return it to the queue",
)
def skip_task(
    task_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    success = skip_assigned_task(db, task_id, user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active task assignment not found for this user.",
        )
    return {"status": "ok", "message": "Task skipped."}


@router.post(
    "/sample",
    summary="Create a sample T1 reference-matching task (developer / testing utility)",
)
def create_sample_task(
    req: CreateSampleTaskRequest,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    task = create_ref_match_task(
        db=db,
        citing_paper_doi=req.citing_paper_doi,
        raw_reference=req.raw_reference,
        candidate_title=req.candidate_title,
        candidate_doi=req.candidate_doi,
        candidate_year=req.candidate_year,
        candidate_journal=req.candidate_journal,
        is_gold=req.is_gold,
        gold_correct_verdict=req.gold_correct_verdict,
        gold_explanation=req.gold_explanation,
    )
    return {
        "status": "ok",
        "task_id": task.id,
        "is_gold": task.is_gold,
    }

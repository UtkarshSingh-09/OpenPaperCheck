"""
Unit tests for review task generation, leasing, and skipping.
"""

from __future__ import annotations

from datetime import timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from openpapercheck.server.db import Base
from openpapercheck.server.models import TaskAssignment
from openpapercheck.server.security import get_or_create_user, utcnow
from openpapercheck.tasks.assignment import (
    cleanup_expired_leases,
    get_next_task_for_reviewer,
    skip_assigned_task,
)
from openpapercheck.tasks.generators.ref_match import create_ref_match_task


def test_task_generation_and_leasing(tmp_path):
    # Setup test DB
    test_db_url = f"sqlite:///{tmp_path}/test_tasks.db"
    engine = create_engine(test_db_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)
    db = session_factory()

    # 1. Create two users
    u1 = get_or_create_user(db, "alice@example.org", "alice_rev")
    u2 = get_or_create_user(db, "bob@example.org", "bob_rev")

    # 2. Create a T1 task
    task = create_ref_match_task(
        db=db,
        citing_paper_doi="10.1038/nature12373",
        raw_reference="Wakefield AJ. Lancet 1998.",
        candidate_title="Ileal-lymphoid-nodular hyperplasia",
        candidate_doi="10.1016/s0140-6736(97)11096-0",
        candidate_year=1998,
    )
    assert task.status == "open"

    # Idempotent: same payload returns same task
    duplicate = create_ref_match_task(
        db=db,
        citing_paper_doi="10.1038/nature12373",
        raw_reference="Wakefield AJ. Lancet 1998.",
        candidate_title="Ileal-lymphoid-nodular hyperplasia",
        candidate_doi="10.1016/s0140-6736(97)11096-0",
        candidate_year=1998,
    )
    assert duplicate.id == task.id

    # 3. User 1 leases the task
    leased_task, assignment1 = get_next_task_for_reviewer(db, u1)
    assert leased_task is not None
    assert leased_task.id == task.id
    assert assignment1.reviewer_id == u1.id
    assert assignment1.status == "assigned"

    # User 1 cannot lease the same task again
    again_task, _ = get_next_task_for_reviewer(db, u1)
    assert again_task is None

    # 4. User 2 can lease the same task independently (task requires 3 reviews)
    leased_task2, assignment2 = get_next_task_for_reviewer(db, u2)
    assert leased_task2 is not None
    assert leased_task2.id == task.id
    assert assignment2.reviewer_id == u2.id

    # 5. Test skip
    assert skip_assigned_task(db, task.id, u2.id) is True
    assignment2_refreshed = (
        db.query(TaskAssignment)
        .filter(TaskAssignment.task_id == task.id, TaskAssignment.reviewer_id == u2.id)
        .first()
    )
    assert assignment2_refreshed.status == "skipped"

    # 6. Test lease expiration
    assignment1.expires_at = utcnow() - timedelta(minutes=5)
    db.commit()
    expired_count = cleanup_expired_leases(db)
    assert expired_count == 1
    db.refresh(assignment1)
    assert assignment1.status == "expired"

    db.close()

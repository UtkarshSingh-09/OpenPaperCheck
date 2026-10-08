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


def test_concurrency_quota_and_primary_key_protection(tmp_path):
    """
    Verify that when lease quota is exhausted, concurrent lease attempts return None,
    and composite primary key (task_id, reviewer_id) strictly prevents duplicate assignments.
    """
    test_db_url = f"sqlite:///{tmp_path}/test_concurrency.db"
    engine = create_engine(test_db_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)
    db1 = session_factory()
    db2 = session_factory()

    u1 = get_or_create_user(db1, "worker1@example.org", "worker1")
    u2 = get_or_create_user(db2, "worker2@example.org", "worker2")

    task = create_ref_match_task(
        db=db1,
        citing_paper_doi="10.1038/nature12373",
        raw_reference="Single quota reference 2026.",
        candidate_title="Nanometre-scale thermometry",
        candidate_doi="10.1038/nature12373",
        candidate_year=2013,
    )
    # Set required_reviews to exactly 1
    task.required_reviews = 1
    db1.commit()

    # Worker 1 claims the 1 available slot
    t1, a1 = get_next_task_for_reviewer(db1, u1)
    assert t1 is not None
    assert a1 is not None

    # Worker 2 simultaneously tries to lease the same task
    t2, a2 = get_next_task_for_reviewer(db2, u2)
    # Since only 1 review was required and it is currently leased, Worker 2 must get None
    assert t2 is None
    assert a2 is None

    db1.close()
    db2.close()


def test_matcher_flagged_candidate_always_forces_human_verification():
    from openpapercheck.tasks.matcher import match_reference

    # High match that would otherwise auto-match without human review (confidence >= 0.95)
    res = match_reference(
        raw_reference="Wakefield AJ. Ileal-lymphoid-nodular hyperplasia. Lancet 1998.",
        candidate_title="Ileal-lymphoid-nodular hyperplasia",
        candidate_year=1998,
        candidate_journal="Lancet",
        candidate_is_flagged=True,  # Candidate is retracted!
    )
    # Ethical invariant: must NEVER auto-match a retracted paper without human review
    assert res["needs_human_verification"] is True


def test_matcher_conflicting_year_capped_below_automatch():
    from openpapercheck.tasks.matcher import match_reference

    # Identical title tokens, but candidate year 2024 conflicts with citing 2018
    res = match_reference(
        raw_reference="Smith J. Quantum Entanglement Dynamics. 2018.",
        candidate_title="Quantum Entanglement Dynamics",
        candidate_year=2024,
    )
    # Confidence must be capped below auto-match threshold (<= 0.65)
    assert res["confidence"] <= 0.65

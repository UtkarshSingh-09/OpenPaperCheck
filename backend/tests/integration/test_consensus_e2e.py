"""
End-to-End Integration Test for Week 5 Definition of Done (DoD).
Validates: Create task -> 3 test users vote -> consensus row written -> reviewer stats updated.
Also validates Gold task feedback and GDPR account deletion.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from openpapercheck.api.main import create_app
from openpapercheck.server.db import Base, get_db
from openpapercheck.server.models import ConsensusLabel, Review, ReviewTask


@pytest.fixture
def client_and_db(tmp_path):
    test_db_url = f"sqlite:///{tmp_path}/test_e2e.db"
    engine = create_engine(test_db_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    app = create_app()

    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client, session_factory


def test_consensus_e2e_three_reviewers_decide_task(client_and_db):
    client, session_factory = client_and_db

    # 1. Create a sample T1 task
    task_res = client.post(
        "/v1/tasks/sample",
        json={
            "citing_paper_doi": "10.1038/nature12373",
            "raw_reference": "Wakefield AJ. Ileal-lymphoid-nodular hyperplasia. Lancet 1998.",
            "candidate_title": "Ileal-lymphoid-nodular hyperplasia, non-specific colitis",
            "candidate_doi": "10.1016/s0140-6736(97)11096-0",
            "candidate_year": 1998,
            "candidate_journal": "Lancet",
        },
    )
    assert task_res.status_code == 200
    task_id = task_res.json()["task_id"]

    # 2. Reviewer 1 (Alice) logs in, fetches task, votes 'yes'
    client.cookies.clear()
    alice_login = client.post(
        "/v1/auth/login",
        json={"email": "alice@example.org", "display_name": "alice_reviewer"},
    )
    assert alice_login.status_code == 200

    alice_task = client.get("/v1/tasks/next")
    assert alice_task.status_code == 200
    assert alice_task.json()["task_id"] == task_id

    rev1 = client.post(
        f"/v1/tasks/{task_id}/reviews",
        json={"verdict": "yes", "note": "Exact match in Lancet", "duration_ms": 3200},
    )
    assert rev1.status_code == 200
    assert rev1.json()["task_status"] == "in_review"

    # 3. Reviewer 2 (Bob) logs in, fetches task, votes 'yes'
    client.cookies.clear()
    bob_login = client.post(
        "/v1/auth/login",
        json={"email": "bob@example.org", "display_name": "bob_reviewer"},
    )
    assert bob_login.status_code == 200

    bob_task = client.get("/v1/tasks/next")
    assert bob_task.status_code == 200
    assert bob_task.json()["task_id"] == task_id

    rev2 = client.post(
        f"/v1/tasks/{task_id}/reviews",
        json={"verdict": "yes", "duration_ms": 4500},
    )
    assert rev2.status_code == 200
    assert rev2.json()["task_status"] == "in_review"

    # 4. Reviewer 3 (Carol) logs in, fetches task, votes 'no'
    client.cookies.clear()
    carol_login = client.post(
        "/v1/auth/login",
        json={"email": "carol@example.org", "display_name": "carol_reviewer"},
    )
    assert carol_login.status_code == 200

    carol_task = client.get("/v1/tasks/next")
    assert carol_task.status_code == 200
    assert carol_task.json()["task_id"] == task_id

    rev3 = client.post(
        f"/v1/tasks/{task_id}/reviews",
        json={"verdict": "no", "note": "Thought title was cut off", "duration_ms": 5100},
    )
    assert rev3.status_code == 200

    # Task must now be decided!
    review3_data = rev3.json()
    assert review3_data["task_status"] == "decided"
    assert review3_data["consensus"]["status"] == "decided"
    assert review3_data["consensus"]["label"] == "yes"
    assert review3_data["consensus"]["n_agree"] == 2
    assert review3_data["consensus"]["method"] == "majority_3"

    # 5. Verify Database Records directly
    with session_factory() as db:
        db_task = db.query(ReviewTask).filter(ReviewTask.id == task_id).first()
        assert db_task.status == "decided"
        assert db_task.decided_at is not None

        label = db.query(ConsensusLabel).filter(ConsensusLabel.task_id == task_id).first()
        assert label is not None
        assert label.label == "yes"
        assert label.n_reviews == 3
        assert label.n_agree == 2
        assert label.agreement == 0.667

    # 6. Check stats for Carol (minority vote: agreed = 0, decided_seen = 1)
    carol_me = client.get("/v1/me")
    assert carol_me.status_code == 200
    stats = carol_me.json()["stats"]
    assert stats["reviews_total"] == 1
    assert stats["decided_seen"] == 1
    assert stats["agree_with_consensus"] == 0

    # 7. Check stats for Alice (majority vote: agreed = 1, decided_seen = 1)
    client.cookies.clear()
    client.post("/v1/auth/login", json={"email": "alice@example.org"})
    alice_me = client.get("/v1/me")
    alice_stats = alice_me.json()["stats"]
    assert alice_stats["reviews_total"] == 1
    assert alice_stats["decided_seen"] == 1
    assert alice_stats["agree_with_consensus"] == 1
    assert alice_stats["consensus_agreement_rate"] == 100.0


def test_gold_task_feedback_and_accuracy(client_and_db):
    client, session_factory = client_and_db

    # Create a Gold task with ground truth
    gold_res = client.post(
        "/v1/tasks/sample",
        json={
            "citing_paper_doi": "10.1038/nature12373",
            "raw_reference": "Smith J. Nature 2020.",
            "candidate_title": "Original Discovery of Target Gene",
            "candidate_doi": "10.1038/nature04473",
            "candidate_year": 2020,
            "is_gold": True,
            "gold_correct_verdict": "yes",
            "gold_explanation": "Verified gold standard match: title and author match perfectly.",
        },
    )
    gold_task_id = gold_res.json()["task_id"]

    # Log in reviewer
    client.cookies.clear()
    client.post("/v1/auth/login", json={"email": "reviewer_gold@example.org"})

    # Fetch next task
    card = client.get("/v1/tasks/next")
    assert card.status_code == 200
    assert card.json()["task_id"] == gold_task_id

    # Vote correctly
    vote_res = client.post(
        f"/v1/tasks/{gold_task_id}/reviews",
        json={"verdict": "yes", "duration_ms": 2500},
    )
    assert vote_res.status_code == 200
    feedback = vote_res.json()["gold_feedback"]
    assert feedback is not None
    assert feedback["is_gold"] is True
    assert feedback["was_correct"] is True
    assert "Verified gold standard" in feedback["explanation"]

    # Check /v1/me shows 100% gold accuracy
    me_res = client.get("/v1/me")
    stats = me_res.json()["stats"]
    assert stats["gold_seen"] == 1
    assert stats["gold_correct"] == 1
    assert stats["gold_accuracy"] == 100.0


def test_account_deletion_anonymizes_reviews(client_and_db):
    client, session_factory = client_and_db

    # User registers and logs in
    client.cookies.clear()
    client.post(
        "/v1/auth/login", json={"email": "delete_me@example.org", "display_name": "temp_user"}
    )

    # Create task and vote
    t = client.post(
        "/v1/tasks/sample",
        json={
            "citing_paper_doi": "10.1038/nature12373",
            "raw_reference": "Ref text",
            "candidate_title": "Paper Title",
            "candidate_doi": "10.1000/182",
        },
    )
    t_id = t.json()["task_id"]
    client.get("/v1/tasks/next")
    client.post(f"/v1/tasks/{t_id}/reviews", json={"verdict": "yes"})

    # Export data
    export_res = client.get("/v1/me/export")
    assert export_res.status_code == 200
    assert len(export_res.json()["reviews"]) == 1

    # Delete account
    del_res = client.delete("/v1/me")
    assert del_res.status_code == 200

    # User cannot access /v1/me anymore
    after_res = client.get("/v1/me")
    assert after_res.status_code == 401

    # Review in DB is preserved but reviewer_id is anonymized (None)
    with session_factory() as db:
        rev = db.query(Review).filter(Review.task_id == t_id).first()
        assert rev is not None
        assert rev.reviewer_id is None

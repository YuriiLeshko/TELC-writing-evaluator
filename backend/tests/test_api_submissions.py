from __future__ import annotations

import pytest

from backend.evaluation.schemas import (
    CriterionScore,
    ImprovedTextResult,
    WordCountCheck,
    WritingEvaluationResult,
)
from backend.models import Submission, TaskSession


def _fake_result() -> WritingEvaluationResult:
    return WritingEvaluationResult(
        topic_mismatch=False,
        situation_mismatch=False,
        criterion_I=CriterionScore(grade="B", points=3, comment="I"),
        criterion_II=CriterionScore(grade="B", points=3, comment="II"),
        criterion_III=CriterionScore(grade="B", points=3, comment="III"),
        word_count=WordCountCheck(value=160, minimum_required=150, meets_requirement=True),
        improved_text=ImprovedTextResult(improved_text="Verbessert", changes_summary=["Satzbau"]),
        raw_score=9,
        final_score=27,
        max_score=45,
    )


def test_evaluate_submission_success(test_client, seeded_users, seeded_tasks, db_session, monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_evaluate(*args, **kwargs):
        return _fake_result()

    monkeypatch.setattr("backend.routers.submissions.evaluate_writing", fake_evaluate)

    session_resp = test_client.post("/task-sessions/start")
    session_id = session_resp.json()["session"]["id"]
    response = test_client.post(
        "/submissions/evaluate",
        json={
            "task_session_id": session_id,
            "selected_task_type": "info",
            "candidate_text": "Antworttext",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["task_session_id"] == session_id
    assert data["result"]["final_score"] == 27

    user = seeded_users["user"]
    db_session.refresh(user)
    assert user.available_submissions == 4

    session = db_session.get(TaskSession, session_id)
    assert session is not None and session.status == "submitted"


def test_evaluate_submission_no_counter_left(test_client, seeded_users, seeded_tasks, db_session) -> None:
    seeded_users["user"].available_submissions = 0
    db_session.commit()
    session_id = test_client.post("/task-sessions/start").json()["session"]["id"]
    response = test_client.post(
        "/submissions/evaluate",
        json={"task_session_id": session_id, "selected_task_type": "info", "candidate_text": "Antwort"},
    )
    assert response.status_code == 403


def test_evaluate_submission_already_submitted(test_client, seeded_users, seeded_tasks, db_session) -> None:
    session = TaskSession(
        user_id=seeded_users["user"].id,
        info_task_id=seeded_tasks["info_task"].id,
        complaint_task_id=seeded_tasks["complaint_task"].id,
        status="submitted",
    )
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)
    response = test_client.post(
        "/submissions/evaluate",
        json={"task_session_id": session.id, "selected_task_type": "info", "candidate_text": "Antwort"},
    )
    assert response.status_code == 400


def test_evaluate_submission_failure_keeps_counter_and_session(test_client, seeded_users, seeded_tasks, db_session, monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_evaluate(_input):
        raise RuntimeError("boom")

    monkeypatch.setattr("backend.routers.submissions.evaluate_writing", fake_evaluate)
    session_id = test_client.post("/task-sessions/start").json()["session"]["id"]
    response = test_client.post(
        "/submissions/evaluate",
        json={"task_session_id": session_id, "selected_task_type": "info", "candidate_text": "Antwort"},
    )
    assert response.status_code == 500

    user = seeded_users["user"]
    db_session.refresh(user)
    assert user.available_submissions == 5

    session = db_session.get(TaskSession, session_id)
    assert session is not None and session.status == "started"


def test_submissions_list_active_and_delete(test_client, seeded_users, seeded_tasks, db_session, monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_evaluate(*args, **kwargs):
        return _fake_result()

    monkeypatch.setattr("backend.routers.submissions.evaluate_writing", fake_evaluate)
    session_id = test_client.post("/task-sessions/start").json()["session"]["id"]
    test_client.post(
        "/submissions/evaluate",
        json={"task_session_id": session_id, "selected_task_type": "info", "candidate_text": "Antwort"},
    )

    my_resp = test_client.get("/submissions/my")
    active_resp = test_client.get("/submissions/active")
    assert my_resp.status_code == 200
    assert active_resp.status_code == 200
    assert len(my_resp.json()) == 1
    submission_id = my_resp.json()[0]["id"]

    delete_resp = test_client.delete(f"/submissions/{submission_id}")
    assert delete_resp.status_code == 200
    assert delete_resp.json()["status"] == "deleted"

    user = seeded_users["user"]
    db_session.refresh(user)
    assert user.available_submissions == 4
    assert db_session.get(Submission, submission_id) is None

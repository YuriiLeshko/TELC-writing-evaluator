from __future__ import annotations

import pytest
from sqlalchemy import select

from backend.evaluation.schemas import (
    AccuracyDetail,
    CommunicationDetail,
    CriterionScore,
    GrammarErrorSpan,
    ImprovedTextResult,
    KeyPointDetail,
    WordCountCheck,
    WritingEvaluationResult,
)
from backend.models import Submission, TaskSession


def _fake_result() -> WritingEvaluationResult:
    return WritingEvaluationResult(
        topic_mismatch=False,
        situation_mismatch=False,
        criterion_I=CriterionScore(
            grade="B",
            points=3,
            comment="I",
            scaled_points=9,
            max_scaled_points=15,
            key_point_details=[
                KeyPointDetail(
                    key_point="P1",
                    covered=True,
                    status="fulfilled",
                    coverage_quality="strong",
                    sentence_count=2,
                    development="detailed",
                    relevance="direct",
                    situation_appropriate=True,
                    language_level="B2",
                    comment="P1 wird klar erfüllt.",
                )
            ],
        ),
        criterion_II=CriterionScore(
            grade="B",
            points=3,
            comment="II",
            scaled_points=9,
            max_scaled_points=15,
            communication_details=[
                CommunicationDetail(
                    aspect="email_elements",
                    label="E-Mail-Elemente",
                    status="strong",
                    level=None,
                    present_items=["Betreff", "Anrede", "Hauptteil", "Grußformel"],
                    missing_items=["Schluss"],
                    evidence=["Betreff: Beschädigte Lieferung"],
                    comment="Die meisten E-Mail-Elemente sind vorhanden.",
                )
            ],
        ),
        criterion_III=CriterionScore(
            grade="B",
            points=3,
            comment="III",
            scaled_points=9,
            max_scaled_points=15,
            accuracy_details=[
                AccuracyDetail(
                    aspect="grammar",
                    label="Grammatik",
                    status="adequate",
                    error_count=1,
                    evidence=["ein Kopfhörer"],
                    comment="Einzelner Kasusfehler.",
                )
            ],
            highlighted_errors=[
                GrammarErrorSpan(
                    text="ein Kopfhörer",
                    correction="einen Kopfhörer",
                    error_type="Kasusfehler",
                    aspect="agreement",
                    explanation="Akkusativ nach Verb.",
                )
            ],
        ),
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
    assert data["result"]["criterion_I"]["scaled_points"] == 9
    assert len(data["result"]["criterion_I"]["key_point_details"]) == 1
    assert data["result"]["criterion_II"]["scaled_points"] == 9
    assert len(data["result"]["criterion_II"]["communication_details"]) == 1
    assert data["result"]["criterion_III"]["scaled_points"] == 9
    assert len(data["result"]["criterion_III"]["accuracy_details"]) == 1
    assert data["result"]["criterion_III"]["highlighted_errors"][0]["aspect"] == "agreement"

    user = seeded_users["user"]
    db_session.refresh(user)
    assert user.available_submissions == 4

    session = db_session.get(TaskSession, session_id)
    assert session is not None and session.status == "submitted"
    assert session.started_at is not None
    assert session.submitted_at is not None
    assert session.duration_seconds is not None
    assert session.duration_seconds >= 0
    submission = db_session.get(Submission, data["submission_id"])
    assert submission is not None
    assert submission.started_at is not None
    assert submission.submitted_at is not None
    assert submission.duration_seconds is not None
    assert submission.duration_seconds >= 0
    assert submission.duration_seconds == session.duration_seconds
    assert submission.result_json["criterion_I"]["max_scaled_points"] == 15
    assert submission.result_json["criterion_II"]["max_scaled_points"] == 15
    assert submission.result_json["criterion_III"]["max_scaled_points"] == 15


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
    assert session.submitted_at is None
    assert session.duration_seconds is None

    failed_submission = db_session.scalar(
        select(Submission).where(Submission.task_session_id == session_id)
    )
    assert failed_submission is not None
    assert failed_submission.status == "failed"
    assert failed_submission.started_at is not None
    assert failed_submission.submitted_at is not None
    assert failed_submission.duration_seconds is not None
    assert failed_submission.duration_seconds >= 0


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
    assert my_resp.json()[0]["started_at"] is not None
    assert my_resp.json()[0]["submitted_at"] is not None
    assert my_resp.json()[0]["duration_seconds"] is not None
    submission_id = my_resp.json()[0]["id"]

    delete_resp = test_client.delete(f"/submissions/{submission_id}")
    assert delete_resp.status_code == 200
    assert delete_resp.json()["status"] == "deleted"

    user = seeded_users["user"]
    db_session.refresh(user)
    assert user.available_submissions == 4
    assert db_session.get(Submission, submission_id) is None

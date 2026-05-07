from __future__ import annotations

import pytest
from sqlalchemy import select

from backend.evaluation.schemas import (
    CommunicationIndicator,
    CriterionScore,
    GrammarErrorSpan,
    ImprovedTextResult,
    KeyPointDetail,
    TaskAchievementSummary,
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
            task_achievement_summary=TaskAchievementSummary(
                fulfilled_count=1,
                partially_fulfilled_count=0,
                not_fulfilled_count=0,
                own_idea_count=0,
                overall_level="B2",
                summary_comment="1 erfüllt, 0 teilweise erfüllt, 0 nicht erfüllt.",
            ),
            key_point_details=[
                KeyPointDetail(
                    number=1,
                    type="expected",
                    key_point="P1",
                    status="fulfilled",
                    sentence_count=2,
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
            analysis_status="success",
            analysis_error=None,
            communication_indicators=[
                CommunicationIndicator(
                    aspect="email_elements",
                    label="E-Mail-Elemente",
                    rating="good",
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
            highlighted_errors=[
                GrammarErrorSpan(
                    text="ein Kopfhörer",
                    correction="einen Kopfhörer",
                    error_type="Kasusfehler",
                    explanation="Akkusativ nach Verb.",
                )
            ],
        ),
        word_count=WordCountCheck(value=160, minimum_required=150, meets_requirement=True),
        improved_text=ImprovedTextResult(improved_text="Verbessert"),
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
    assert "grade" not in data["result"]["criterion_I"]
    assert "points" not in data["result"]["criterion_I"]
    assert data["result"]["criterion_I"]["task_achievement_summary"]["fulfilled_count"] == 1
    assert data["result"]["criterion_I"]["key_point_details"][0]["number"] == 1
    assert data["result"]["criterion_I"]["key_point_details"][0]["type"] == "expected"
    assert data["result"]["criterion_II"]["scaled_points"] == 9
    assert data["result"]["criterion_II"]["analysis_status"] == "success"
    assert len(data["result"]["criterion_II"]["communication_indicators"]) == 1
    assert "grade" not in data["result"]["criterion_II"]
    assert "points" not in data["result"]["criterion_II"]
    detail = data["result"]["criterion_II"]["communication_indicators"][0]
    assert detail["aspect"] == "email_elements"
    assert detail["label"] == "E-Mail-Elemente"
    assert detail["rating"] == "good"
    assert data["result"]["criterion_III"]["scaled_points"] == 9
    assert data["result"]["criterion_III"]["aspect_ratings"] is None
    assert "grade" not in data["result"]["criterion_III"]
    assert "points" not in data["result"]["criterion_III"]
    assert data["result"]["criterion_III"]["highlighted_errors"][0]["error_type"] == "Kasusfehler"
    assert "aspect" not in data["result"]["criterion_III"]["highlighted_errors"][0]

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
    assert submission.result_json["criterion_I"]["task_achievement_summary"]["fulfilled_count"] == 1
    assert "grade" not in submission.result_json["criterion_I"]
    assert "points" not in submission.result_json["criterion_I"]
    assert submission.result_json["criterion_II"]["max_scaled_points"] == 15
    assert submission.result_json["criterion_II"]["communication_indicators"][0]["label"] == "E-Mail-Elemente"
    assert "grade" not in submission.result_json["criterion_II"]
    assert "points" not in submission.result_json["criterion_II"]
    assert submission.result_json["criterion_III"]["max_scaled_points"] == 15
    assert "grade" not in submission.result_json["criterion_III"]
    assert "points" not in submission.result_json["criterion_III"]
    assert "aspect" not in submission.result_json["criterion_III"]["highlighted_errors"][0]


def test_evaluate_submission_result_contract_e2e(
    test_client,
    seeded_users,
    seeded_tasks,
    db_session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_evaluate(*args, **kwargs):
        return _fake_result()

    monkeypatch.setattr("backend.routers.submissions.evaluate_writing", fake_evaluate)

    session_id = test_client.post("/task-sessions/start").json()["session"]["id"]
    evaluate_resp = test_client.post(
        "/submissions/evaluate",
        json={
            "task_session_id": session_id,
            "selected_task_type": "info",
            "candidate_text": "Antworttext",
        },
    )
    assert evaluate_resp.status_code == 200
    payload = evaluate_resp.json()
    result = payload["result"]

    assert set(result["criterion_I"].keys()) == {
        "scaled_points",
        "max_scaled_points",
        "comment",
        "task_achievement_summary",
        "key_point_details",
    }
    assert set(result["criterion_II"].keys()) == {
        "scaled_points",
        "max_scaled_points",
        "comment",
        "analysis_status",
        "analysis_error",
        "communication_indicators",
    }
    assert set(result["criterion_III"].keys()) == {
        "scaled_points",
        "max_scaled_points",
        "comment",
        "aspect_ratings",
        "highlighted_errors",
    }
    assert "word_count" in result
    assert "improved_text" in result

    submission = db_session.get(Submission, payload["submission_id"])
    assert submission is not None
    saved = submission.result_json
    assert saved["criterion_I"] == result["criterion_I"]
    assert saved["criterion_II"] == result["criterion_II"]
    assert saved["criterion_III"] == result["criterion_III"]

    list_resp = test_client.get("/submissions/my")
    assert list_resp.status_code == 200
    listed = list_resp.json()
    assert listed and listed[0]["duration_seconds"] is not None
    assert listed[0]["duration_seconds"] >= 0


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

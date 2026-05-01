from __future__ import annotations

from backend.models import ComplaintTask, InfoTask, Submission, TaskSession, User


def test_user_defaults_and_counters(db_session) -> None:
    user = User(email="u1@example.com", hashed_password="demo")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    assert user.role == "user"
    assert user.is_active is True
    assert user.available_sessions == 5
    assert user.available_submissions == 5


def test_task_and_session_and_submission_relationships(db_session) -> None:
    user = User(email="u2@example.com", hashed_password="demo")
    info = InfoTask(
        task_number=1,
        source_text="s1",
        situation_text="si1",
        instruction_text="i1",
        expected_key_points_json=["k1"],
    )
    complaint = ComplaintTask(
        task_number=1,
        source_text="s2",
        situation_text="si2",
        instruction_text="i2",
        expected_key_points_json=["k2"],
    )
    db_session.add_all([user, info, complaint])
    db_session.commit()

    session = TaskSession(
        user_id=user.id,
        info_task_id=info.id,
        complaint_task_id=complaint.id,
        status="started",
    )
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)
    assert session.status == "started"

    submission = Submission(
        user_id=user.id,
        task_session_id=session.id,
        selected_task_type="info",
        selected_task_id=info.id,
        candidate_text="Antwort",
        result_json={"ok": True},
        status="success",
    )
    db_session.add(submission)
    db_session.commit()
    db_session.refresh(submission)
    assert submission.status == "success"

    db_session.refresh(user)
    db_session.refresh(session)
    assert len(user.task_sessions) == 1
    assert len(user.submissions) == 1
    assert session.submission is not None
    assert submission.result_json["ok"] is True

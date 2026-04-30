from __future__ import annotations

from backend.models import TaskSession


def test_start_task_session_updates_counters(test_client, seeded_users, seeded_tasks, db_session) -> None:
    response = test_client.post("/task-sessions/start")
    assert response.status_code == 200
    data = response.json()
    assert data["session"]["status"] == "started"

    user = seeded_users["user"]
    db_session.refresh(user)
    assert user.available_sessions == 4
    assert user.next_info_task_index == 2
    assert user.next_complaint_task_index == 2


def test_start_task_session_no_available_sessions(test_client, seeded_users, seeded_tasks, db_session) -> None:
    user = seeded_users["user"]
    user.available_sessions = 0
    db_session.commit()

    response = test_client.post("/task-sessions/start")
    assert response.status_code == 403
    assert response.json()["detail"] == "No available task sessions left."


def test_get_active_sessions(test_client, seeded_users, seeded_tasks, db_session) -> None:
    test_client.post("/task-sessions/start")
    response = test_client.get("/task-sessions/active")
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_delete_started_session(test_client, seeded_users, seeded_tasks, db_session) -> None:
    created = test_client.post("/task-sessions/start").json()["session"]["id"]
    response = test_client.delete(f"/task-sessions/{created}")
    assert response.status_code == 200
    assert response.json()["status"] == "deleted"


def test_delete_submitted_session_returns_400(test_client, seeded_users, seeded_tasks, db_session) -> None:
    session = TaskSession(
        user_id=seeded_users["user"].id,
        info_task_id=seeded_tasks["info_task"].id,
        complaint_task_id=seeded_tasks["complaint_task"].id,
        status="submitted",
    )
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)

    response = test_client.delete(f"/task-sessions/{session.id}")
    assert response.status_code == 400
    assert response.json()["detail"] == "Submitted sessions cannot be deleted."

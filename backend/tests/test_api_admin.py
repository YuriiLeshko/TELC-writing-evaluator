from __future__ import annotations

from backend.models import ComplaintTask, InfoTask, Submission, TaskSession, User


def test_admin_users_crud_and_counters(test_client, seeded_users, db_session) -> None:
    list_resp = test_client.get("/admin/users")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) >= 2

    create_resp = test_client.post(
        "/admin/users",
        json={
            "email": "created@example.com",
            "username": "created",
            "password": "pwd",
            "role": "user",
            "available_sessions": 2,
            "available_submissions": 3,
            "is_active": True,
        },
    )
    assert create_resp.status_code == 200
    created_id = create_resp.json()["id"]

    patch_resp = test_client.patch(
        f"/admin/users/{created_id}",
        json={"role": "admin", "available_sessions": 10, "is_active": False},
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["role"] == "admin"

    counters_resp = test_client.patch(
        f"/admin/users/{created_id}/counters",
        json={"available_sessions": 20, "available_submissions": 30},
    )
    assert counters_resp.status_code == 200
    assert counters_resp.json()["available_sessions"] == 20

    deactivate_resp = test_client.patch(f"/admin/users/{created_id}/deactivate")
    activate_resp = test_client.patch(f"/admin/users/{created_id}/activate")
    assert deactivate_resp.status_code == 200
    assert activate_resp.status_code == 200


def test_admin_delete_user_deactivates_if_related(test_client, seeded_users, seeded_tasks, db_session) -> None:
    user = seeded_users["user"]
    session = TaskSession(
        user_id=user.id,
        info_task_id=seeded_tasks["info_task"].id,
        complaint_task_id=seeded_tasks["complaint_task"].id,
        status="started",
    )
    db_session.add(session)
    db_session.commit()

    resp = test_client.delete(f"/admin/users/{user.id}")
    assert resp.status_code == 409
    assert "Deactivate the user instead" in resp.json()["detail"]
    db_session.refresh(user)
    assert user.is_active is True


def test_admin_delete_user_hard_deletes_without_relations(test_client, seeded_users, db_session) -> None:
    create_resp = test_client.post(
        "/admin/users",
        json={
            "email": "delete-me@example.com",
            "username": "delete-me",
            "password": "pwd",
            "role": "user",
            "available_sessions": 1,
            "available_submissions": 1,
            "is_active": True,
        },
    )
    assert create_resp.status_code == 200
    user_id = create_resp.json()["id"]

    resp = test_client.delete(f"/admin/users/{user_id}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "deleted"
    assert db_session.get(User, user_id) is None


def test_admin_user_activate_deactivate_persists(test_client, seeded_users, db_session) -> None:
    user = seeded_users["user"]
    deact = test_client.patch(f"/admin/users/{user.id}/deactivate")
    assert deact.status_code == 200
    db_session.refresh(user)
    assert user.is_active is False

    act = test_client.patch(f"/admin/users/{user.id}/activate")
    assert act.status_code == 200
    db_session.refresh(user)
    assert user.is_active is True


def test_admin_manage_info_tasks(test_client, seeded_users, seeded_tasks) -> None:
    list_resp = test_client.get("/admin/info-tasks")
    assert list_resp.status_code == 200

    create_resp = test_client.post(
        "/admin/info-tasks",
        json={
            "source_text": "s",
            "situation_text": "si",
            "instruction_text": "i",
            "expected_key_points": ["a", "b"],
        },
    )
    assert create_resp.status_code == 200
    assert create_resp.json()["task_number"] == 2
    assert create_resp.json()["is_active"] is False
    task_id = create_resp.json()["id"]

    deactivate_resp = test_client.patch(f"/admin/info-tasks/{task_id}/deactivate")
    activate_resp = test_client.patch(f"/admin/info-tasks/{task_id}/activate")
    delete_resp = test_client.delete(f"/admin/info-tasks/{task_id}")
    assert deactivate_resp.status_code == 200
    assert activate_resp.status_code == 200
    assert delete_resp.status_code == 200
    assert delete_resp.json()["status"] == "deleted"


def test_admin_manage_complaint_tasks(test_client, seeded_users, seeded_tasks) -> None:
    list_resp = test_client.get("/admin/complaint-tasks")
    assert list_resp.status_code == 200

    create_resp = test_client.post(
        "/admin/complaint-tasks",
        json={
            "source_text": "s",
            "situation_text": "si",
            "instruction_text": "i",
            "expected_key_points": ["a", "b"],
        },
    )
    assert create_resp.status_code == 200
    assert create_resp.json()["task_number"] == 2
    assert create_resp.json()["is_active"] is False
    task_id = create_resp.json()["id"]

    deactivate_resp = test_client.patch(f"/admin/complaint-tasks/{task_id}/deactivate")
    activate_resp = test_client.patch(f"/admin/complaint-tasks/{task_id}/activate")
    delete_resp = test_client.delete(f"/admin/complaint-tasks/{task_id}")
    assert deactivate_resp.status_code == 200
    assert activate_resp.status_code == 200
    assert delete_resp.status_code == 200
    assert delete_resp.json()["status"] == "deleted"


def test_admin_task_lists_include_inactive_tasks(test_client, seeded_users, seeded_tasks, db_session) -> None:
    info_task = seeded_tasks["info_task"]
    complaint_task = seeded_tasks["complaint_task"]
    info_task.is_active = False
    complaint_task.is_active = False
    db_session.commit()

    info_list_resp = test_client.get("/admin/info-tasks")
    complaint_list_resp = test_client.get("/admin/complaint-tasks")
    assert info_list_resp.status_code == 200
    assert complaint_list_resp.status_code == 200

    info_by_id = {item["id"]: item for item in info_list_resp.json()}
    complaint_by_id = {item["id"]: item for item in complaint_list_resp.json()}
    assert info_by_id[info_task.id]["is_active"] is False
    assert complaint_by_id[complaint_task.id]["is_active"] is False


def test_admin_info_task_activate_deactivate_persists(test_client, seeded_users, seeded_tasks, db_session) -> None:
    task = seeded_tasks["info_task"]
    deact = test_client.patch(f"/admin/info-tasks/{task.id}/deactivate")
    assert deact.status_code == 200
    assert deact.json()["is_active"] is False
    db_session.expire_all()
    reloaded_after_deact = db_session.get(InfoTask, task.id)
    assert reloaded_after_deact is not None
    assert reloaded_after_deact.is_active is False

    act = test_client.patch(f"/admin/info-tasks/{task.id}/activate")
    assert act.status_code == 200
    assert act.json()["is_active"] is True
    db_session.expire_all()
    reloaded_after_act = db_session.get(InfoTask, task.id)
    assert reloaded_after_act is not None
    assert reloaded_after_act.is_active is True


def test_admin_delete_info_task_hard_deletes_when_unused(test_client, seeded_users, db_session) -> None:
    task = InfoTask(
        task_number=99,
        source_text="src",
        situation_text="sit",
        instruction_text="inst",
        expected_key_points_json=["kp"],
        is_active=True,
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)

    resp = test_client.delete(f"/admin/info-tasks/{task.id}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "deleted"
    assert db_session.get(InfoTask, task.id) is None


def test_admin_delete_info_task_returns_error_when_used(test_client, seeded_users, seeded_tasks, db_session) -> None:
    user = seeded_users["user"]
    task = seeded_tasks["info_task"]
    session = TaskSession(
        user_id=user.id,
        info_task_id=task.id,
        complaint_task_id=seeded_tasks["complaint_task"].id,
        status="started",
    )
    db_session.add(session)
    db_session.commit()

    resp = test_client.delete(f"/admin/info-tasks/{task.id}")
    assert resp.status_code == 409
    assert "Deactivate it instead" in resp.json()["detail"]


def test_admin_complaint_task_activate_deactivate_persists(test_client, seeded_users, seeded_tasks, db_session) -> None:
    task = seeded_tasks["complaint_task"]
    deact = test_client.patch(f"/admin/complaint-tasks/{task.id}/deactivate")
    assert deact.status_code == 200
    assert deact.json()["is_active"] is False
    db_session.expire_all()
    reloaded_after_deact = db_session.get(ComplaintTask, task.id)
    assert reloaded_after_deact is not None
    assert reloaded_after_deact.is_active is False

    act = test_client.patch(f"/admin/complaint-tasks/{task.id}/activate")
    assert act.status_code == 200
    assert act.json()["is_active"] is True
    db_session.expire_all()
    reloaded_after_act = db_session.get(ComplaintTask, task.id)
    assert reloaded_after_act is not None
    assert reloaded_after_act.is_active is True


def test_admin_delete_complaint_task_hard_deletes_when_unused(test_client, seeded_users, db_session) -> None:
    task = ComplaintTask(
        task_number=99,
        source_text="src",
        situation_text="sit",
        instruction_text="inst",
        expected_key_points_json=["kp"],
        is_active=True,
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)

    resp = test_client.delete(f"/admin/complaint-tasks/{task.id}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "deleted"
    assert db_session.get(ComplaintTask, task.id) is None


def test_admin_delete_complaint_task_returns_error_when_used(test_client, seeded_users, seeded_tasks, db_session) -> None:
    user = seeded_users["user"]
    task = seeded_tasks["complaint_task"]
    session = TaskSession(
        user_id=user.id,
        info_task_id=seeded_tasks["info_task"].id,
        complaint_task_id=task.id,
        status="started",
    )
    db_session.add(session)
    db_session.commit()
    submission = Submission(
        user_id=user.id,
        task_session_id=session.id,
        selected_task_type="complaint",
        selected_task_id=task.id,
        candidate_text="x",
        result_json={},
    )
    db_session.add(submission)
    db_session.commit()

    resp = test_client.delete(f"/admin/complaint-tasks/{task.id}")
    assert resp.status_code == 409
    assert "Deactivate it instead" in resp.json()["detail"]


def test_admin_create_info_task_numbering_starts_at_one_when_empty(test_client, seeded_users) -> None:
    create_resp = test_client.post(
        "/admin/info-tasks",
        json={
            "source_text": "s",
            "situation_text": "si",
            "instruction_text": "i",
            "expected_key_points": ["a"],
            "is_active": True,
        },
    )
    assert create_resp.status_code == 200
    assert create_resp.json()["task_number"] == 1


def test_admin_create_complaint_task_numbering_starts_at_one_when_empty(test_client, seeded_users) -> None:
    create_resp = test_client.post(
        "/admin/complaint-tasks",
        json={
            "source_text": "s",
            "situation_text": "si",
            "instruction_text": "i",
            "expected_key_points": ["a"],
            "is_active": True,
        },
    )
    assert create_resp.status_code == 200
    assert create_resp.json()["task_number"] == 1


def test_admin_create_info_task_uses_max_plus_one(test_client, seeded_users, seeded_tasks) -> None:
    first = test_client.post(
        "/admin/info-tasks",
        json={
            "source_text": "s1",
            "situation_text": "si1",
            "instruction_text": "i1",
            "expected_key_points": ["a"],
            "is_active": True,
        },
    )
    second = test_client.post(
        "/admin/info-tasks",
        json={
            "source_text": "s2",
            "situation_text": "si2",
            "instruction_text": "i2",
            "expected_key_points": ["b"],
            "is_active": True,
        },
    )
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["task_number"] == 2
    assert second.json()["task_number"] == 3


def test_admin_create_complaint_task_uses_max_plus_one(test_client, seeded_users, seeded_tasks) -> None:
    first = test_client.post(
        "/admin/complaint-tasks",
        json={
            "source_text": "s1",
            "situation_text": "si1",
            "instruction_text": "i1",
            "expected_key_points": ["a"],
            "is_active": True,
        },
    )
    second = test_client.post(
        "/admin/complaint-tasks",
        json={
            "source_text": "s2",
            "situation_text": "si2",
            "instruction_text": "i2",
            "expected_key_points": ["b"],
            "is_active": True,
        },
    )
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["task_number"] == 2
    assert second.json()["task_number"] == 3


def test_admin_access_errors_when_admin_missing_or_inactive(test_client, seeded_users, db_session) -> None:
    admin = seeded_users["admin"]
    admin.is_active = False
    db_session.commit()
    response = test_client.get("/admin/users")
    assert response.status_code == 403

    db_session.delete(admin)
    db_session.commit()
    response = test_client.get("/admin/users")
    assert response.status_code == 401

    # restore admin to keep fixture teardown simple in this test context
    db_session.add(
        User(
            email="admin@example.com",
            username="admin",
            hashed_password="demo",
            role="admin",
            is_active=True,
        )
    )
    db_session.commit()

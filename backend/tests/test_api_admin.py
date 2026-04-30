from __future__ import annotations

from backend.models import TaskSession, User


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
    assert resp.status_code == 200
    assert resp.json()["status"] == "deactivated"
    db_session.refresh(user)
    assert user.is_active is False


def test_admin_manage_info_tasks(test_client, seeded_users, seeded_tasks) -> None:
    list_resp = test_client.get("/admin/info-tasks")
    assert list_resp.status_code == 200

    create_resp = test_client.post(
        "/admin/info-tasks",
        json={
            "task_number": 22,
            "source_text": "s",
            "situation_text": "si",
            "instruction_text": "i",
            "expected_key_points": ["a", "b"],
            "is_active": True,
        },
    )
    assert create_resp.status_code == 200
    task_id = create_resp.json()["id"]

    patch_resp = test_client.patch(f"/admin/info-tasks/{task_id}", json={"is_active": False})
    delete_resp = test_client.delete(f"/admin/info-tasks/{task_id}")
    assert patch_resp.status_code == 200
    assert delete_resp.status_code == 200
    assert delete_resp.json()["status"] == "deactivated"


def test_admin_manage_complaint_tasks(test_client, seeded_users, seeded_tasks) -> None:
    list_resp = test_client.get("/admin/complaint-tasks")
    assert list_resp.status_code == 200

    create_resp = test_client.post(
        "/admin/complaint-tasks",
        json={
            "task_number": 33,
            "source_text": "s",
            "situation_text": "si",
            "instruction_text": "i",
            "expected_key_points": ["a", "b"],
            "is_active": True,
        },
    )
    assert create_resp.status_code == 200
    task_id = create_resp.json()["id"]

    patch_resp = test_client.patch(f"/admin/complaint-tasks/{task_id}", json={"is_active": False})
    delete_resp = test_client.delete(f"/admin/complaint-tasks/{task_id}")
    assert patch_resp.status_code == 200
    assert delete_resp.status_code == 200
    assert delete_resp.json()["status"] == "deactivated"


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

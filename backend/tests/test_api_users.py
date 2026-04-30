from __future__ import annotations

def test_get_users_me_returns_demo_user(test_client, seeded_users) -> None:
    response = test_client.get("/users/me")
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "user@example.com"
    assert "available_sessions" in data


def test_get_users_me_inactive_user_returns_403(test_client, seeded_users, db_session) -> None:
    user = seeded_users["user"]
    user.is_active = False
    db_session.commit()
    response = test_client.get("/users/me")
    assert response.status_code == 403


def test_register_update_and_delete_self_flow(test_client, seeded_users, db_session) -> None:
    register_resp = test_client.post(
        "/users/register",
        json={"email": "new@example.com", "username": "new", "password": "pwd"},
    )
    assert register_resp.status_code == 201
    assert register_resp.json()["email"] == "new@example.com"

    patch_resp = test_client.patch(
        "/users/me",
        json={"email": "user-updated@example.com", "password": "newpwd"},
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["email"] == "user-updated@example.com"

    delete_resp = test_client.delete("/users/me")
    assert delete_resp.status_code == 200
    assert delete_resp.json()["status"] == "deleted"


def test_users_list_endpoint_not_available_for_regular_user(test_client, seeded_users) -> None:
    response = test_client.get("/users")
    assert response.status_code in (404, 405)

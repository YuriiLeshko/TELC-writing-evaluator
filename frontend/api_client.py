import os
from typing import Any

import requests

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
TIMEOUT_SECONDS = 60


class ApiError(Exception):
    pass


def _request(method: str, path: str, **kwargs: Any) -> Any:
    url = f"{API_BASE_URL.rstrip('/')}/{path.lstrip('/')}"
    timeout = kwargs.pop("timeout", TIMEOUT_SECONDS)
    try:
        response = requests.request(method=method, url=url, timeout=timeout, **kwargs)
    except requests.RequestException as exc:
        raise ApiError(f"Backend unavailable: {exc}") from exc

    if not response.ok:
        detail = ""
        try:
            payload = response.json()
            detail = payload.get("detail") or str(payload)
        except ValueError:
            detail = response.text.strip()
        message = detail or f"HTTP {response.status_code}"
        raise ApiError(message)

    if response.status_code == 204:
        return {}
    try:
        return response.json()
    except ValueError as exc:
        raise ApiError("Invalid JSON response from backend.") from exc


def health_check() -> dict[str, Any]:
    return _request("GET", "/health")


def get_current_user() -> dict[str, Any]:
    return _request("GET", "/users/me")


def start_task_session() -> dict[str, Any]:
    return _request("POST", "/task-sessions/start")


def get_my_sessions() -> list[dict[str, Any]]:
    return _request("GET", "/task-sessions/my")


def get_active_sessions() -> list[dict[str, Any]]:
    return _request("GET", "/task-sessions/active")


def get_task_session(session_id: int) -> dict[str, Any]:
    return _request("GET", f"/task-sessions/{session_id}")


def delete_task_session(session_id: int) -> dict[str, Any]:
    return _request("DELETE", f"/task-sessions/{session_id}")


def submit_evaluation(task_session_id: int, selected_task_type: str, candidate_text: str) -> dict[str, Any]:
    payload = {
        "task_session_id": task_session_id,
        "selected_task_type": selected_task_type,
        "candidate_text": candidate_text,
    }
    return _request("POST", "/submissions/evaluate", json=payload, timeout=180)


def get_my_submissions() -> list[dict[str, Any]]:
    return _request("GET", "/submissions/my")


def get_submission(submission_id: int) -> dict[str, Any]:
    return _request("GET", f"/submissions/{submission_id}")


def delete_submission(submission_id: int) -> dict[str, Any]:
    return _request("DELETE", f"/submissions/{submission_id}")


def admin_get_users() -> list[dict[str, Any]]:
    return _request("GET", "/admin/users")


def admin_update_user_counters(
    user_id: int, available_sessions: int | None, available_submissions: int | None
) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    if available_sessions is not None:
        payload["available_sessions"] = available_sessions
    if available_submissions is not None:
        payload["available_submissions"] = available_submissions
    return _request("PATCH", f"/admin/users/{user_id}/counters", json=payload)


def admin_activate_user(user_id: int) -> dict[str, Any]:
    return _request("PATCH", f"/admin/users/{user_id}/activate")


def admin_deactivate_user(user_id: int) -> dict[str, Any]:
    return _request("PATCH", f"/admin/users/{user_id}/deactivate")


def admin_get_info_tasks() -> list[dict[str, Any]]:
    return _request("GET", "/admin/info-tasks")


def admin_get_info_task(task_id: int) -> dict[str, Any]:
    return _request("GET", f"/admin/info-tasks/{task_id}")


def admin_create_info_task(
    task_number: int,
    source_text: str,
    situation_text: str,
    instruction_text: str,
    expected_key_points: list[str],
    is_active: bool,
) -> dict[str, Any]:
    payload = {
        "task_number": task_number,
        "source_text": source_text,
        "situation_text": situation_text,
        "instruction_text": instruction_text,
        "expected_key_points": expected_key_points,
        "is_active": is_active,
    }
    return _request("POST", "/admin/info-tasks", json=payload)


def admin_update_info_task(task_id: int, **fields: Any) -> dict[str, Any]:
    return _request("PATCH", f"/admin/info-tasks/{task_id}", json=fields)


def admin_delete_info_task(task_id: int) -> dict[str, Any]:
    return _request("DELETE", f"/admin/info-tasks/{task_id}")


def admin_get_complaint_tasks() -> list[dict[str, Any]]:
    return _request("GET", "/admin/complaint-tasks")


def admin_get_complaint_task(task_id: int) -> dict[str, Any]:
    return _request("GET", f"/admin/complaint-tasks/{task_id}")


def admin_create_complaint_task(
    task_number: int,
    source_text: str,
    situation_text: str,
    instruction_text: str,
    expected_key_points: list[str],
    is_active: bool,
) -> dict[str, Any]:
    payload = {
        "task_number": task_number,
        "source_text": source_text,
        "situation_text": situation_text,
        "instruction_text": instruction_text,
        "expected_key_points": expected_key_points,
        "is_active": is_active,
    }
    return _request("POST", "/admin/complaint-tasks", json=payload)


def admin_update_complaint_task(task_id: int, **fields: Any) -> dict[str, Any]:
    return _request("PATCH", f"/admin/complaint-tasks/{task_id}", json=fields)


def admin_delete_complaint_task(task_id: int) -> dict[str, Any]:
    return _request("DELETE", f"/admin/complaint-tasks/{task_id}")

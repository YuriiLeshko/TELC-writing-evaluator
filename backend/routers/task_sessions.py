from __future__ import annotations
"""
Task session router for TELC model-test session creation.

Purpose:
- Start and read task sessions for the demo current user.
- Pick a random active info task and complaint task the user has not yet
  received (not present in any prior TaskSession for that user).

Structure:
- Utility helpers to parse key points and map ORM objects to API schemas.
- `POST /task-sessions/start` to create a new session and decrement session counter.
- `GET /task-sessions/my` and `GET /task-sessions/{session_id}` to read sessions.

Dependencies:
- `fastapi` router/dependency primitives.
- `sqlalchemy` ORM (`Session`, `select`, `joinedload`).
- `backend.models` task/session/user entities and `backend.api_schemas`.
"""

import json
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from backend.api_schemas import (
    ComplaintTaskRead,
    InfoTaskRead,
    StartTaskSessionResponse,
    TaskSessionRead,
)
from backend.database import get_db
from backend.models import ComplaintTask, InfoTask, TaskSession, User
from backend.routers.users import get_demo_current_user
from backend.services.task_selection import (
    pick_random_unseen_complaint_task,
    pick_random_unseen_info_task,
)

router = APIRouter(prefix="/task-sessions", tags=["task-sessions"])


def parse_key_points(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return []
        if isinstance(parsed, list):
            return [str(item) for item in parsed]
    return []


def info_task_to_schema(task: InfoTask) -> InfoTaskRead:
    return InfoTaskRead(
        id=task.id,
        task_number=task.task_number,
        source_text=task.source_text,
        situation_text=task.situation_text,
        instruction_text=task.instruction_text,
        expected_key_points=parse_key_points(task.expected_key_points_json),
    )


def complaint_task_to_schema(task: ComplaintTask) -> ComplaintTaskRead:
    return ComplaintTaskRead(
        id=task.id,
        task_number=task.task_number,
        source_text=task.source_text,
        situation_text=task.situation_text,
        instruction_text=task.instruction_text,
        expected_key_points=parse_key_points(task.expected_key_points_json),
    )


def task_session_to_schema(session: TaskSession) -> TaskSessionRead:
    return TaskSessionRead(
        id=session.id,
        started_at=session.started_at,
        submitted_at=session.submitted_at,
        duration_seconds=session.duration_seconds,
        selected_task_type=session.selected_task_type,
        status=session.status,
        info_task=info_task_to_schema(session.info_task),
        complaint_task=complaint_task_to_schema(session.complaint_task),
    )


@router.post("/start", response_model=StartTaskSessionResponse)
def start_task_session(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_demo_current_user),
) -> StartTaskSessionResponse:
    if not current_user.is_active:
        raise HTTPException(status_code=403, detail="User is inactive.")
    if current_user.available_sessions <= 0:
        raise HTTPException(status_code=403, detail="No available task sessions left.")

    info_task = pick_random_unseen_info_task(db, current_user.id)
    complaint_task = pick_random_unseen_complaint_task(db, current_user.id)
    if info_task is None or complaint_task is None:
        raise HTTPException(
            status_code=404,
            detail="No unused tasks available for this user (all active tasks were already used).",
        )

    session = TaskSession(
        user_id=current_user.id,
        info_task_id=info_task.id,
        complaint_task_id=complaint_task.id,
        started_at=datetime.now(timezone.utc),
        status="started",
    )
    db.add(session)
    current_user.available_sessions -= 1
    db.commit()

    reloaded_session = db.scalar(
        select(TaskSession)
        .options(joinedload(TaskSession.info_task), joinedload(TaskSession.complaint_task))
        .where(TaskSession.id == session.id)
    )
    if reloaded_session is None:
        raise HTTPException(status_code=500, detail="Failed to create session.")

    return StartTaskSessionResponse(
        session=task_session_to_schema(reloaded_session),
        display_title=f"Modelltest {reloaded_session.id}",
    )


@router.get("/my", response_model=list[TaskSessionRead])
def list_my_task_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_demo_current_user),
) -> list[TaskSessionRead]:
    sessions = db.scalars(
        select(TaskSession)
        .options(joinedload(TaskSession.info_task), joinedload(TaskSession.complaint_task))
        .where(TaskSession.user_id == current_user.id)
        .order_by(TaskSession.id.desc())
    ).all()
    return [task_session_to_schema(session) for session in sessions]


@router.get("/active", response_model=list[TaskSessionRead])
def list_active_task_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_demo_current_user),
) -> list[TaskSessionRead]:
    sessions = db.scalars(
        select(TaskSession)
        .options(joinedload(TaskSession.info_task), joinedload(TaskSession.complaint_task))
        .where(
            TaskSession.user_id == current_user.id,
            TaskSession.status == "started",
        )
        .order_by(TaskSession.id.desc())
    ).all()
    return [task_session_to_schema(session) for session in sessions]


@router.get("/{session_id}", response_model=TaskSessionRead)
def get_task_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_demo_current_user),
) -> TaskSessionRead:
    session = db.scalar(
        select(TaskSession)
        .options(joinedload(TaskSession.info_task), joinedload(TaskSession.complaint_task))
        .where(
            TaskSession.id == session_id,
            TaskSession.user_id == current_user.id,
        )
    )
    if session is None:
        raise HTTPException(status_code=404, detail="Task session not found.")
    return task_session_to_schema(session)


@router.delete("/{session_id}")
def delete_task_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_demo_current_user),
) -> dict[str, int | str]:
    session = db.scalar(
        select(TaskSession).where(
            TaskSession.id == session_id,
            TaskSession.user_id == current_user.id,
        )
    )
    if session is None:
        raise HTTPException(status_code=404, detail="Task session not found.")
    if session.status == "submitted":
        raise HTTPException(status_code=400, detail="Submitted sessions cannot be deleted.")

    db.delete(session)
    db.commit()
    return {"status": "deleted", "session_id": session_id}


if __name__ == "__main__":
    parsed_from_list = parse_key_points(["a", "b"])
    parsed_from_json = parse_key_points('["x", "y"]')
    print("task_sessions.py smoke test passed.")
    print(f"parse list -> {parsed_from_list}")
    print(f"parse json -> {parsed_from_json}")

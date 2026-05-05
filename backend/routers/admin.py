from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.api_schemas import (
    ComplaintTaskCreate,
    ComplaintTaskRead,
    ComplaintTaskUpdate,
    CounterUpdate,
    InfoTaskCreate,
    InfoTaskRead,
    InfoTaskUpdate,
    UserCreate,
    UserRead,
    UserUpdate,
)
from backend.database import get_db
from backend.models import ComplaintTask, InfoTask, Submission, TaskSession, User
from backend.routers.task_sessions import complaint_task_to_schema, info_task_to_schema
from backend.routers.users import get_demo_admin_user

router = APIRouter(prefix="/admin", tags=["admin"])


def user_to_schema(user: User) -> UserRead:
    return UserRead.model_validate(user, from_attributes=True)


def _next_task_number(model: type[InfoTask] | type[ComplaintTask], db: Session) -> int:
    max_number = db.scalar(select(func.max(model.task_number)))
    return int(max_number or 0) + 1


@router.get("/users", response_model=list[UserRead])
def admin_list_users(
    _: User = Depends(get_demo_admin_user),
    db: Session = Depends(get_db),
) -> list[UserRead]:
    users = db.scalars(select(User).order_by(User.id.asc())).all()
    return [user_to_schema(user) for user in users]


@router.get("/users/{user_id}", response_model=UserRead)
def admin_get_user(
    user_id: int,
    _: User = Depends(get_demo_admin_user),
    db: Session = Depends(get_db),
) -> UserRead:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")
    return user_to_schema(user)


@router.post("/users", response_model=UserRead)
def admin_create_user(
    payload: UserCreate,
    _: User = Depends(get_demo_admin_user),
    db: Session = Depends(get_db),
) -> UserRead:
    existing = db.scalar(select(User).where(User.email == payload.email))
    if existing is not None:
        raise HTTPException(status_code=400, detail="Email already exists.")

    user = User(
        email=payload.email,
        username=payload.username,
        hashed_password=payload.password,
        role=payload.role,
        is_active=payload.is_active,
        available_sessions=payload.available_sessions,
        available_submissions=payload.available_submissions,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user_to_schema(user)


@router.patch("/users/{user_id}", response_model=UserRead)
def admin_update_user(
    user_id: int,
    payload: UserUpdate,
    _: User = Depends(get_demo_admin_user),
    db: Session = Depends(get_db),
) -> UserRead:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")

    data = payload.model_dump(exclude_unset=True)
    if "email" in data and data["email"] != user.email:
        existing = db.scalar(select(User).where(User.email == data["email"]))
        if existing is not None:
            raise HTTPException(status_code=400, detail="Email already exists.")
    for field, value in data.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)
    return user_to_schema(user)


@router.delete("/users/{user_id}")
def admin_delete_user(
    user_id: int,
    current_admin: User = Depends(get_demo_admin_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")
    if user.id == current_admin.id:
        raise HTTPException(status_code=400, detail="Admin cannot delete themselves.")
    if user.role == "admin":
        raise HTTPException(status_code=403, detail="Admin users cannot be deleted.")

    has_related = db.scalar(select(TaskSession.id).where(TaskSession.user_id == user.id).limit(1)) or db.scalar(
        select(Submission.id).where(Submission.user_id == user.id).limit(1)
    )
    if has_related:
        raise HTTPException(
            status_code=409,
            detail="User cannot be deleted because related sessions or submissions exist. Deactivate the user instead.",
        )

    db.delete(user)
    db.commit()
    return {"status": "deleted"}


@router.patch("/users/{user_id}/counters", response_model=UserRead)
def admin_update_counters(
    user_id: int,
    payload: CounterUpdate,
    _: User = Depends(get_demo_admin_user),
    db: Session = Depends(get_db),
) -> UserRead:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")

    data = payload.model_dump(exclude_unset=True)
    if "available_sessions" in data:
        user.available_sessions = data["available_sessions"]
    if "available_submissions" in data:
        user.available_submissions = data["available_submissions"]
    db.commit()
    db.refresh(user)
    return user_to_schema(user)


@router.patch("/users/{user_id}/activate", response_model=UserRead)
def admin_activate_user(
    user_id: int,
    _: User = Depends(get_demo_admin_user),
    db: Session = Depends(get_db),
) -> UserRead:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")
    user.is_active = True
    db.commit()
    db.refresh(user)
    return user_to_schema(user)


@router.patch("/users/{user_id}/deactivate", response_model=UserRead)
def admin_deactivate_user(
    user_id: int,
    _: User = Depends(get_demo_admin_user),
    db: Session = Depends(get_db),
) -> UserRead:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")
    user.is_active = False
    db.commit()
    db.refresh(user)
    return user_to_schema(user)


@router.get("/info-tasks", response_model=list[InfoTaskRead])
def admin_list_info_tasks(
    _: User = Depends(get_demo_admin_user),
    db: Session = Depends(get_db),
) -> list[InfoTaskRead]:
    tasks = db.scalars(select(InfoTask).order_by(InfoTask.task_number.asc())).all()
    return [info_task_to_schema(task) for task in tasks]


@router.post("/info-tasks", response_model=InfoTaskRead)
def admin_create_info_task(
    payload: InfoTaskCreate,
    _: User = Depends(get_demo_admin_user),
    db: Session = Depends(get_db),
) -> InfoTaskRead:
    task_number = payload.task_number if payload.task_number is not None else _next_task_number(InfoTask, db)
    existing = db.scalar(select(InfoTask).where(InfoTask.task_number == task_number))
    if existing is not None:
        raise HTTPException(status_code=400, detail="Info task number already exists.")
    task = InfoTask(
        task_number=task_number,
        source_text=payload.source_text,
        situation_text=payload.situation_text,
        instruction_text=payload.instruction_text,
        expected_key_points_json=payload.expected_key_points,
        is_active=payload.is_active,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return info_task_to_schema(task)


@router.get("/info-tasks/{task_id}", response_model=InfoTaskRead)
def admin_get_info_task(
    task_id: int,
    _: User = Depends(get_demo_admin_user),
    db: Session = Depends(get_db),
) -> InfoTaskRead:
    task = db.get(InfoTask, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Info task not found.")
    return info_task_to_schema(task)


@router.patch("/info-tasks/{task_id}", response_model=InfoTaskRead)
def admin_update_info_task(
    task_id: int,
    payload: InfoTaskUpdate,
    _: User = Depends(get_demo_admin_user),
    db: Session = Depends(get_db),
) -> InfoTaskRead:
    task = db.get(InfoTask, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Info task not found.")

    data = payload.model_dump(exclude_unset=True)
    if "task_number" in data and data["task_number"] != task.task_number:
        existing = db.scalar(select(InfoTask).where(InfoTask.task_number == data["task_number"]))
        if existing is not None:
            raise HTTPException(status_code=400, detail="Info task number already exists.")
    if "expected_key_points" in data:
        task.expected_key_points_json = data.pop("expected_key_points")
    for field, value in data.items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)
    return info_task_to_schema(task)


@router.delete("/info-tasks/{task_id}")
def admin_delete_info_task(
    task_id: int,
    _: User = Depends(get_demo_admin_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    task = db.get(InfoTask, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Info task not found.")
    has_related = db.scalar(select(TaskSession.id).where(TaskSession.info_task_id == task.id).limit(1)) or db.scalar(
        select(Submission.id).where((Submission.selected_task_type == "info") & (Submission.selected_task_id == task.id)).limit(1)
    )
    if has_related:
        raise HTTPException(status_code=409, detail="Task cannot be deleted because it is already used. Deactivate it instead.")
    db.delete(task)
    db.commit()
    return {"status": "deleted", "task_id": task_id}


@router.patch("/info-tasks/{task_id}/deactivate", response_model=InfoTaskRead)
def admin_deactivate_info_task(
    task_id: int,
    _: User = Depends(get_demo_admin_user),
    db: Session = Depends(get_db),
) -> InfoTaskRead:
    task = db.get(InfoTask, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Info task not found.")
    task.is_active = False
    db.commit()
    db.refresh(task)
    return info_task_to_schema(task)


@router.patch("/info-tasks/{task_id}/activate", response_model=InfoTaskRead)
def admin_activate_info_task(
    task_id: int,
    _: User = Depends(get_demo_admin_user),
    db: Session = Depends(get_db),
) -> InfoTaskRead:
    task = db.get(InfoTask, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Info task not found.")
    task.is_active = True
    db.commit()
    db.refresh(task)
    return info_task_to_schema(task)


@router.get("/complaint-tasks", response_model=list[ComplaintTaskRead])
def admin_list_complaint_tasks(
    _: User = Depends(get_demo_admin_user),
    db: Session = Depends(get_db),
) -> list[ComplaintTaskRead]:
    tasks = db.scalars(select(ComplaintTask).order_by(ComplaintTask.task_number.asc())).all()
    return [complaint_task_to_schema(task) for task in tasks]


@router.post("/complaint-tasks", response_model=ComplaintTaskRead)
def admin_create_complaint_task(
    payload: ComplaintTaskCreate,
    _: User = Depends(get_demo_admin_user),
    db: Session = Depends(get_db),
) -> ComplaintTaskRead:
    task_number = payload.task_number if payload.task_number is not None else _next_task_number(ComplaintTask, db)
    existing = db.scalar(select(ComplaintTask).where(ComplaintTask.task_number == task_number))
    if existing is not None:
        raise HTTPException(status_code=400, detail="Complaint task number already exists.")
    task = ComplaintTask(
        task_number=task_number,
        source_text=payload.source_text,
        situation_text=payload.situation_text,
        instruction_text=payload.instruction_text,
        expected_key_points_json=payload.expected_key_points,
        is_active=payload.is_active,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return complaint_task_to_schema(task)


@router.get("/complaint-tasks/{task_id}", response_model=ComplaintTaskRead)
def admin_get_complaint_task(
    task_id: int,
    _: User = Depends(get_demo_admin_user),
    db: Session = Depends(get_db),
) -> ComplaintTaskRead:
    task = db.get(ComplaintTask, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Complaint task not found.")
    return complaint_task_to_schema(task)


@router.patch("/complaint-tasks/{task_id}", response_model=ComplaintTaskRead)
def admin_update_complaint_task(
    task_id: int,
    payload: ComplaintTaskUpdate,
    _: User = Depends(get_demo_admin_user),
    db: Session = Depends(get_db),
) -> ComplaintTaskRead:
    task = db.get(ComplaintTask, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Complaint task not found.")

    data = payload.model_dump(exclude_unset=True)
    if "task_number" in data and data["task_number"] != task.task_number:
        existing = db.scalar(select(ComplaintTask).where(ComplaintTask.task_number == data["task_number"]))
        if existing is not None:
            raise HTTPException(status_code=400, detail="Complaint task number already exists.")
    if "expected_key_points" in data:
        task.expected_key_points_json = data.pop("expected_key_points")
    for field, value in data.items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)
    return complaint_task_to_schema(task)


@router.delete("/complaint-tasks/{task_id}")
def admin_delete_complaint_task(
    task_id: int,
    _: User = Depends(get_demo_admin_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    task = db.get(ComplaintTask, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Complaint task not found.")
    has_related = db.scalar(select(TaskSession.id).where(TaskSession.complaint_task_id == task.id).limit(1)) or db.scalar(
        select(Submission.id)
        .where((Submission.selected_task_type == "complaint") & (Submission.selected_task_id == task.id))
        .limit(1)
    )
    if has_related:
        raise HTTPException(status_code=409, detail="Task cannot be deleted because it is already used. Deactivate it instead.")
    db.delete(task)
    db.commit()
    return {"status": "deleted", "task_id": task_id}


@router.patch("/complaint-tasks/{task_id}/deactivate", response_model=ComplaintTaskRead)
def admin_deactivate_complaint_task(
    task_id: int,
    _: User = Depends(get_demo_admin_user),
    db: Session = Depends(get_db),
) -> ComplaintTaskRead:
    task = db.get(ComplaintTask, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Complaint task not found.")
    task.is_active = False
    db.commit()
    db.refresh(task)
    return complaint_task_to_schema(task)


@router.patch("/complaint-tasks/{task_id}/activate", response_model=ComplaintTaskRead)
def admin_activate_complaint_task(
    task_id: int,
    _: User = Depends(get_demo_admin_user),
    db: Session = Depends(get_db),
) -> ComplaintTaskRead:
    task = db.get(ComplaintTask, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Complaint task not found.")
    task.is_active = True
    db.commit()
    db.refresh(task)
    return complaint_task_to_schema(task)

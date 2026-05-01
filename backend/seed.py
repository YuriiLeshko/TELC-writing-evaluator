from __future__ import annotations
"""
Seed and smoke-test utilities for TELC evaluator SQLite database.

Purpose:
- Initialize schema and insert demo users.
- Load info/complaint tasks from external JSON files.
- Keep seeding idempotent for repeated local runs.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
import json

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.database import SessionLocal, init_db
from backend.models import ComplaintTask, InfoTask, User


@dataclass(frozen=True)
class UserSeed:
    email: str
    role: str
    hashed_password: str = "demo"
    username: str | None = None
    is_active: bool = True
    available_sessions: int = 5
    available_submissions: int = 5


@dataclass(frozen=True)
class TaskSeed:
    task_number: int
    source_text: str
    situation_text: str
    instruction_text: str
    expected_key_points_json: list[str]
    is_active: bool = True


USER_SEEDS: Sequence[UserSeed] = (
    UserSeed(
        email="admin@example.com",
        role="admin",
        username="admin",
        is_active=True,
        available_sessions=999,
        available_submissions=999,
    ),
    UserSeed(
        email="user@example.com",
        role="user",
        username="user",
        is_active=True,
        available_sessions=20,
        available_submissions=20,
    ),
)

TASKS_BASE_DIR = Path(__file__).resolve().parent / "seed_tasks"
INFO_TASKS_DIR = TASKS_BASE_DIR / "info"
COMPLAINT_TASKS_DIR = TASKS_BASE_DIR / "complaint"


def _read_task_file(path: Path) -> TaskSeed:
    data = json.loads(path.read_text())
    for key in (
        "task_number",
        "source_text",
        "situation_text",
        "instruction_text",
        "expected_key_points",
    ):
        if key not in data:
            raise ValueError(f"Missing key '{key}' in {path}")

    key_points = data["expected_key_points"]
    if not isinstance(key_points, list) or any(not isinstance(item, str) for item in key_points):
        raise ValueError(f"'expected_key_points' must be list[str] in {path}")

    return TaskSeed(
        task_number=int(data["task_number"]),
        source_text=str(data["source_text"]),
        situation_text=str(data["situation_text"]),
        instruction_text=str(data["instruction_text"]),
        expected_key_points_json=[item.strip() for item in key_points if item.strip()],
        is_active=bool(data.get("is_active", True)),
    )


def load_info_task_seeds() -> Sequence[TaskSeed]:
    files = sorted(INFO_TASKS_DIR.glob("*.json"))
    if not files:
        raise FileNotFoundError(f"No info task files found in {INFO_TASKS_DIR}")
    return tuple(_read_task_file(path) for path in files)


def load_complaint_task_seeds() -> Sequence[TaskSeed]:
    files = sorted(COMPLAINT_TASKS_DIR.glob("*.json"))
    if not files:
        raise FileNotFoundError(f"No complaint task files found in {COMPLAINT_TASKS_DIR}")
    return tuple(_read_task_file(path) for path in files)


def get_next_task_pair_for_user(db: Session, user: User) -> tuple[InfoTask, ComplaintTask] | None:
    info_task = db.scalar(
        select(InfoTask).where(
            InfoTask.task_number == user.next_info_task_index,
            InfoTask.is_active.is_(True),
        )
    )
    complaint_task = db.scalar(
        select(ComplaintTask).where(
            ComplaintTask.task_number == user.next_complaint_task_index,
            ComplaintTask.is_active.is_(True),
        )
    )
    if info_task is None or complaint_task is None:
        return None
    return info_task, complaint_task


def advance_user_task_indices(user: User) -> None:
    user.next_info_task_index += 1
    user.next_complaint_task_index += 1


def seed_users(db: Session) -> None:
    for seed in USER_SEEDS:
        existing = db.scalar(select(User).where(User.email == seed.email))
        if existing is None:
            db.add(
                User(
                    email=seed.email,
                    username=seed.username,
                    hashed_password=seed.hashed_password,
                    role=seed.role,
                    is_active=seed.is_active,
                    available_sessions=seed.available_sessions,
                    available_submissions=seed.available_submissions,
                )
            )


def seed_info_tasks(db: Session) -> None:
    for seed in load_info_task_seeds():
        existing = db.scalar(select(InfoTask).where(InfoTask.task_number == seed.task_number))
        if existing is None:
            db.add(
                InfoTask(
                    task_number=seed.task_number,
                    source_text=seed.source_text,
                    situation_text=seed.situation_text,
                    instruction_text=seed.instruction_text,
                    expected_key_points_json=seed.expected_key_points_json,
                    is_active=seed.is_active,
                )
            )


def seed_complaint_tasks(db: Session) -> None:
    for seed in load_complaint_task_seeds():
        existing = db.scalar(select(ComplaintTask).where(ComplaintTask.task_number == seed.task_number))
        if existing is None:
            db.add(
                ComplaintTask(
                    task_number=seed.task_number,
                    source_text=seed.source_text,
                    situation_text=seed.situation_text,
                    instruction_text=seed.instruction_text,
                    expected_key_points_json=seed.expected_key_points_json,
                    is_active=seed.is_active,
                )
            )


def print_summary(db: Session) -> None:
    users_count = db.scalar(select(func.count()).select_from(User)) or 0
    info_tasks_count = db.scalar(select(func.count()).select_from(InfoTask)) or 0
    complaint_tasks_count = db.scalar(select(func.count()).select_from(ComplaintTask)) or 0

    print("Seed completed.")
    print(f"users count: {users_count}")
    print(f"info tasks count: {info_tasks_count}")
    print(f"complaint tasks count: {complaint_tasks_count}")
    print(f"info source dir: {INFO_TASKS_DIR}")
    print(f"complaint source dir: {COMPLAINT_TASKS_DIR}")


def seed() -> None:
    init_db()
    with SessionLocal() as db:
        seed_users(db)
        seed_info_tasks(db)
        seed_complaint_tasks(db)
        db.commit()
        print_summary(db)


if __name__ == "__main__":
    print("Running seed.py smoke test...")
    seed()

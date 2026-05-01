from __future__ import annotations
"""
Seed and smoke-test utilities for TELC evaluator SQLite database.

Purpose:
- Initialize schema and insert minimal MVP demo data (users + tasks).
- Load task definitions from JSON under backend/seed_data/tasks/.
- Keep seeding idempotent for repeated local runs.
- Provide task-pair helper using random unseen tasks (`get_next_task_pair_for_user`).

Structure:
- Seed dataclass (`UserSeed`) for static user payloads.
- Task loading helpers and upsert by task_number.
- Task selection helper (`get_next_task_pair_for_user`) delegating to `backend.services.task_selection`.
- `seed()` entrypoint used by IDE terminal run: `PYTHONPATH=. python backend/seed.py`.

Dependencies:
pip install sqlalchemy
"""

import json
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.database import SessionLocal, init_db
from backend.models import ComplaintTask, InfoTask, User
from backend.services.task_selection import (
    pick_random_unseen_complaint_task,
    pick_random_unseen_info_task,
)

# During development, if database schema changed, reset DB manually:
# rm -f telc_evaluator.db
# PYTHONPATH=. python backend/seed.py

BASE_DIR = Path(__file__).resolve().parent
INFO_TASKS_DIR = BASE_DIR / "seed_data" / "tasks" / "info"
COMPLAINT_TASKS_DIR = BASE_DIR / "seed_data" / "tasks" / "complaint"


@dataclass(frozen=True)
class UserSeed:
    email: str
    role: str
    hashed_password: str = "demo"
    username: str | None = None
    is_active: bool = True
    available_sessions: int = 5
    available_submissions: int = 5


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
        available_sessions=5,
        available_submissions=5,
    ),
)


def load_task_file(path: Path) -> dict:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as e:
        raise ValueError(f"Cannot read task file {path}: {e}") from e
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in task file {path}: {e}") from e
    if not isinstance(data, dict):
        raise ValueError(f"Task file {path} must contain a JSON object, got {type(data).__name__}")
    return data


def load_task_files(directory: Path) -> list[dict]:
    if not directory.is_dir():
        return []
    paths = sorted(directory.glob("*.json"))
    result: list[dict] = []
    seen_numbers: dict[int, Path] = {}
    for path in paths:
        data = load_task_file(path)
        validate_task_data(data, path)
        task_number = data["task_number"]
        if task_number in seen_numbers:
            raise ValueError(
                f"Duplicate task_number {task_number} in {seen_numbers[task_number]} and {path}"
            )
        seen_numbers[task_number] = path
        result.append(data)
    return result


def validate_task_data(data: dict, path: Path) -> None:
    def err(msg: str) -> ValueError:
        return ValueError(f"{path}: {msg}")

    if "task_number" not in data:
        raise err("missing required field 'task_number'")
    tn = data["task_number"]
    if not isinstance(tn, int) or isinstance(tn, bool):
        raise err(f"'task_number' must be an int, got {type(tn).__name__}")

    for key in ("source_text", "situation_text", "instruction_text"):
        if key not in data:
            raise err(f"missing required field '{key}'")
        val = data[key]
        if not isinstance(val, str) or not val.strip():
            raise err(f"'{key}' must be a non-empty string")

    if "expected_key_points" not in data:
        raise err("missing required field 'expected_key_points'")
    points = data["expected_key_points"]
    if not isinstance(points, list) or len(points) == 0:
        raise err("'expected_key_points' must be a non-empty list")
    for i, p in enumerate(points):
        if not isinstance(p, str) or not p.strip():
            raise err(f"'expected_key_points'[{i}] must be a non-empty string")

    if "is_active" in data and not isinstance(data["is_active"], bool):
        raise err("'is_active' must be a boolean when present")


def serialize_key_points(points: list[str]) -> Any:
    """Return value for JSON column `expected_key_points_json` (list of strings)."""
    return list(points)


def upsert_info_task(db: Session, data: dict) -> InfoTask:
    is_active = bool(data["is_active"]) if "is_active" in data else True
    key_payload = serialize_key_points(list(data["expected_key_points"]))
    existing = db.scalar(select(InfoTask).where(InfoTask.task_number == data["task_number"]))
    if existing is None:
        row = InfoTask(
            task_number=data["task_number"],
            source_text=data["source_text"],
            situation_text=data["situation_text"],
            instruction_text=data["instruction_text"],
            expected_key_points_json=key_payload,
            is_active=is_active,
        )
        db.add(row)
        return row
    existing.source_text = data["source_text"]
    existing.situation_text = data["situation_text"]
    existing.instruction_text = data["instruction_text"]
    existing.expected_key_points_json = key_payload
    existing.is_active = is_active
    return existing


def upsert_complaint_task(db: Session, data: dict) -> ComplaintTask:
    is_active = bool(data["is_active"]) if "is_active" in data else True
    key_payload = serialize_key_points(list(data["expected_key_points"]))
    existing = db.scalar(select(ComplaintTask).where(ComplaintTask.task_number == data["task_number"]))
    if existing is None:
        row = ComplaintTask(
            task_number=data["task_number"],
            source_text=data["source_text"],
            situation_text=data["situation_text"],
            instruction_text=data["instruction_text"],
            expected_key_points_json=key_payload,
            is_active=is_active,
        )
        db.add(row)
        return row
    existing.source_text = data["source_text"]
    existing.situation_text = data["situation_text"]
    existing.instruction_text = data["instruction_text"]
    existing.expected_key_points_json = key_payload
    existing.is_active = is_active
    return existing


def get_next_task_pair_for_user(db: Session, user: User) -> tuple[InfoTask, ComplaintTask] | None:
    """
    Returns a random pair of active tasks the user has not yet received
    (no matching TaskSession rows). Mirrors `/task-sessions/start` selection.
    """
    info_task = pick_random_unseen_info_task(db, user.id)
    complaint_task = pick_random_unseen_complaint_task(db, user.id)
    if info_task is None or complaint_task is None:
        return None
    return info_task, complaint_task


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


def seed_info_tasks(db: Session) -> int:
    payloads = load_task_files(INFO_TASKS_DIR)
    for data in payloads:
        upsert_info_task(db, data)
    return len(payloads)


def seed_complaint_tasks(db: Session) -> int:
    payloads = load_task_files(COMPLAINT_TASKS_DIR)
    for data in payloads:
        upsert_complaint_task(db, data)
    return len(payloads)


def print_summary(db: Session, info_files_loaded: int, complaint_files_loaded: int) -> None:
    users_count = db.scalar(select(func.count()).select_from(User)) or 0
    info_tasks_count = db.scalar(select(func.count()).select_from(InfoTask)) or 0
    complaint_tasks_count = db.scalar(select(func.count()).select_from(ComplaintTask)) or 0

    demo_user = db.scalar(select(User).where(User.email == "user@example.com"))

    print("Seed completed.")
    print(f"users count: {users_count}")
    print(f"info tasks count: {info_tasks_count}")
    print(f"complaint tasks count: {complaint_tasks_count}")
    print(f"loaded info task files: {info_files_loaded}")
    print(f"loaded complaint task files: {complaint_files_loaded}")
    if demo_user is not None:
        print(f"demo user available_sessions: {demo_user.available_sessions}")
        print(f"demo user available_submissions: {demo_user.available_submissions}")


def seed() -> None:
    init_db()
    with SessionLocal() as db:
        seed_users(db)
        info_loaded = seed_info_tasks(db)
        complaint_loaded = seed_complaint_tasks(db)
        db.commit()
        print_summary(db, info_loaded, complaint_loaded)


if __name__ == "__main__":
    print("Running seed.py smoke test...")
    seed()

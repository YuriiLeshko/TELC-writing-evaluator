from __future__ import annotations
"""
Seed and smoke-test utilities for TELC evaluator SQLite database.

Purpose:
- Initialize schema and insert minimal MVP demo data (users + tasks).
- Keep seeding idempotent for repeated local runs.
- Provide task-pair helper logic for deterministic next-task selection.

Structure:
- Seed dataclasses (`UserSeed`, `TaskSeed`) and static seed payloads.
- Task selection helpers (`get_next_task_pair_for_user`, `advance_user_task_indices`).
- Insert functions for users/info tasks/complaint tasks.
- `seed()` entrypoint used by IDE terminal run: `PYTHONPATH=. python backend/seed.py`.

Dependencies:
pip install sqlalchemy
"""

from collections.abc import Sequence
from dataclasses import dataclass

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


@dataclass(frozen=True)
class TaskSeed:
    task_number: int
    source_text: str
    situation_text: str
    instruction_text: str
    expected_key_points_json: list[str]


USER_SEEDS: Sequence[UserSeed] = (
    UserSeed(email="admin@example.com", role="admin", username="admin"),
    UserSeed(email="user@example.com", role="user", username="user"),
)

INFO_TASK_SEEDS: Sequence[TaskSeed] = (
    TaskSeed(
        task_number=1,
        source_text=(
            "Ihre Wandergruppe plant einen Tagesausflug in die Berge. "
            "Im letzten Rundschreiben wurden Treffpunkt, Ausruestung und Kosten genannt."
        ),
        situation_text=(
            "Ein neues Mitglied konnte am Vorbereitungstreffen nicht teilnehmen und bittet um alle wichtigen Infos."
        ),
        instruction_text=(
            "Schreiben Sie einen Informationsbrief. Gehen Sie auf Treffpunkt und Uhrzeit, noetige Ausruestung, "
            "Kostenbeitrag und Kontaktmoeglichkeit fuer Rueckfragen ein."
        ),
        expected_key_points_json=[
            "Treffpunkt und genaue Uhrzeit nennen",
            "Noetige Ausruestung beschreiben",
            "Kosten oder Beitrag erklaeren",
            "Kontakt fuer Rueckfragen angeben",
        ],
    ),
)

COMPLAINT_TASK_SEEDS: Sequence[TaskSeed] = (
    TaskSeed(
        task_number=1,
        source_text=(
            "Sie haben bei Gartenservice Flora einen Fruehjahrsservice bestellt. "
            "Der Einsatz war verspaetet, einige Beete wurden nicht bearbeitet, und es gab trotzdem die volle Rechnung."
        ),
        situation_text=(
            "Sie moechten sich schriftlich beschweren und eine faire Loesung verlangen."
        ),
        instruction_text=(
            "Schreiben Sie einen Beschwerdebrief an Gartenservice Flora. "
            "Beschreiben Sie die Probleme konkret, erlaeutern Sie Ihre Erwartung und fordern Sie eine angemessene Reaktion."
        ),
        expected_key_points_json=[
            "Verspaetung oder Terminproblem erwaehnen",
            "Unvollstaendige Leistung konkret nennen",
            "Unzufriedenheit mit der Rechnung darstellen",
            "Konkrete Loesung oder Ausgleich fordern",
        ],
    ),
)


def get_next_task_pair_for_user(db: Session, user: User) -> tuple[InfoTask, ComplaintTask] | None:
    """
    Returns the active task pair based on user's next indices.
    Later session creation should increment both indices after showing tasks.
    """
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
                    is_active=True,
                )
            )


def seed_info_tasks(db: Session) -> None:
    for seed in INFO_TASK_SEEDS:
        existing = db.scalar(select(InfoTask).where(InfoTask.task_number == seed.task_number))
        if existing is None:
            db.add(
                InfoTask(
                    task_number=seed.task_number,
                    source_text=seed.source_text,
                    situation_text=seed.situation_text,
                    instruction_text=seed.instruction_text,
                    expected_key_points_json=seed.expected_key_points_json,
                    is_active=True,
                )
            )


def seed_complaint_tasks(db: Session) -> None:
    for seed in COMPLAINT_TASK_SEEDS:
        existing = db.scalar(select(ComplaintTask).where(ComplaintTask.task_number == seed.task_number))
        if existing is None:
            db.add(
                ComplaintTask(
                    task_number=seed.task_number,
                    source_text=seed.source_text,
                    situation_text=seed.situation_text,
                    instruction_text=seed.instruction_text,
                    expected_key_points_json=seed.expected_key_points_json,
                    is_active=True,
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

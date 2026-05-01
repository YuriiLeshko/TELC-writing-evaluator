from __future__ import annotations
"""
Random task selection based on prior sessions for a user.

A task is considered already received if it appears in any TaskSession
for that user (including sessions still in status started). Deleting a
session frees those task ids for future draws.
"""

import random

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models import ComplaintTask, InfoTask, TaskSession


def _used_info_task_ids(db: Session, user_id: int) -> set[int]:
    ids = db.scalars(select(TaskSession.info_task_id).where(TaskSession.user_id == user_id)).all()
    return set(ids)


def _used_complaint_task_ids(db: Session, user_id: int) -> set[int]:
    ids = db.scalars(select(TaskSession.complaint_task_id).where(TaskSession.user_id == user_id)).all()
    return set(ids)


def pick_random_unseen_info_task(db: Session, user_id: int) -> InfoTask | None:
    used = _used_info_task_ids(db, user_id)
    stmt = select(InfoTask).where(InfoTask.is_active.is_(True))
    if used:
        stmt = stmt.where(InfoTask.id.not_in(used))
    candidates = list(db.scalars(stmt).all())
    if not candidates:
        return None
    return random.choice(candidates)


def pick_random_unseen_complaint_task(db: Session, user_id: int) -> ComplaintTask | None:
    used = _used_complaint_task_ids(db, user_id)
    stmt = select(ComplaintTask).where(ComplaintTask.is_active.is_(True))
    if used:
        stmt = stmt.where(ComplaintTask.id.not_in(used))
    candidates = list(db.scalars(stmt).all())
    if not candidates:
        return None
    return random.choice(candidates)

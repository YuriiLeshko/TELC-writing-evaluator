from __future__ import annotations

from sqlalchemy import select

from backend.models import ComplaintTask, InfoTask, User
from backend.seed import seed_complaint_tasks, seed_info_tasks, seed_users


def test_seed_users_and_tasks_idempotent(db_session) -> None:
    seed_users(db_session)
    seed_info_tasks(db_session)
    seed_complaint_tasks(db_session)
    db_session.commit()

    seed_users(db_session)
    seed_info_tasks(db_session)
    seed_complaint_tasks(db_session)
    db_session.commit()

    users = db_session.scalars(select(User)).all()
    info_tasks = db_session.scalars(select(InfoTask)).all()
    complaint_tasks = db_session.scalars(select(ComplaintTask)).all()

    assert len(users) == 2
    assert len(info_tasks) == 1
    assert len(complaint_tasks) == 1

    admin = db_session.scalar(select(User).where(User.email == "admin@example.com"))
    demo_user = db_session.scalar(select(User).where(User.email == "user@example.com"))
    assert admin is not None and admin.role == "admin"
    assert demo_user is not None and demo_user.role == "user"

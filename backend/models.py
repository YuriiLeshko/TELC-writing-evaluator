from __future__ import annotations
"""
SQLAlchemy ORM models for TELC writing evaluator backend.

Purpose:
- Define persistent entities for users, tasks, sessions, and submissions.
- Keep data structure ready for FastAPI service layer without routes in this module.

Structure:
- `User`: account and usage counters (sessions / submissions).
- `InfoTask` / `ComplaintTask`: task banks for both TELC task types.
- `TaskSession`: per-attempt pairing and timing metadata.
- `Submission`: saved candidate text and evaluation result payload.
- `utc_now()`: shared UTC timestamp helper.

Dependencies:
pip install sqlalchemy
"""

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from backend.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    username: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="user", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    available_sessions: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    available_submissions: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    task_sessions: Mapped[list[TaskSession]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    submissions: Mapped[list[Submission]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


class InfoTask(Base):
    __tablename__ = "info_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=False)
    task_number: Mapped[int] = mapped_column(Integer, unique=True, index=True, nullable=False)
    source_text: Mapped[str] = mapped_column(Text, nullable=False)
    situation_text: Mapped[str] = mapped_column(Text, nullable=False)
    instruction_text: Mapped[str] = mapped_column(Text, nullable=False)
    expected_key_points_json: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    task_sessions: Mapped[list[TaskSession]] = relationship(back_populates="info_task")


class ComplaintTask(Base):
    __tablename__ = "complaint_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=False)
    task_number: Mapped[int] = mapped_column(Integer, unique=True, index=True, nullable=False)
    source_text: Mapped[str] = mapped_column(Text, nullable=False)
    situation_text: Mapped[str] = mapped_column(Text, nullable=False)
    instruction_text: Mapped[str] = mapped_column(Text, nullable=False)
    expected_key_points_json: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    task_sessions: Mapped[list[TaskSession]] = relationship(back_populates="complaint_task")


class TaskSession(Base):
    __tablename__ = "task_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    info_task_id: Mapped[int] = mapped_column(ForeignKey("info_tasks.id"), nullable=False)
    complaint_task_id: Mapped[int] = mapped_column(ForeignKey("complaint_tasks.id"), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    selected_task_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    selected_task_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="started", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user: Mapped[User] = relationship(back_populates="task_sessions")
    info_task: Mapped[InfoTask] = relationship(back_populates="task_sessions")
    complaint_task: Mapped[ComplaintTask] = relationship(back_populates="task_sessions")
    submission: Mapped[Submission | None] = relationship(
        back_populates="task_session",
        cascade="all, delete-orphan",
        uselist=False,
    )


class Submission(Base):
    __tablename__ = "submissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    task_session_id: Mapped[int] = mapped_column(
        ForeignKey("task_sessions.id"),
        nullable=False,
        unique=True,
    )
    selected_task_type: Mapped[str] = mapped_column(String(20), nullable=False)
    selected_task_id: Mapped[int] = mapped_column(Integer, nullable=False)
    candidate_text: Mapped[str] = mapped_column(Text, nullable=False)
    result_json: Mapped[dict[str, Any] | list[Any]] = mapped_column(JSON, nullable=False)
    raw_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    final_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    word_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="success", nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user: Mapped[User] = relationship(back_populates="submissions")
    task_session: Mapped[TaskSession] = relationship(back_populates="submission")


if __name__ == "__main__":
    model_names = [User.__name__, InfoTask.__name__, ComplaintTask.__name__, TaskSession.__name__, Submission.__name__]
    table_names = [User.__tablename__, InfoTask.__tablename__, ComplaintTask.__tablename__, TaskSession.__tablename__, Submission.__tablename__]
    print(f"models.py smoke test passed: loaded models={model_names}")
    print(f"mapped tables={table_names}")

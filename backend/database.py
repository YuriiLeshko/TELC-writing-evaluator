"""
Database setup for TELC evaluator backend (SQLite + SQLAlchemy).

Purpose:
- Provide a single SQLAlchemy engine/session configuration for the backend.
- Expose `Base` for declarative models and helper functions for app startup.

Structure:
- `engine`: SQLite engine with `check_same_thread=False`.
- `SessionLocal`: session factory for request-scoped DB work.
- `Base`: declarative base used by ORM models.
- `get_db()`: generator dependency for FastAPI-compatible usage.
- `init_db()`: creates all tables from loaded model metadata.

Dependencies:
pip install sqlalchemy
"""

from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./telc_evaluator.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from backend import models  # noqa: F401

    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_db()
    with SessionLocal() as db:
        db.execute(text("SELECT 1"))
    print("database.py smoke test passed: engine/session/init_db are operational.")

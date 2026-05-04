from __future__ import annotations

import os
from collections.abc import Generator
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

os.environ.setdefault("OPENROUTER_API_KEY", "test-key")
os.environ.setdefault("MODEL_NAME", "test-model")
os.environ.setdefault("FALLBACK_MODEL_NAME", "test-fallback-model")

from backend.database import Base, get_db
from backend.main import app
from backend.models import ComplaintTask, InfoTask, User


class FakeLLMClient:
    def __init__(self, responses: list[dict[str, Any]]) -> None:
        self.responses = list(responses)
        self.calls: list[dict[str, Any]] = []

    async def call_llm_json(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        self.calls.append(
            {
                "system_prompt": system_prompt,
                "user_prompt": user_prompt,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
        )
        if not self.responses:
            raise RuntimeError("No fake LLM responses configured.")
        return self.responses.pop(0)


@pytest.fixture
def db_session(tmp_path: pytest.TempPathFactory) -> Generator[Session, None, None]:
    db_file = tmp_path / "test.db"
    engine = create_engine(
        f"sqlite:///{db_file}",
        connect_args={"check_same_thread": False},
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture
def test_client(db_session: Session, monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        try:
            yield db_session
        finally:
            pass

    monkeypatch.setattr("backend.main.init_db", lambda: None)
    monkeypatch.setattr("backend.main.apply_idempotent_seed", lambda: None)
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
def seeded_users(db_session: Session) -> dict[str, User]:
    admin = User(
        email="admin@example.com",
        username="admin",
        hashed_password="demo",
        role="admin",
        is_active=True,
        available_sessions=5,
        available_submissions=5,
    )
    user = User(
        email="user@example.com",
        username="user",
        hashed_password="demo",
        role="user",
        is_active=True,
        available_sessions=5,
        available_submissions=5,
    )
    db_session.add_all([admin, user])
    db_session.commit()
    db_session.refresh(admin)
    db_session.refresh(user)
    return {"admin": admin, "user": user}


@pytest.fixture
def seeded_tasks(db_session: Session) -> dict[str, Any]:
    info_task = InfoTask(
        task_number=1,
        source_text="Info source",
        situation_text="Info situation",
        instruction_text="Info instruction",
        expected_key_points_json=["Punkt 1", "Punkt 2"],
        is_active=True,
    )
    complaint_task = ComplaintTask(
        task_number=1,
        source_text="Complaint source",
        situation_text="Complaint situation",
        instruction_text="Complaint instruction",
        expected_key_points_json=["Beschwerde 1", "Beschwerde 2"],
        is_active=True,
    )
    db_session.add_all([info_task, complaint_task])
    db_session.commit()
    db_session.refresh(info_task)
    db_session.refresh(complaint_task)
    return {"info_task": info_task, "complaint_task": complaint_task}


@pytest.fixture
def fake_llm_client() -> FakeLLMClient:
    return FakeLLMClient([])

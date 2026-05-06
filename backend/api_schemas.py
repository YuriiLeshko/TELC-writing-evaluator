from __future__ import annotations
"""
Pydantic API schemas for TELC Writing Evaluator HTTP layer.

Purpose:
- Define request/response contracts used by FastAPI routers.
- Keep transport models separated from SQLAlchemy ORM models.

Structure:
- User, task, and session read schemas.
- Submission request/response schemas for evaluation flow.
- MVP-focused models with `from_attributes=True` where ORM mapping is needed.

Dependencies:
- `pydantic` v2 (`BaseModel`, `ConfigDict`).
- Python typing and datetime primitives for API field types.
"""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    username: str | None
    role: str
    is_active: bool
    available_sessions: int
    available_submissions: int
    next_info_task_index: int
    next_complaint_task_index: int


class UserCreate(BaseModel):
    email: str
    username: str | None = None
    password: str
    role: Literal["user", "admin"] = "user"
    available_sessions: int = 5
    available_submissions: int = 5
    is_active: bool = True


class UserRegister(BaseModel):
    email: str
    username: str | None = None
    password: str


class UserSelfUpdate(BaseModel):
    username: str | None = None
    email: str | None = None
    password: str | None = None


class UserUpdate(BaseModel):
    email: str | None = None
    username: str | None = None
    role: Literal["user", "admin"] | None = None
    is_active: bool | None = None
    available_sessions: int | None = None
    available_submissions: int | None = None
    next_info_task_index: int | None = None
    next_complaint_task_index: int | None = None


class CounterUpdate(BaseModel):
    available_sessions: int | None = None
    available_submissions: int | None = None


class InfoTaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_number: int
    source_text: str
    situation_text: str
    instruction_text: str
    expected_key_points: list[str]
    is_active: bool


class ComplaintTaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_number: int
    source_text: str
    situation_text: str
    instruction_text: str
    expected_key_points: list[str]
    is_active: bool


class InfoTaskCreate(BaseModel):
    task_number: int | None = None
    source_text: str
    situation_text: str
    instruction_text: str
    expected_key_points: list[str]
    is_active: bool = False


class InfoTaskUpdate(BaseModel):
    task_number: int | None = None
    source_text: str | None = None
    situation_text: str | None = None
    instruction_text: str | None = None
    expected_key_points: list[str] | None = None
    is_active: bool | None = None


class ComplaintTaskCreate(BaseModel):
    task_number: int | None = None
    source_text: str
    situation_text: str
    instruction_text: str
    expected_key_points: list[str]
    is_active: bool = False


class ComplaintTaskUpdate(BaseModel):
    task_number: int | None = None
    source_text: str | None = None
    situation_text: str | None = None
    instruction_text: str | None = None
    expected_key_points: list[str] | None = None
    is_active: bool | None = None


class TaskSessionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    started_at: datetime
    submitted_at: datetime | None
    duration_seconds: int | None
    selected_task_type: str | None
    status: str
    info_task: InfoTaskRead
    complaint_task: ComplaintTaskRead


class StartTaskSessionResponse(BaseModel):
    session: TaskSessionRead
    display_title: str


class TaskSessionSelectionUpdateRequest(BaseModel):
    selected_task_type: Literal["info", "complaint"]


class SubmitEvaluationRequest(BaseModel):
    task_session_id: int
    selected_task_type: Literal["info", "complaint"]
    candidate_text: str


class SubmitEvaluationResponse(BaseModel):
    submission_id: int
    task_session_id: int
    selected_task_type: str
    selected_task_id: int
    result: dict[str, Any]


class SubmissionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_session_id: int
    selected_task_type: str
    selected_task_id: int
    candidate_text: str
    result: dict[str, Any]
    raw_score: int | None
    final_score: int | None
    max_score: int | None
    word_count: int | None
    started_at: datetime | None
    submitted_at: datetime
    duration_seconds: int | None
    status: str
    error_message: str | None


if __name__ == "__main__":
    sample_request = SubmitEvaluationRequest(
        task_session_id=1,
        selected_task_type="info",
        candidate_text="Sehr geehrte Damen und Herren, ...",
    )
    print("api_schemas.py smoke test passed.")
    print(sample_request.model_dump())

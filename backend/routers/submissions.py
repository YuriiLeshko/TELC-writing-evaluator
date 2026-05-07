from __future__ import annotations
"""
Submission router for evaluating and retrieving TELC writing attempts.

Purpose:
- Evaluate candidate text for a selected session task and persist results.
- Expose submission history and single-submission retrieval for demo user.

Structure:
- Key-point parsing and submission-to-schema mapping helpers.
- `POST /submissions/evaluate` async evaluation endpoint.
- `GET /submissions/my` and `GET /submissions/{submission_id}` read endpoints.

Dependencies:
- `fastapi` for routing/dependencies/HTTP errors.
- `sqlalchemy` for session queries and persistence.
- `backend.evaluation.pipeline.evaluate_writing` and evaluation input schema.
- `backend.models` and `backend.api_schemas`.
"""

import json
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from backend.api_schemas import (
    SubmissionRead,
    SubmitEvaluationRequest,
    SubmitEvaluationResponse,
)
from backend.database import get_db
from backend.evaluation.pipeline import evaluate_writing
from backend.evaluation.schemas import WritingEvaluationInput
from backend.models import Submission, TaskSession, User
from backend.routers.users import get_demo_current_user

router = APIRouter(prefix="/submissions", tags=["submissions"])


def parse_key_points(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return []
        if isinstance(parsed, list):
            return [str(item) for item in parsed]
    return []


def _sanitize_result_for_api(result_payload: dict[str, Any]) -> dict[str, Any]:
    """Shape evaluation JSON for API clients.

    Strips redundant / internal-only shapes but keeps grades, scaled points,
    analysis_status/analysis_error for partial or failed criteria (nullable).
    Highlighted-error objects exclude legacy ``aspect``.
    Top-level keys (topic_mismatch, overall analysis_status/error, scores, improved_text)
    pass through unchanged from ``WritingEvaluationResult.model_dump``.
    """
    sanitized = dict(result_payload)
    criterion_i = sanitized.get("criterion_I")
    if isinstance(criterion_i, dict):
        sanitized["criterion_I"] = {
            "grade": criterion_i.get("grade"),
            "points": criterion_i.get("points"),
            "scaled_points": criterion_i.get("scaled_points"),
            "max_scaled_points": criterion_i.get("max_scaled_points"),
            "comment": criterion_i.get("comment"),
            "analysis_status": criterion_i.get("analysis_status"),
            "analysis_error": criterion_i.get("analysis_error"),
            "task_achievement_summary": criterion_i.get("task_achievement_summary"),
            "key_point_details": criterion_i.get("key_point_details", []),
        }
    criterion_ii = sanitized.get("criterion_II")
    if isinstance(criterion_ii, dict):
        sanitized["criterion_II"] = {
            "grade": criterion_ii.get("grade"),
            "points": criterion_ii.get("points"),
            "scaled_points": criterion_ii.get("scaled_points"),
            "max_scaled_points": criterion_ii.get("max_scaled_points"),
            "comment": criterion_ii.get("comment"),
            "analysis_status": criterion_ii.get("analysis_status"),
            "analysis_error": criterion_ii.get("analysis_error"),
            "communication_indicators": criterion_ii.get("communication_indicators", []),
        }
    criterion_iii = sanitized.get("criterion_III")
    if isinstance(criterion_iii, dict):
        sanitized["criterion_III"] = {
            "grade": criterion_iii.get("grade"),
            "points": criterion_iii.get("points"),
            "scaled_points": criterion_iii.get("scaled_points"),
            "max_scaled_points": criterion_iii.get("max_scaled_points"),
            "comment": criterion_iii.get("comment"),
            "analysis_status": criterion_iii.get("analysis_status"),
            "analysis_error": criterion_iii.get("analysis_error"),
            "aspect_ratings": criterion_iii.get("aspect_ratings"),
            "highlighted_errors": [
                {
                    "text": item.get("text"),
                    "correction": item.get("correction"),
                    "error_type": item.get("error_type"),
                    "explanation": item.get("explanation"),
                }
                for item in criterion_iii.get("highlighted_errors", [])
                if isinstance(item, dict)
            ],
        }
    return sanitized


def submission_to_schema(submission: Submission) -> SubmissionRead:
    result_value = submission.result_json if isinstance(submission.result_json, dict) else {}
    return SubmissionRead(
        id=submission.id,
        task_session_id=submission.task_session_id,
        selected_task_type=submission.selected_task_type,
        selected_task_id=submission.selected_task_id,
        candidate_text=submission.candidate_text,
        result=result_value,
        raw_score=submission.raw_score,
        final_score=submission.final_score,
        max_score=submission.max_score,
        word_count=submission.word_count,
        started_at=submission.started_at,
        submitted_at=submission.submitted_at,
        duration_seconds=submission.duration_seconds,
        status=submission.status,
        error_message=submission.error_message,
    )


@router.post("/evaluate", response_model=SubmitEvaluationResponse)
async def evaluate_submission(
    payload: SubmitEvaluationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_demo_current_user),
) -> SubmitEvaluationResponse:
    if not current_user.is_active:
        raise HTTPException(status_code=403, detail="User is inactive.")
    if current_user.available_submissions <= 0:
        raise HTTPException(status_code=403, detail="No available submissions left.")

    session = db.scalar(
        select(TaskSession)
        .options(joinedload(TaskSession.info_task), joinedload(TaskSession.complaint_task))
        .where(
            TaskSession.id == payload.task_session_id,
            TaskSession.user_id == current_user.id,
        )
    )
    if session is None:
        raise HTTPException(status_code=404, detail="Task session not found.")
    if session.status == "submitted":
        raise HTTPException(status_code=400, detail="Session already submitted.")

    if payload.selected_task_type == "info":
        selected_task = session.info_task
    elif payload.selected_task_type == "complaint":
        selected_task = session.complaint_task
    else:
        raise HTTPException(status_code=400, detail="Invalid selected_task_type.")

    expected_key_points = parse_key_points(selected_task.expected_key_points_json)
    task_text = (
        f"Ausgangstext:\n{selected_task.source_text}\n\n"
        f"Situation:\n{selected_task.situation_text}\n\n"
        f"Ihre Aufgabe:\n{selected_task.instruction_text}"
    )
    input_data = WritingEvaluationInput(
        task_text=task_text,
        expected_key_points=expected_key_points,
        candidate_text=payload.candidate_text,
    )

    try:
        result = await evaluate_writing(input_data)
        result_payload = _sanitize_result_for_api(result.model_dump(mode="json"))
        submitted_at = datetime.now(timezone.utc)
        started_at = session.started_at
        if started_at.tzinfo is None:
            started_at = started_at.replace(tzinfo=timezone.utc)
        duration_seconds = int((submitted_at - started_at).total_seconds())
        duration_seconds = max(duration_seconds, 0)

        session.submitted_at = submitted_at
        session.duration_seconds = duration_seconds
        session.selected_task_type = payload.selected_task_type
        session.selected_task_id = selected_task.id
        session.status = "submitted"
        current_user.available_submissions -= 1

        submission = Submission(
            user_id=current_user.id,
            task_session_id=session.id,
            selected_task_type=payload.selected_task_type,
            selected_task_id=selected_task.id,
            candidate_text=payload.candidate_text,
            result_json=result_payload,
            raw_score=result.raw_score,
            final_score=result.final_score,
            max_score=result.max_score,
            word_count=result.word_count.value if result.word_count else None,
            started_at=started_at,
            submitted_at=submitted_at,
            duration_seconds=duration_seconds,
            status="success",
        )
        db.add(submission)
        db.commit()
        db.refresh(submission)

        return SubmitEvaluationResponse(
            submission_id=submission.id,
            task_session_id=submission.task_session_id,
            selected_task_type=submission.selected_task_type,
            selected_task_id=submission.selected_task_id,
            result=result_payload,
        )
    except Exception as exc:
        failed_submitted_at = datetime.now(timezone.utc)
        failed_started_at = session.started_at
        if failed_started_at.tzinfo is None:
            failed_started_at = failed_started_at.replace(tzinfo=timezone.utc)
        failed_duration_seconds = int((failed_submitted_at - failed_started_at).total_seconds())
        failed_duration_seconds = max(failed_duration_seconds, 0)
        failed_submission = Submission(
            user_id=current_user.id,
            task_session_id=session.id,
            selected_task_type=payload.selected_task_type,
            selected_task_id=selected_task.id,
            candidate_text=payload.candidate_text,
            result_json={},
            started_at=failed_started_at,
            submitted_at=failed_submitted_at,
            duration_seconds=failed_duration_seconds,
            status="failed",
            error_message=str(exc),
        )
        db.add(failed_submission)
        db.commit()
        raise HTTPException(status_code=500, detail="Evaluation failed.") from exc


@router.get("/my", response_model=list[SubmissionRead])
def list_my_submissions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_demo_current_user),
) -> list[SubmissionRead]:
    submissions = db.scalars(
        select(Submission)
        .where(Submission.user_id == current_user.id)
        .order_by(Submission.id.desc())
    ).all()
    return [submission_to_schema(item) for item in submissions]


@router.get("/active", response_model=list[SubmissionRead])
def list_active_submissions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_demo_current_user),
) -> list[SubmissionRead]:
    submissions = db.scalars(
        select(Submission)
        .where(Submission.user_id == current_user.id)
        .order_by(Submission.id.desc())
    ).all()
    return [submission_to_schema(item) for item in submissions]


@router.get("/{submission_id}", response_model=SubmissionRead)
def get_submission(
    submission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_demo_current_user),
) -> SubmissionRead:
    submission = db.scalar(
        select(Submission).where(
            Submission.id == submission_id,
            Submission.user_id == current_user.id,
        )
    )
    if submission is None:
        raise HTTPException(status_code=404, detail="Submission not found.")
    return submission_to_schema(submission)


@router.delete("/{submission_id}")
def delete_submission(
    submission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_demo_current_user),
) -> dict[str, int | str]:
    submission = db.scalar(
        select(Submission).where(
            Submission.id == submission_id,
            Submission.user_id == current_user.id,
        )
    )
    if submission is None:
        raise HTTPException(status_code=404, detail="Submission not found.")
    db.delete(submission)
    db.commit()
    return {"status": "deleted", "submission_id": submission_id}


if __name__ == "__main__":
    parsed_from_list = parse_key_points(["k1", "k2"])
    parsed_from_json = parse_key_points('["k3", "k4"]')
    print("submissions.py smoke test passed.")
    print(f"parse list -> {parsed_from_list}")
    print(f"parse json -> {parsed_from_json}")

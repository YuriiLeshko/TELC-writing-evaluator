"""TELC B2 key-points checker for Criterion I inputs.

This module extracts fulfilled expected key points, relevant own ideas, and
invalid points from candidate writing. It does not assign criterion grades or
points and does not perform scoring.
"""

from __future__ import annotations

from typing import Any

from backend.evaluation.prompts.key_points import (
    SYSTEM_PROMPT,
    build_key_points_user_prompt,
)
from backend.evaluation.schemas import KeyPointCheckResult, WritingEvaluationInput
from backend.services.llm_client import LLMClient


def _ensure_string_list(value: object) -> list[str]:
    """Normalize possible LLM list-like outputs to list[str]."""
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        stripped = value.strip()
        return [stripped] if stripped else []
    return []


def _ensure_dict_list(value: object) -> list[dict]:
    """Normalize possible LLM object-list outputs to list[dict]."""
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    return []


def _normalize_status(value: Any) -> str:
    normalized = str(value or "").strip().lower()
    if normalized in {"fulfilled", "partially_fulfilled", "not_fulfilled"}:
        return normalized
    if normalized in {"partial", "partially", "teilweise"}:
        return "partially_fulfilled"
    return "not_fulfilled"


def _normalize_level(value: Any) -> str | None:
    if value in (None, ""):
        return None
    normalized = str(value).strip().upper()
    if normalized in {"B2", "B1+", "B1", "A2"}:
        return normalized
    return None


def _normalize_sentence_count(value: Any) -> int:
    try:
        return max(int(value), 0)
    except (TypeError, ValueError):
        return 0


def _normalize_expected_key_point_details(
    expected_key_points: list[str],
    raw_details: list[dict],
) -> list[dict[str, Any]]:
    normalized_by_text: dict[str, dict[str, Any]] = {}
    normalized_by_number: dict[int, dict[str, Any]] = {}

    expected_norm_to_index = {
        str(point).strip().lower(): idx + 1 for idx, point in enumerate(expected_key_points)
    }

    for item in raw_details:
        raw_type = str(item.get("type", "")).strip().lower()
        if raw_type == "own_idea":
            continue
        key_point = str(item.get("key_point", "")).strip()
        if not key_point:
            continue

        number = item.get("number")
        try:
            number_int = int(number) if number is not None else None
        except (TypeError, ValueError):
            number_int = None
        if number_int is None:
            number_int = expected_norm_to_index.get(key_point.lower())

        normalized = {
            "number": number_int,
            "type": "expected",
            "key_point": key_point,
            "status": _normalize_status(item.get("status")),
            "sentence_count": _normalize_sentence_count(item.get("sentence_count")),
            "situation_appropriate": item.get("situation_appropriate"),
            "language_level": _normalize_level(item.get("language_level")),
            "comment": str(item.get("comment") or "").strip() or "Keine Details verfügbar.",
        }
        normalized_by_text[key_point.lower()] = normalized
        if number_int is not None:
            normalized_by_number[number_int] = normalized

    result: list[dict[str, Any]] = []
    for idx, expected_point in enumerate(expected_key_points, start=1):
        expected_key = str(expected_point).strip().lower()
        detail = normalized_by_number.get(idx) or normalized_by_text.get(expected_key)
        if detail is None:
            detail = {
                "number": idx,
                "type": "expected",
                "key_point": expected_point,
                "status": "not_fulfilled",
                "sentence_count": 0,
                "situation_appropriate": None,
                "language_level": None,
                "comment": "Dieser Leitpunkt wurde nicht ausreichend erfüllt.",
            }
        else:
            detail["number"] = idx
            detail["type"] = "expected"
            detail["key_point"] = expected_point
        result.append(detail)
    return result


def _build_own_idea_details(own_ideas: list[str]) -> list[dict[str, Any]]:
    return [
        {
            "number": None,
            "type": "own_idea",
            "key_point": idea,
            "status": "fulfilled",
            "sentence_count": 1,
            "situation_appropriate": True,
            "language_level": None,
            "comment": "Relevante eigene Idee.",
        }
        for idea in own_ideas
    ]


async def check_key_points(
    llm_client: LLMClient,
    input_data: WritingEvaluationInput,
) -> KeyPointCheckResult:
    """Check fulfilled key points and relevant own ideas for Criterion I."""
    user_prompt = build_key_points_user_prompt(
        task_text=input_data.task_text,
        expected_key_points=input_data.expected_key_points,
        candidate_text=input_data.candidate_text,
    )

    raw_result = await llm_client.call_llm_json(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        temperature=0.0,
        max_tokens=900,
    )
    if not isinstance(raw_result, dict):
        raise ValueError("Key-points checker must return a JSON object.")

    raw_result["fulfilled_key_points"] = _ensure_string_list(
        raw_result.get("fulfilled_key_points")
    )
    raw_result["own_ideas"] = _ensure_string_list(raw_result.get("own_ideas"))
    raw_result["invalid_points"] = _ensure_string_list(raw_result.get("invalid_points"))
    raw_result["positive_feedback"] = _ensure_string_list(
        raw_result.get("positive_feedback")
    )
    raw_result["improvement_feedback"] = _ensure_string_list(
        raw_result.get("improvement_feedback")
    )
    raw_details = _ensure_dict_list(raw_result.get("key_point_details"))
    normalized_expected_details = _normalize_expected_key_point_details(
        expected_key_points=input_data.expected_key_points,
        raw_details=raw_details,
    )
    own_idea_details = _build_own_idea_details(raw_result["own_ideas"])
    raw_result["key_point_details"] = normalized_expected_details + own_idea_details

    return KeyPointCheckResult.model_validate(raw_result)


if __name__ == "__main__":
    import asyncio

    async def _smoke_test() -> None:
        llm_client = LLMClient()
        input_data = WritingEvaluationInput(
            task_text=(
                "Sie haben online ein Produkt gekauft, aber es wurde beschädigt geliefert. "
                "Schreiben Sie eine formelle E-Mail an den Kundenservice. "
                "Beschreiben Sie das Problem, erklären Sie Ihre Erwartungen und bitten Sie um eine Lösung."
            ),
            expected_key_points=[
                "Problem mit beschädigtem Produkt beschreiben",
                "Erwartungen erklären",
                "Um eine Lösung bitten",
            ],
            candidate_text=(
                "Betreff: Beschädigte Lieferung\n\n"
                "Sehr geehrte Damen und Herren,\n\n"
                "ich habe letzte Woche bei Ihnen einen Kopfhörer bestellt. Leider ist das Paket "
                "beschädigt angekommen, und der Kopfhörer funktioniert nicht richtig. Deshalb bin ich "
                "mit der Lieferung nicht zufrieden.\n\n"
                "Ich erwarte, dass Sie mir entweder ein neues Gerät schicken oder den Kaufpreis "
                "zurückerstatten. Bitte informieren Sie mich, wie wir dieses Problem lösen können.\n\n"
                "Mit freundlichen Grüßen\n"
                "Max Müller"
            ),
        )

        result = await check_key_points(llm_client=llm_client, input_data=input_data)
        print(result.model_dump_json(indent=2))
        print("key_point_details:", result.key_point_details)

    asyncio.run(_smoke_test())

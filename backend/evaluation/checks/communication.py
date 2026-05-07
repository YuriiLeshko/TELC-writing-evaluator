"""TELC B2 communicative-design checker for Criterion II inputs.

This module extracts structured communication features from candidate writing.
It does not assign grades or points and does not perform any scoring.
"""

from __future__ import annotations

from typing import Any

from backend.evaluation.prompts.communication import (
    SYSTEM_PROMPT,
    build_communication_user_prompt,
)
from backend.evaluation.schemas import CommunicationCheckResult, WritingEvaluationInput
from backend.services.llm_client import LLMClient

ASPECTS_IN_ORDER = [
    "email_elements",
    "structure",
    "coherence",
    "cohesion",
    "register",
    "vocabulary",
    "sentence_variety",
]

ASPECT_LABELS = {
    "email_elements": "E-Mail-Elemente",
    "structure": "Struktur",
    "coherence": "Zusammenhang",
    "cohesion": "Verknüpfungen",
    "register": "Register und Stil",
    "vocabulary": "Wortschatz",
    "sentence_variety": "Satzvielfalt",
}

STATUS_NORMALIZATION = {
    "strong": "strong",
    "good": "strong",
    "adequate": "adequate",
    "acceptable": "adequate",
    "ok": "adequate",
    "weak": "weak",
    "missing": "missing",
    "absent": "missing",
    "none": "missing",
    "inappropriate": "inappropriate",
    "not_appropriate": "inappropriate",
    "unsuitable": "inappropriate",
}


def _normalize_status(value: Any) -> str:
    normalized = str(value or "").strip().lower()
    return STATUS_NORMALIZATION.get(normalized, normalized)


def _normalize_string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError("communication_details list fields must be arrays when provided")
    return [str(item).strip() for item in value if str(item).strip()]


def _normalize_level(value: Any) -> str | None:
    if value in (None, ""):
        return None
    normalized = str(value).strip().upper()
    if normalized in {"B2", "B1+", "B1", "A2"}:
        return normalized
    return None


def _build_default_detail(aspect: str) -> dict[str, Any]:
    return {
        "aspect": aspect,
        "label": ASPECT_LABELS[aspect],
        "status": "missing",
        "level": None,
        "present_items": [],
        "missing_items": [],
        "evidence": [],
        "comment": "Keine ausreichenden Hinweise im Text erkannt.",
    }


def _normalize_communication_details(value: Any) -> list[dict[str, Any]]:
    if value is None:
        details_in: list[dict[str, Any]] = []
    elif not isinstance(value, list):
        raise ValueError("communication_details must be a JSON array")
    else:
        details_in = [item for item in value if isinstance(item, dict)]
        if value and not details_in:
            raise ValueError("communication_details must contain JSON objects")

    details_by_aspect: dict[str, dict[str, Any]] = {}
    for item in details_in:
        aspect = str(item.get("aspect", "")).strip().lower()
        if aspect not in ASPECT_LABELS:
            continue

        normalized = {
            "aspect": aspect,
            "label": str(item.get("label") or ASPECT_LABELS[aspect]).strip() or ASPECT_LABELS[aspect],
            "status": _normalize_status(item.get("status")),
            "level": _normalize_level(item.get("level")),
            "present_items": _normalize_string_list(item.get("present_items")),
            "missing_items": _normalize_string_list(item.get("missing_items")),
            "evidence": _normalize_string_list(item.get("evidence")),
            "comment": str(item.get("comment") or "").strip() or "Keine Details verfügbar.",
        }
        details_by_aspect[aspect] = normalized

    return [details_by_aspect.get(aspect, _build_default_detail(aspect)) for aspect in ASPECTS_IN_ORDER]


async def check_communication(
    llm_client: LLMClient,
    input_data: WritingEvaluationInput,
) -> CommunicationCheckResult:
    """Check communicative design features for Criterion II."""
    user_prompt = build_communication_user_prompt(
        task_text=input_data.task_text,
        candidate_text=input_data.candidate_text,
    )

    raw_result = await llm_client.call_llm_json(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        temperature=0.0,
        max_tokens=900,
    )
    if not isinstance(raw_result, dict):
        raise ValueError("Communication checker must return a JSON object.")

    raw_result["communication_details"] = _normalize_communication_details(raw_result.get("communication_details"))

    return CommunicationCheckResult.model_validate(raw_result)


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

        result = await check_communication(llm_client=llm_client, input_data=input_data)
        print(result.model_dump_json(indent=2))
        print("communication_details:", result.communication_details)

    asyncio.run(_smoke_test())

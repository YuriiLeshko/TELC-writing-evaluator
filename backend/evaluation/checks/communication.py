"""TELC B2 communicative-design checker for Criterion II inputs.

This module extracts structured communication features from candidate writing.
It does not assign grades or points and does not perform any scoring.
"""

from __future__ import annotations

from typing import Any

from backend.evaluation.prompts.communication import (
    REPAIR_INSTRUCTION,
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

RATING_NORMALIZATION = {
    "excellent": "excellent",
    "strong": "excellent",
    "very_good": "excellent",
    "good": "good",
    "appropriate": "good",
    "adequate": "acceptable",
    "acceptable": "acceptable",
    "mostly_appropriate": "acceptable",
    "ok": "acceptable",
    "weak": "weak",
    "poor": "weak",
    "inappropriate": "weak",
    "varied": "good",
    "some_variety": "acceptable",
    "simple": "weak",
    "incoherent": "missing",
    "missing": "missing",
    "absent": "missing",
    "none": "missing",
}


def _normalize_rating(value: Any) -> str:
    normalized = str(value or "").strip().lower()
    if not normalized:
        return "missing"
    return RATING_NORMALIZATION.get(normalized, "weak")


def _normalize_vocabulary_level(value: Any) -> str:
    normalized = str(value or "").strip().upper()
    if normalized in {"B2", "B1+", "B1", "A2"}:
        return normalized
    return "B1"


def _derive_email_structure_quality(raw_result: dict[str, Any]) -> Any:
    if raw_result.get("email_structure_quality") not in (None, ""):
        return raw_result.get("email_structure_quality")

    boolean_keys = [
        "has_subject",
        "has_greeting",
        "has_introduction",
        "has_body_structure",
        "has_conclusion",
        "has_closing",
    ]
    bool_values = [raw_result.get(key) for key in boolean_keys if key in raw_result]
    if not bool_values:
        return None

    true_count = sum(bool(value) for value in bool_values)
    total_count = len(bool_values)
    ratio = true_count / total_count if total_count else 0.0

    if ratio >= 0.95:
        return "excellent"
    if ratio >= 0.7:
        return "good"
    if ratio >= 0.4:
        return "acceptable"
    if ratio > 0.0:
        return "weak"
    return "missing"


def _normalize_communication_result_fields(raw_result: dict[str, Any]) -> None:
    # Support both new schema fields and old prompt/checkpoint aliases.
    raw_result["email_structure_quality"] = _normalize_rating(
        _derive_email_structure_quality(raw_result)
    )
    raw_result["coherence_quality"] = _normalize_rating(
        raw_result.get("coherence_quality")
    )
    raw_result["cohesion_quality"] = _normalize_rating(
        raw_result.get("cohesion_quality")
    )
    raw_result["register_quality"] = _normalize_rating(
        raw_result.get("register_quality")
    )
    raw_result["sentence_variety_quality"] = _normalize_rating(
        raw_result.get("sentence_variety_quality", raw_result.get("sentence_variety"))
    )
    raw_result["vocabulary_level"] = _normalize_vocabulary_level(
        raw_result.get("vocabulary_level")
    )


def _build_default_indicator(aspect: str) -> dict[str, Any]:
    return {
        "aspect": aspect,
        "label": ASPECT_LABELS[aspect],
        "rating": "missing",
        "comment": "Keine ausreichenden Hinweise im Text erkannt.",
    }


def _normalize_communication_indicators(value: Any) -> list[dict[str, Any]]:
    if value is None:
        indicators_in: list[dict[str, Any]] = []
    elif not isinstance(value, list):
        raise ValueError("communication_indicators must be a JSON array")
    else:
        indicators_in = [item for item in value if isinstance(item, dict)]
        if value and not indicators_in:
            raise ValueError("communication_indicators must contain JSON objects")

    indicators_by_aspect: dict[str, dict[str, Any]] = {}
    for item in indicators_in:
        aspect = str(item.get("aspect", "")).strip().lower()
        if aspect not in ASPECT_LABELS:
            continue

        normalized = {
            "aspect": aspect,
            "label": ASPECT_LABELS[aspect],
            "rating": _normalize_rating(item.get("rating")),
            "comment": str(item.get("comment") or "").strip() or "Keine Details verfügbar.",
        }
        indicators_by_aspect[aspect] = normalized

    return [indicators_by_aspect.get(aspect, _build_default_indicator(aspect)) for aspect in ASPECTS_IN_ORDER]


async def check_communication(
    llm_client: LLMClient,
    input_data: WritingEvaluationInput,
    *,
    append_schema_repair_hint: bool = False,
) -> CommunicationCheckResult:
    """Check communicative design features for Criterion II.

    Performs a single LLM call. Retry policy lives in ``pipeline.evaluate_writing``;
    pass ``append_schema_repair_hint=True`` on subsequent pipeline attempts to append
    a short schema discipline reminder to the user prompt (see ``REPAIR_INSTRUCTION``).
    """
    base_user_prompt = build_communication_user_prompt(
        task_text=input_data.task_text,
        candidate_text=input_data.candidate_text,
    )
    user_prompt = (
        base_user_prompt
        if not append_schema_repair_hint
        else f"{base_user_prompt}\n\n{REPAIR_INSTRUCTION}"
    )
    raw_result = await llm_client.call_llm_json(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        temperature=0.0,
        max_tokens=2200,
    )
    if not isinstance(raw_result, dict):
        raise ValueError("Communication checker must return a JSON object.")

    _normalize_communication_result_fields(raw_result)
    raw_result["communication_indicators"] = _normalize_communication_indicators(
        raw_result.get("communication_indicators")
    )
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
        print("communication_indicators:", result.communication_indicators)

    asyncio.run(_smoke_test())

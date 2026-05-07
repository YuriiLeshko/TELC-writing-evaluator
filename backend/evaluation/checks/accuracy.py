"""TELC B2 formal-accuracy checker for Criterion III inputs.

This module extracts structured formal-accuracy features from candidate writing.
It does not assign grades or points and does not perform any scoring.
"""

from __future__ import annotations

from typing import Any

from backend.evaluation.prompts.accuracy import (
    SYSTEM_PROMPT,
    build_accuracy_user_prompt,
)
from backend.evaluation.schemas import AccuracyCheckResult, WritingEvaluationInput
from backend.services.llm_client import LLMClient


ACCURACY_ASPECTS = [
    "grammar",
    "syntax",
    "word_order",
    "verb_forms",
    "agreement",
    "spelling",
    "punctuation",
    "capitalization",
    "comprehension",
]


ACCURACY_STATUS_NORMALIZATION = {
    "strong": "strong",
    "excellent": "strong",
    "good": "strong",
    "adequate": "adequate",
    "acceptable": "adequate",
    "ok": "adequate",
    "weak": "weak",
    "problematic": "problematic",
    "poor": "problematic",
    "bad": "problematic",
}


def _normalize_accuracy_status(value: Any) -> str:
    """Normalize possible LLM status values to AccuracyStatus."""
    normalized = str(value or "").strip().lower()
    return ACCURACY_STATUS_NORMALIZATION.get(normalized, "adequate")


def _normalize_aspect_ratings(value: Any) -> dict[str, str]:
    """Normalize simple per-aspect formal-accuracy ratings.

    The checker guarantees that all required Criterion III aspects are present.
    """
    if not isinstance(value, dict):
        value = {}

    return {
        aspect: _normalize_accuracy_status(value.get(aspect))
        for aspect in ACCURACY_ASPECTS
    }


def _normalize_highlighted_errors(
    value: Any,
    candidate_text: str,
) -> list[dict[str, Any]]:
    """Normalize concrete user-facing errors.

    Keeps only errors whose text is an exact fragment of candidate_text.
    Limits output to 10 highlighted errors.
    """
    if value is None:
        return []

    if not isinstance(value, list):
        raise ValueError("highlighted_errors must be a JSON array")

    items = [item for item in value if isinstance(item, dict)]

    if value and not items:
        raise ValueError("highlighted_errors must contain JSON objects")

    normalized: list[dict[str, Any]] = []

    for item in items:
        text = str(item.get("text") or "").strip()
        correction = str(item.get("correction") or "").strip()
        error_type = str(item.get("error_type") or "").strip()
        explanation = str(item.get("explanation") or "").strip()

        if not (text and correction and error_type and explanation):
            continue

        if text not in candidate_text:
            continue

        if len(text.split()) > 12:
            continue

        normalized.append(
            {
                "text": text,
                "correction": correction,
                "error_type": error_type,
                "explanation": explanation,
            }
        )

        if len(normalized) >= 10:
            break

    return normalized


async def check_accuracy(
    llm_client: LLMClient,
    input_data: WritingEvaluationInput,
) -> AccuracyCheckResult:
    """Check formal accuracy features for Criterion III."""
    user_prompt = build_accuracy_user_prompt(
        candidate_text=input_data.candidate_text,
    )

    raw_result = await llm_client.call_llm_json(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        temperature=0.0,
        max_tokens=1400,
    )

    if not isinstance(raw_result, dict):
        raise ValueError("Accuracy checker must return a JSON object.")

    raw_result["aspect_ratings"] = _normalize_aspect_ratings(
        raw_result.get("aspect_ratings")
    )

    raw_result["highlighted_errors"] = _normalize_highlighted_errors(
        raw_result.get("highlighted_errors"),
        input_data.candidate_text,
    )

    return AccuracyCheckResult.model_validate(raw_result)


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
                "ich habe letzte Woche bei Ihnen ein Kopfhörer gekauft. Leider ist das Paket "
                "beschädigt angekommen, und es funktioniert nicht richtig. Deshalb bin ich "
                "mit der Lieferung nicht zufrieden.\n\n"
                "Ich erwarte, dass Sie mir entweder ein neues Gerät schicken oder den Kaufpreis "
                "zurückerstatten. Bitte informieren Sie mich, wie wir dieses Problem lösen können.\n\n"
                "Mit freundlichen Grüßen\n"
                "Max Müller"
            ),
        )

        result = await check_accuracy(llm_client=llm_client, input_data=input_data)
        print(result.model_dump_json(indent=2))
        print("aspect_ratings:", result.aspect_ratings)
        print("highlighted_errors:", result.highlighted_errors)

    asyncio.run(_smoke_test())
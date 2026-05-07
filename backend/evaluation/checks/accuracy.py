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

ACCURACY_ASPECTS_IN_ORDER = [
    "grammar",
    "syntax",
    "word_order",
    "spelling",
    "punctuation",
    "comprehension",
]

ACCURACY_LABELS = {
    "grammar": "Grammatik",
    "syntax": "Satzbau",
    "word_order": "Wortstellung",
    "spelling": "Rechtschreibung",
    "punctuation": "Zeichensetzung",
    "comprehension": "Verständlichkeit",
}

STATUS_NORMALIZATION = {
    "strong": "strong",
    "good": "strong",
    "adequate": "adequate",
    "acceptable": "adequate",
    "weak": "weak",
    "problematic": "problematic",
    "poor": "problematic",
}


def _normalize_status(value: Any) -> str:
    normalized = str(value or "").strip().lower()
    return STATUS_NORMALIZATION.get(normalized, "adequate")


def _normalize_error_count(value: Any) -> int:
    try:
        return max(int(value), 0)
    except (TypeError, ValueError):
        return 0


def _normalize_accuracy_details(value: Any) -> list[dict[str, Any]]:
    if value is None:
        details_in: list[dict[str, Any]] = []
    elif not isinstance(value, list):
        raise ValueError("accuracy_details must be a JSON array")
    else:
        details_in = [item for item in value if isinstance(item, dict)]
        if value and not details_in:
            raise ValueError("accuracy_details must contain JSON objects")

    by_aspect: dict[str, dict[str, Any]] = {}
    for item in details_in:
        aspect = str(item.get("aspect", "")).strip().lower()
        if aspect not in ACCURACY_LABELS:
            continue
        by_aspect[aspect] = {
            "aspect": aspect,
            "label": str(item.get("label") or ACCURACY_LABELS[aspect]).strip() or ACCURACY_LABELS[aspect],
            "status": _normalize_status(item.get("status")),
            "error_count": _normalize_error_count(item.get("error_count")),
            "evidence": [],
            "comment": str(item.get("comment") or "").strip() or "Keine Details verfügbar.",
        }

    return [
        by_aspect.get(
            aspect,
            {
                "aspect": aspect,
                "label": ACCURACY_LABELS[aspect],
                "status": "strong",
                "error_count": 0,
                "evidence": [],
                "comment": "Keine auffälligen Probleme erkannt.",
            },
        )
        for aspect in ACCURACY_ASPECTS_IN_ORDER
    ]


def _normalize_highlighted_errors(value: Any, candidate_text: str) -> list[dict[str, Any]]:
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
        max_tokens=900,
    )
    if not isinstance(raw_result, dict):
        raise ValueError("Accuracy checker must return a JSON object.")

    raw_result["accuracy_details"] = _normalize_accuracy_details(raw_result.get("accuracy_details"))
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
        print("accuracy_details:", result.accuracy_details)
        print("highlighted_errors:", result.highlighted_errors)

    asyncio.run(_smoke_test())

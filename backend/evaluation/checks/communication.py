"""TELC B2 communicative-design checker for Criterion II inputs.

This module extracts structured communication features from candidate writing.
It does not assign grades or points and does not perform any scoring.
"""

from __future__ import annotations

import logging
from typing import Any

from backend.evaluation.prompts.communication import (
    REPAIR_INSTRUCTION,
    SYSTEM_PROMPT,
    build_communication_user_prompt,
)
from backend.evaluation.schemas import CommunicationCheckResult, WritingEvaluationInput
from backend.services.llm_client import LLMJSONParseError
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

logger = logging.getLogger(__name__)

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
    "adequate": "acceptable",
    "acceptable": "acceptable",
    "ok": "acceptable",
    "weak": "weak",
    "missing": "missing",
    "absent": "missing",
    "none": "missing",
}


class CommunicationAnalysisFailed(Exception):
    """Raised when Criterion II analysis fails across all retry attempts."""


def _normalize_rating(value: Any) -> str:
    normalized = str(value or "").strip().lower()
    return RATING_NORMALIZATION.get(normalized, normalized)


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
            "label": str(item.get("label") or ASPECT_LABELS[aspect]).strip() or ASPECT_LABELS[aspect],
            "rating": _normalize_rating(item.get("rating")),
            "comment": str(item.get("comment") or "").strip() or "Keine Details verfügbar.",
        }
        indicators_by_aspect[aspect] = normalized

    return [indicators_by_aspect.get(aspect, _build_default_indicator(aspect)) for aspect in ASPECTS_IN_ORDER]


async def check_communication(
    llm_client: LLMClient,
    input_data: WritingEvaluationInput,
) -> CommunicationCheckResult:
    """Check communicative design features for Criterion II."""
    base_user_prompt = build_communication_user_prompt(
        task_text=input_data.task_text,
        candidate_text=input_data.candidate_text,
    )
    errors: list[str] = []

    for attempt in range(1, 4):
        user_prompt = base_user_prompt if attempt == 1 else f"{base_user_prompt}\n\n{REPAIR_INSTRUCTION}"
        try:
            raw_result = await llm_client.call_llm_json(
                system_prompt=SYSTEM_PROMPT,
                user_prompt=user_prompt,
                temperature=0.0,
                max_tokens=2200,
            )
            if not isinstance(raw_result, dict):
                raise ValueError("Communication checker must return a JSON object.")

            raw_result["communication_indicators"] = _normalize_communication_indicators(
                raw_result.get("communication_indicators")
            )
            return CommunicationCheckResult.model_validate(raw_result)
        except (LLMJSONParseError, ValueError) as exc:
            logger.warning("Communication check attempt %s failed: %s", attempt, exc)
            errors.append(f"attempt {attempt}: {exc}")
        except Exception as exc:
            logger.warning("Communication check attempt %s validation failed: %s", attempt, exc)
            errors.append(f"attempt {attempt}: {exc}")

    raise CommunicationAnalysisFailed("; ".join(errors))


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

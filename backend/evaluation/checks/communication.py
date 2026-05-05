"""TELC B2 communicative-design checker for Criterion II inputs.

This module extracts structured communication features from candidate writing.
It does not assign grades or points and does not perform any scoring.
"""

from __future__ import annotations

from backend.evaluation.prompts.communication import (
    SYSTEM_PROMPT,
    build_communication_user_prompt,
)
from backend.evaluation.schemas import CommunicationCheckResult, WritingEvaluationInput
from backend.services.llm_client import LLMClient


def _ensure_dict_list(value: object) -> list[dict]:
    """Normalize possible LLM object-list outputs to list[dict]."""
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    return []


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
    raw_result["communication_details"] = _ensure_dict_list(
        raw_result.get("communication_details")
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
        print("communication_details:", result.communication_details)

    asyncio.run(_smoke_test())

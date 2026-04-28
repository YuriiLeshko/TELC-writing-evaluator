"""TELC B2 key-points checker for Criterion I inputs.

This module extracts fulfilled expected key points, relevant own ideas, and
invalid points from candidate writing. It does not assign criterion grades or
points and does not perform scoring.
"""

from __future__ import annotations

from backend.evaluation.prompts.key_points import (
    SYSTEM_PROMPT,
    build_key_points_user_prompt,
)
from backend.evaluation.schemas import KeyPointCheckResult, WritingEvaluationInput
from backend.services.llm_client import LLMClient


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

    asyncio.run(_smoke_test())

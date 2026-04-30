"""TELC B2 formal-accuracy checker for Criterion III inputs.

This module extracts structured formal-accuracy features from candidate writing.
It does not assign grades or points and does not perform any scoring.
"""

from __future__ import annotations

from backend.evaluation.prompts.accuracy import (
    SYSTEM_PROMPT,
    build_accuracy_user_prompt,
)
from backend.evaluation.schemas import AccuracyCheckResult, WritingEvaluationInput
from backend.services.llm_client import LLMClient


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

    asyncio.run(_smoke_test())

"""Generate an improved TELC B2 candidate text after evaluation.

Purpose:
- Produce a corrected and better-structured German version of the candidate text.
- Preserve original intent and avoid inventing specific facts.
- Support learning feedback without affecting scoring.

This module does NOT:
- calculate scores
- modify criterion grades or points
- change evaluation outcomes
"""

from __future__ import annotations

from backend.services.llm_client import LLMClient
from backend.evaluation.prompts.improvement import (
    SYSTEM_PROMPT,
    build_improvement_user_prompt,
)
from backend.evaluation.schemas import ImprovedTextResult, WritingEvaluationInput


async def generate_improved_text(
    llm_client: LLMClient,
    input_data: WritingEvaluationInput,
) -> ImprovedTextResult:
    """Generate and validate an improved German candidate text."""
    user_prompt = build_improvement_user_prompt(input_data)
    raw_result = await llm_client.call_llm_json(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        temperature=0.2,
        max_tokens=1200,
    )
    return ImprovedTextResult.model_validate(raw_result)


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
        result = await generate_improved_text(llm_client=llm_client, input_data=input_data)
        print(result.model_dump_json(indent=2))

    asyncio.run(_smoke_test())

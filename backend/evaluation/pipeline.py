"""TELC B2 writing evaluation orchestration pipeline.

Purpose
-------
This module orchestrates the full TELC B2 writing assessment flow. It accepts
validated input, executes LLM-based extraction checks in strict TELC order, then
applies deterministic scoring and returns a structured final result.

Evaluation order
----------------
1) Relevance pre-check (topic and situation)
2) Topic mismatch short-circuit (D/D/D and immediate return)
3) Key points check (Criterion I evidence)
4) Communicative design check (Criterion II evidence)
5) Formal accuracy check (Criterion III evidence)
6) Deterministic scoring and final result build

Dependencies
------------
- LLM extraction checks from `backend.evaluation.checks.*`
- Deterministic scoring from `backend.evaluation.scoring`
- Result assembly via `backend.evaluation.result_builder` (with safe fallback)

Notes
-----
- LLM checks in this pipeline extract structured data only.
- Score and final-score calculations are deterministic.
- This module does not contain prompt text or scoring rules.
"""

from __future__ import annotations

import asyncio

from backend.services.llm_client import LLMClient

from backend.evaluation.schemas import (
    AccuracyCheckResult,
    CommunicationCheckResult,
    KeyPointCheckResult,
    RelevanceCheckResult,
    WritingEvaluationInput,
    WritingEvaluationResult,
)

from backend.evaluation.checks.relevance import check_relevance
from backend.evaluation.checks.key_points import check_key_points
from backend.evaluation.checks.communication import check_communication
from backend.evaluation.checks.accuracy import check_accuracy

from backend.evaluation.scoring import (
    calculate_final_score,
    make_score,
    score_all_criteria,
)
import backend.evaluation.result_builder as result_builder_module


def _build_result_fallback(
    *,
    relevance: RelevanceCheckResult,
    key_points: KeyPointCheckResult,
    communication: CommunicationCheckResult,
    accuracy: AccuracyCheckResult,
    criterion_i,
    criterion_ii,
    criterion_iii,
    final_score,
) -> WritingEvaluationResult:
    """Build final result locally when result_builder has no builder function."""
    return WritingEvaluationResult(
        topic_mismatch=relevance.topic_mismatch,
        situation_mismatch=relevance.situation_mismatch,
        criterion_I=criterion_i,
        criterion_II=criterion_ii,
        criterion_III=criterion_iii,
        raw_score=final_score.raw_score,
        final_score=final_score.final_score,
        max_score=final_score.max_score,
        explanations={
            "relevance": relevance.explanation,
            "criterion_I": key_points.explanation,
            "criterion_II": communication.explanation,
            "criterion_III": accuracy.explanation,
        },
    )


def _build_final_result(
    *,
    relevance: RelevanceCheckResult,
    key_points: KeyPointCheckResult,
    communication: CommunicationCheckResult,
    accuracy: AccuracyCheckResult,
    criterion_i,
    criterion_ii,
    criterion_iii,
    final_score,
) -> WritingEvaluationResult:
    """Call project result builder if available, else use local fallback."""
    builder = getattr(result_builder_module, "build_final_result", None)
    if callable(builder):
        return builder(
            relevance=relevance,
            key_points=key_points,
            communication=communication,
            accuracy=accuracy,
            criterion_i=criterion_i,
            criterion_ii=criterion_ii,
            criterion_iii=criterion_iii,
            final_score=final_score,
        )
    return _build_result_fallback(
        relevance=relevance,
        key_points=key_points,
        communication=communication,
        accuracy=accuracy,
        criterion_i=criterion_i,
        criterion_ii=criterion_ii,
        criterion_iii=criterion_iii,
        final_score=final_score,
    )


async def evaluate_writing(
    input_data: WritingEvaluationInput,
    llm_client: LLMClient | None = None,
) -> WritingEvaluationResult:
    """Run full TELC B2 writing evaluation pipeline."""
    if llm_client is None:
        llm_client = LLMClient()

    relevance = await check_relevance(llm_client, input_data)

    if relevance.topic_mismatch:
        criterion_i = make_score("D")
        criterion_ii = make_score("D")
        criterion_iii = make_score("D")
        final_score = calculate_final_score(
            criterion_i,
            criterion_ii,
            criterion_iii,
        )

        key_points = KeyPointCheckResult(
            fulfilled_key_points=[],
            own_ideas=[],
            invalid_points=[],
            explanation="Skipped due to topic mismatch.",
        )
        communication = CommunicationCheckResult(
            has_subject=False,
            has_greeting=False,
            has_introduction=False,
            has_body_structure=False,
            has_conclusion=False,
            has_closing=False,
            register_quality="inappropriate",
            coherence_quality="incoherent",
            vocabulary_level="A2",
            sentence_variety="simple",
            explanation="Skipped due to topic mismatch.",
        )
        accuracy = AccuracyCheckResult(
            grammar_control="basic",
            systematic_errors=[],
            spelling_quality="poor",
            punctuation_quality="poor",
            comprehension_affected=True,
            explanation="Skipped due to topic mismatch.",
        )

        return _build_final_result(
            relevance=relevance,
            key_points=key_points,
            communication=communication,
            accuracy=accuracy,
            criterion_i=criterion_i,
            criterion_ii=criterion_ii,
            criterion_iii=criterion_iii,
            final_score=final_score,
        )

    key_points, communication, accuracy = await asyncio.gather(
        check_key_points(llm_client, input_data),
        check_communication(llm_client, input_data),
        check_accuracy(llm_client, input_data),
    )

    criterion_i, criterion_ii, criterion_iii, final_score = score_all_criteria(
        relevance=relevance,
        key_points=key_points,
        communication=communication,
        accuracy=accuracy,
    )

    return _build_final_result(
        relevance=relevance,
        key_points=key_points,
        communication=communication,
        accuracy=accuracy,
        criterion_i=criterion_i,
        criterion_ii=criterion_ii,
        criterion_iii=criterion_iii,
        final_score=final_score,
    )


if __name__ == "__main__":
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

        result = await evaluate_writing(input_data=input_data, llm_client=llm_client)
        print(result.model_dump_json(indent=2))

    asyncio.run(_smoke_test())

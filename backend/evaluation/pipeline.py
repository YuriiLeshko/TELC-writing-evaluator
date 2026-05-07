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
import logging

from backend.services.llm_client import LLMClient

from backend.evaluation.schemas import (
    AccuracyCheckResult,
    CommunicationCheckResult,
    ImprovedTextResult,
    KeyPointCheckResult,
    RelevanceCheckResult,
    WordCountCheck,
    WritingEvaluationInput,
    WritingEvaluationResult,
)

from backend.evaluation.checks.relevance import check_relevance
from backend.evaluation.checks.key_points import check_key_points
from backend.evaluation.checks.communication import check_communication
from backend.evaluation.checks.accuracy import check_accuracy
from backend.evaluation.improvement import generate_improved_text

from backend.evaluation.scoring import apply_word_count_override, calculate_final_score, make_score, score_all_criteria
from backend.evaluation.result_builder import build_final_result

MINIMUM_WORD_COUNT = 150
logger = logging.getLogger(__name__)


def count_words(text: str) -> int:
    """Count words in candidate text deterministically."""
    stripped = text.strip()
    if not stripped:
        return 0
    return sum(1 for token in stripped.split() if token)


def _build_word_count_check(word_count: int) -> WordCountCheck:
    """Build structured word count metadata for final output."""
    return WordCountCheck(
        value=word_count,
        minimum_required=MINIMUM_WORD_COUNT,
        meets_requirement=word_count >= MINIMUM_WORD_COUNT,
    )


def _fallback_relevance_result() -> RelevanceCheckResult:
    """Return safe relevance fallback when LLM check fails."""
    return RelevanceCheckResult(
        topic_mismatch=False,
        situation_mismatch=False,
        explanation="Automatischer Fallback: Relevanz konnte wegen LLM-Ausfall nicht zuverlässig geprüft werden.",
        positive_feedback=[],
        improvement_feedback=[
            "Bitte später erneut prüfen, da der Relevanz-Check technisch fehlgeschlagen ist."
        ],
    )


def _fallback_key_points_result() -> KeyPointCheckResult:
    """Return safe key-point fallback when LLM check fails."""
    return KeyPointCheckResult(
        fulfilled_key_points=[],
        own_ideas=[],
        invalid_points=[],
        explanation="Automatischer Fallback: Leitpunkt-Analyse war wegen LLM-Ausfall nicht verfügbar.",
        positive_feedback=[],
        improvement_feedback=[
            "Bitte später erneut analysieren, um eine vollständige Leitpunkt-Bewertung zu erhalten."
        ],
    )


def _fallback_accuracy_result() -> AccuracyCheckResult:
    """Return safe formal-accuracy fallback when LLM check fails."""
    return AccuracyCheckResult(
        grammar_control="basic",
        systematic_errors=[],
        spelling_quality="poor",
        punctuation_quality="poor",
        comprehension_affected=True,
        explanation="Automatischer Fallback: Sprachrichtigkeitsanalyse war wegen LLM-Ausfall nicht verfügbar.",
        positive_feedback=[],
        improvement_feedback=[
            "Bitte später erneut prüfen, um belastbare Hinweise zu Grammatik und Orthografie zu erhalten."
        ],
        example_errors=[],
        technical_notes=["Technischer Fallback ohne detaillierte Fehleranalyse."],
        aspect_ratings={
            "grammar": "problematic",
            "syntax": "problematic",
            "word_order": "problematic",
            "verb_forms": "problematic",
            "agreement": "problematic",
            "spelling": "problematic",
            "punctuation": "problematic",
            "capitalization": "problematic",
            "comprehension": "problematic",
        },
    )


async def evaluate_writing(
    input_data: WritingEvaluationInput,
    llm_client: LLMClient | None = None,
) -> WritingEvaluationResult:
    """Run full TELC B2 writing evaluation pipeline."""
    if llm_client is None:
        llm_client = LLMClient()

    word_count = count_words(input_data.candidate_text)
    word_count_check = _build_word_count_check(word_count)
    try:
        relevance = await check_relevance(llm_client, input_data)
    except Exception:
        logger.exception("Relevance check failed, using fallback result.")
        relevance = _fallback_relevance_result()

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
            email_structure_quality="missing",
            coherence_quality="missing",
            cohesion_quality="missing",
            register_quality="weak",
            vocabulary_level="A2",
            sentence_variety_quality="weak",
            explanation="Skipped due to topic mismatch.",
        )
        accuracy = AccuracyCheckResult(
            grammar_control="basic",
            systematic_errors=[],
            spelling_quality="poor",
            punctuation_quality="poor",
            comprehension_affected=True,
            explanation="Skipped due to topic mismatch.",
            aspect_ratings={
                "grammar": "problematic",
                "syntax": "problematic",
                "word_order": "problematic",
                "verb_forms": "problematic",
                "agreement": "problematic",
                "spelling": "problematic",
                "punctuation": "problematic",
                "capitalization": "problematic",
                "comprehension": "problematic",
            },
        )
        try:
            improved_text = await generate_improved_text(
                llm_client=llm_client,
                input_data=input_data,
                key_points_result=key_points,
                communication_result=communication,
                accuracy_result=accuracy,
            )
        except Exception:
            logger.exception("Improved text generation failed, using fallback improved text.")
            improved_text = ImprovedTextResult(
                improved_text=input_data.candidate_text,
                changes_summary=[
                    "Technischer Fallback: Verbesserte Version konnte wegen LLM-Ausfall nicht erstellt werden."
                ],
            )

        return build_final_result(
            relevance=relevance,
            key_points=key_points,
            communication=communication,
            accuracy=accuracy,
            criterion_i=criterion_i,
            criterion_ii=criterion_ii,
            criterion_iii=criterion_iii,
            final_score=final_score,
            word_count=word_count_check,
            improved_text=improved_text,
        )

    checks = await asyncio.gather(
        check_key_points(llm_client, input_data),
        check_communication(llm_client, input_data),
        check_accuracy(llm_client, input_data),
        return_exceptions=True,
    )
    key_points_result, communication_result, accuracy_result = checks

    if isinstance(key_points_result, Exception):
        logger.error(
            "Key-points check failed, using fallback result.",
            exc_info=(
                type(key_points_result),
                key_points_result,
                key_points_result.__traceback__,
            ),
        )
        key_points = _fallback_key_points_result()
    else:
        key_points = key_points_result

    communication_analysis_failed = False
    communication_analysis_error = ""
    if isinstance(communication_result, Exception):
        logger.error(
            "Communication check failed.",
            exc_info=(
                type(communication_result),
                communication_result,
                communication_result.__traceback__,
            ),
        )
        communication_analysis_failed = True
        communication_analysis_error = (
            "Die kommunikative Gestaltung konnte technisch nicht zuverlässig analysiert werden."
        )
        communication = CommunicationCheckResult(
            email_structure_quality="missing",
            coherence_quality="missing",
            cohesion_quality="missing",
            register_quality="weak",
            vocabulary_level="A2",
            sentence_variety_quality="weak",
            explanation=communication_analysis_error,
            communication_indicators=[],
        )
    else:
        communication = communication_result

    if isinstance(accuracy_result, Exception):
        logger.error(
            "Accuracy check failed, using fallback result.",
            exc_info=(
                type(accuracy_result),
                accuracy_result,
                accuracy_result.__traceback__,
            ),
        )
        accuracy = _fallback_accuracy_result()
    else:
        accuracy = accuracy_result

    criterion_i, criterion_ii, criterion_iii, final_score = score_all_criteria(
        relevance=relevance,
        key_points=key_points,
        communication=communication,
        accuracy=accuracy,
    )
    criterion_i, criterion_ii, criterion_iii = apply_word_count_override(
        word_count=word_count,
        minimum_required=MINIMUM_WORD_COUNT,
        criterion_i=criterion_i,
        criterion_ii=criterion_ii,
        criterion_iii=criterion_iii,
    )
    final_score = calculate_final_score(
        criterion_i,
        criterion_ii,
        criterion_iii,
    )
    if communication_analysis_failed:
        criterion_ii = make_score("D")
        final_score = calculate_final_score(
            criterion_i,
            criterion_ii,
            criterion_iii,
        )
    try:
        improved_text = await generate_improved_text(
            llm_client=llm_client,
            input_data=input_data,
            key_points_result=key_points,
            communication_result=communication,
            accuracy_result=accuracy,
        )
    except Exception:
        logger.exception("Improved text generation failed, using fallback improved text.")
        improved_text = ImprovedTextResult(
            improved_text=input_data.candidate_text,
            changes_summary=[
                "Technischer Fallback: Verbesserte Version konnte wegen LLM-Ausfall nicht erstellt werden."
            ],
        )

    return build_final_result(
        relevance=relevance,
        key_points=key_points,
        communication=communication,
        accuracy=accuracy,
        criterion_i=criterion_i,
        criterion_ii=criterion_ii,
        criterion_iii=criterion_iii,
        final_score=final_score,
        word_count=word_count_check,
        improved_text=improved_text,
        communication_analysis_status="failed" if communication_analysis_failed else "success",
        communication_analysis_error=communication_analysis_error if communication_analysis_failed else None,
    )


if __name__ == "__main__":
    async def _smoke_test() -> None:
        llm_client = LLMClient()
        short_input_data = WritingEvaluationInput(
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

        short_result = await evaluate_writing(
            input_data=short_input_data,
            llm_client=llm_client,
        )
        print("SHORT TEXT RESULT (<150 words):")
        print(short_result.model_dump_json(indent=2))

        long_candidate_text = (
            "Betreff: Beschädigte Lieferung und Bitte um Lösung\n\n"
            "Sehr geehrte Damen und Herren,\n\n"
            "ich wende mich heute an Sie, weil ich mit meiner letzten Bestellung ein ernstes Problem habe. "
            "Vor einigen Tagen habe ich in Ihrem Onlineshop einen Kopfhörer bestellt, den ich beruflich und "
            "privat regelmäßig nutzen wollte. Das Paket kam zwar pünktlich an, war aber von außen deutlich "
            "beschädigt. Beim Öffnen habe ich gesehen, dass auch die Verpackung des Geräts eingedrückt war. "
            "Nach einem kurzen Test musste ich feststellen, dass der Kopfhörer nur auf einer Seite Ton wiedergibt "
            "und zudem ein störendes Rauschen verursacht.\n\n"
            "Ich habe mich bewusst für Ihr Produkt entschieden, weil ich bisher gute Erfahrungen mit Ihrem "
            "Kundenservice gemacht habe und auf Qualität vertraut habe. Umso enttäuschter bin ich jetzt über den "
            "aktuellen Zustand der Lieferung. Da ich das Gerät zeitnah brauche, erwarte ich eine schnelle und "
            "kundenorientierte Lösung. Aus meiner Sicht wäre entweder ein umgehender Ersatzversand oder eine "
            "vollständige Rückerstattung des Kaufpreises angemessen.\n\n"
            "Bitte teilen Sie mir mit, welche Schritte ich als Nächstes durchführen soll und an welche Adresse "
            "ich das defekte Produkt zurücksenden kann. Ich wäre Ihnen dankbar, wenn Sie meine Anfrage zeitnah "
            "bearbeiten könnten, damit das Problem möglichst schnell geklärt wird.\n\n"
            "Mit freundlichen Grüßen\n"
            "Max Müller"
        )
        long_input_data = WritingEvaluationInput(
            task_text=short_input_data.task_text,
            expected_key_points=short_input_data.expected_key_points,
            candidate_text=long_candidate_text,
        )
        long_result = await evaluate_writing(
            input_data=long_input_data,
            llm_client=llm_client,
        )
        print("\nLONG TEXT RESULT (>150 words):")
        print(long_result.model_dump_json(indent=2))

    asyncio.run(_smoke_test())

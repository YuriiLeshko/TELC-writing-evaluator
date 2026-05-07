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
from collections.abc import Awaitable, Callable
from typing import TypeVar

from backend.services.llm_client import LLMClient

from backend.evaluation.schemas import (
    AccuracyCheckResult,
    CommunicationCheckResult,
    CriterionScore,
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

from backend.evaluation.scoring import (
    apply_word_count_override,
    calculate_final_score,
    make_score,
    score_criterion_i,
    score_criterion_ii,
    score_criterion_iii,
)
from backend.evaluation.result_builder import build_final_result

MINIMUM_WORD_COUNT = 150
logger = logging.getLogger(__name__)
RETRY_ATTEMPTS = 3
T = TypeVar("T")


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


async def _run_with_retries(
    checker_name: str,
    task_factory: Callable[[], Awaitable[T]],
    attempts: int = RETRY_ATTEMPTS,
) -> T:
    last_exc: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            return await task_factory()
        except Exception as exc:  # noqa: PERF203
            last_exc = exc
            logger.warning(
                "%s attempt %s/%s failed: %s",
                checker_name,
                attempt,
                attempts,
                exc,
            )
    raise RuntimeError(f"{checker_name} failed after {attempts} attempts") from last_exc


def _failed_criterion(message: str) -> CriterionScore:
    return CriterionScore(
        grade=None,
        points=None,
        comment=message,
        analysis_status="failed",
        analysis_error=message,
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
        relevance = await _run_with_retries(
            checker_name="relevance",
            task_factory=lambda: check_relevance(llm_client, input_data),
        )
    except Exception:
        logger.exception("Relevance check failed after retries.")
        fail_message = (
            "Die Relevanzprüfung konnte technisch nicht durchgeführt werden. "
            "Die Bewertung wurde abgebrochen."
        )
        failed = _failed_criterion(fail_message)
        return build_final_result(
            relevance=None,
            key_points=None,
            communication=None,
            accuracy=None,
            criterion_i=failed,
            criterion_ii=failed.model_copy(deep=True),
            criterion_iii=failed.model_copy(deep=True),
            final_score=None,
            word_count=word_count_check,
            improved_text=ImprovedTextResult(
                improved_text=input_data.candidate_text,
                changes_summary=["Technischer Hinweis: Verbesserung konnte nicht erstellt werden."],
            ),
            overall_analysis_status="failed",
            overall_analysis_error=fail_message,
        )

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
            explanation="Analyse wurde wegen Themenverfehlung übersprungen.",
            positive_feedback=[],
            improvement_feedback=[
                "Die Leitpunktanalyse wurde wegen Themenverfehlung nicht durchgeführt."
            ],
            key_point_details=[],
        )
        communication = CommunicationCheckResult(
            email_structure_quality="missing",
            coherence_quality="missing",
            cohesion_quality="missing",
            register_quality="weak",
            vocabulary_level="A2",
            sentence_variety_quality="weak",
            explanation="Analyse wurde wegen Themenverfehlung übersprungen.",
            communication_indicators=[],
        )
        accuracy = AccuracyCheckResult(
            grammar_control="basic",
            systematic_errors=[],
            spelling_quality="poor",
            punctuation_quality="poor",
            comprehension_affected=True,
            explanation="Analyse wurde wegen Themenverfehlung übersprungen.",
            positive_feedback=[],
            improvement_feedback=[
                "Die Sprachrichtigkeitsanalyse wurde wegen Themenverfehlung nicht durchgeführt."
            ],
            example_errors=[],
            technical_notes=[],
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
            highlighted_errors=[],
        )
        improved_text = ImprovedTextResult(
            improved_text=input_data.candidate_text,
            changes_summary=[
                "Keine verbesserte Version erstellt, da der Text das Thema verfehlt."
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
            overall_analysis_status="success",
            overall_analysis_error=None,
        )

    checks = await asyncio.gather(
        _run_with_retries("key_points", lambda: check_key_points(llm_client, input_data)),
        # communication checker already has an internal 3-attempt repair loop.
        # Keep a single outer attempt to avoid 3 x 3 duplicated retries.
        _run_with_retries("communication", lambda: check_communication(llm_client, input_data), attempts=1),
        _run_with_retries("accuracy", lambda: check_accuracy(llm_client, input_data)),
        return_exceptions=True,
    )
    key_points_result, communication_result, accuracy_result = checks

    key_points = key_points_result if not isinstance(key_points_result, Exception) else None
    communication = communication_result if not isinstance(communication_result, Exception) else None
    accuracy = accuracy_result if not isinstance(accuracy_result, Exception) else None

    key_failed_msg = "Die Leitpunktanalyse konnte technisch nicht durchgeführt werden. Dieses Kriterium wurde nicht bewertet."
    comm_failed_msg = "Die Analyse der kommunikativen Gestaltung konnte technisch nicht durchgeführt werden. Dieses Kriterium wurde nicht bewertet."
    acc_failed_msg = "Die Sprachrichtigkeitsanalyse konnte technisch nicht durchgeführt werden. Dieses Kriterium wurde nicht bewertet."

    criterion_i = (
        score_criterion_i(relevance, key_points) if key_points is not None else _failed_criterion(key_failed_msg)
    )
    criterion_ii = (
        score_criterion_ii(relevance, communication)
        if communication is not None
        else _failed_criterion(comm_failed_msg)
    )
    criterion_iii = (
        score_criterion_iii(relevance, accuracy) if accuracy is not None else _failed_criterion(acc_failed_msg)
    )

    if (
        criterion_i.analysis_status != "failed"
        and criterion_ii.analysis_status != "failed"
        and criterion_iii.analysis_status != "failed"
    ):
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
        overall_analysis_status = "success"
        overall_analysis_error = None
    else:
        final_score = None
        overall_analysis_status = "partial"
        failed_messages = [
            msg
            for msg, criterion in (
                (key_failed_msg, criterion_i),
                (comm_failed_msg, criterion_ii),
                (acc_failed_msg, criterion_iii),
            )
            if criterion.analysis_status == "failed"
        ]
        overall_analysis_error = " ".join(failed_messages)
    if overall_analysis_status != "success":
        improved_text = ImprovedTextResult(
            improved_text=input_data.candidate_text,
            changes_summary=[
                "Keine verbesserte Version erstellt, da die Bewertung nicht vollständig durchgeführt werden konnte."
            ],
        )
    else:
        assert key_points is not None
        assert communication is not None
        assert accuracy is not None
        try:
            improved_text = await _run_with_retries(
                checker_name="improved_text",
                task_factory=lambda: generate_improved_text(
                    llm_client=llm_client,
                    input_data=input_data,
                    key_points_result=key_points,
                    communication_result=communication,
                    accuracy_result=accuracy,
                ),
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
        overall_analysis_status=overall_analysis_status,
        overall_analysis_error=overall_analysis_error,
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

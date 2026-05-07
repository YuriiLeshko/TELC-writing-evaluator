"""Build concise TELC B2 evaluation payload with per-criterion comments."""

from __future__ import annotations

from typing import Literal

from backend.evaluation.schemas import (
    AccuracyCheckResult,
    CommunicationCheckResult,
    CriterionScore,
    FinalScore,
    KeyPointCheckResult,
    RelevanceCheckResult,
    WordCountCheck,
    ImprovedTextResult,
    WritingEvaluationResult,
    TaskAchievementSummary,
)


def _first_or_default(items: list[str], default: str) -> str:
    """Return the first non-empty item or fallback text."""
    for item in items:
        stripped = item.strip()
        if stripped:
            return stripped
    return default


def _build_criterion_i_comment(key_points: KeyPointCheckResult) -> str:
    """Create concise Criterion I comment from key-point evidence."""
    fulfilled_count = len(key_points.fulfilled_key_points)
    own_idea_count = len(key_points.own_ideas)
    positive = _first_or_default(
        key_points.positive_feedback,
        f"{fulfilled_count} Leitpunkt(e) sind klar ausgearbeitet.",
    )
    if key_points.invalid_points:
        improvement = f"Zur Verbesserung sollte Folgendes gezielt ausgearbeitet werden: {key_points.invalid_points[0]}."
    elif own_idea_count == 0:
        improvement = "Zur Verbesserung sollte eine relevante und gut ausgearbeitete eigene Idee ergänzt werden."
    else:
        improvement = _first_or_default(
            key_points.improvement_feedback,
            "Zur Verbesserung sollten mehr konkrete aufgabenbezogene Details ergänzt werden.",
        )
    return f"{positive} {improvement}"


def _build_task_achievement_summary(key_points: KeyPointCheckResult) -> TaskAchievementSummary:
    """Build frontend-facing Criterion I summary from normalized details."""
    details = key_points.key_point_details or []
    expected_details = [d for d in details if d.type == "expected"]
    own_idea_count = len(key_points.own_ideas)

    fulfilled_count = len([d for d in expected_details if d.status == "fulfilled"])
    partially_fulfilled_count = len([d for d in expected_details if d.status == "partially_fulfilled"])
    not_fulfilled_count = len([d for d in expected_details if d.status == "not_fulfilled"])

    level_priority = {"A2": 1, "B1": 2, "B1+": 3, "B2": 4}
    best_level: str | None = None
    for detail in details:
        lvl = detail.language_level
        if lvl is None:
            continue
        if best_level is None or level_priority[lvl] > level_priority[best_level]:
            best_level = lvl

    summary_comment = (
        f"{fulfilled_count} erfüllt, {partially_fulfilled_count} teilweise erfüllt, "
        f"{not_fulfilled_count} nicht erfüllt."
    )
    return TaskAchievementSummary(
        fulfilled_count=fulfilled_count,
        partially_fulfilled_count=partially_fulfilled_count,
        not_fulfilled_count=not_fulfilled_count,
        own_idea_count=own_idea_count,
        overall_level=best_level,
        summary_comment=summary_comment,
    )


def _build_criterion_ii_comment(communication: CommunicationCheckResult) -> str:
    """Create concise Criterion II comment from communication evidence."""
    return communication.explanation.strip() or "Die kommunikative Gestaltung wurde ausgewertet."


def _build_criterion_iii_comment(accuracy: AccuracyCheckResult) -> str:
    """Create concise Criterion III comment from formal-accuracy evidence."""
    positive = _first_or_default(
        accuracy.positive_feedback,
        "Grammatik, Rechtschreibung und Zeichensetzung sind überwiegend sicher.",
    )
    if accuracy.systematic_errors:
        improvement = f"Zur Verbesserung sollten wiederkehrende Fehler bei {accuracy.systematic_errors[0]} reduziert werden."
    elif accuracy.example_errors:
        improvement = f"Zur Verbesserung sollten Probleme wie {accuracy.example_errors[0]} gezielt korrigiert werden."
    else:
        improvement = _first_or_default(
            accuracy.improvement_feedback,
            "Zur Verbesserung sollten wiederkehrende formale Fehler gezielt korrigiert werden.",
        )
    return f"{positive} {improvement}"


def _attach_accuracy_errors(
    criterion_score: CriterionScore,
    accuracy: AccuracyCheckResult,
) -> CriterionScore:
    """Attach aspect ratings and structured error spans to Criterion III."""
    criterion_score.aspect_ratings = accuracy.aspect_ratings
    criterion_score.highlighted_errors = accuracy.highlighted_errors
    return criterion_score


def build_final_result(
    *,
    relevance: RelevanceCheckResult | None,
    key_points: KeyPointCheckResult | None,
    communication: CommunicationCheckResult | None,
    accuracy: AccuracyCheckResult | None,
    criterion_i: CriterionScore,
    criterion_ii: CriterionScore,
    criterion_iii: CriterionScore,
    final_score: FinalScore | None,
    word_count: WordCountCheck | None = None,
    improved_text: ImprovedTextResult,
    overall_analysis_status: Literal["success", "partial", "failed"] = "success",
    overall_analysis_error: str | None = None,
) -> WritingEvaluationResult:
    """Build final result with concise criterion-level comments."""
    if criterion_i.analysis_status != "failed" and key_points is not None:
        criterion_i.comment = _build_criterion_i_comment(key_points)
        criterion_i.scaled_points = (criterion_i.points or 0) * 3
        criterion_i.max_scaled_points = 15
        criterion_i.key_point_details = key_points.key_point_details
        criterion_i.task_achievement_summary = _build_task_achievement_summary(key_points)
        criterion_i.analysis_status = "success"
        criterion_i.analysis_error = None

    if criterion_ii.analysis_status != "failed" and communication is not None:
        criterion_ii.comment = _build_criterion_ii_comment(communication)
        criterion_ii.scaled_points = (criterion_ii.points or 0) * 3
        criterion_ii.max_scaled_points = 15
        criterion_ii.analysis_status = "success"
        criterion_ii.analysis_error = None
        criterion_ii.communication_indicators = communication.communication_indicators

    if criterion_iii.analysis_status != "failed" and accuracy is not None:
        criterion_iii.comment = _build_criterion_iii_comment(accuracy)
        criterion_iii.scaled_points = (criterion_iii.points or 0) * 3
        criterion_iii.max_scaled_points = 15
        criterion_iii = _attach_accuracy_errors(criterion_iii, accuracy)
        criterion_iii.analysis_status = "success"
        criterion_iii.analysis_error = None

    if (
        word_count is not None
        and not word_count.meets_requirement
        and criterion_i.analysis_status != "failed"
        and criterion_ii.analysis_status != "failed"
        and criterion_iii.analysis_status != "failed"
    ):
        note = " Die Endpunktzahl ist jedoch 0, weil der Text unter 150 Wörtern liegt."
        criterion_i.comment = (criterion_i.comment or "") + note
        criterion_ii.comment = (criterion_ii.comment or "") + note
        criterion_iii.comment = (criterion_iii.comment or "") + note

    return WritingEvaluationResult(
        topic_mismatch=relevance.topic_mismatch if relevance is not None else False,
        situation_mismatch=relevance.situation_mismatch if relevance is not None else False,
        criterion_I=criterion_i,
        criterion_II=criterion_ii,
        criterion_III=criterion_iii,
        word_count=word_count,
        improved_text=improved_text,
        analysis_status=overall_analysis_status,
        analysis_error=overall_analysis_error,
        raw_score=final_score.raw_score if final_score is not None else None,
        final_score=final_score.final_score if final_score is not None else None,
        max_score=final_score.max_score if final_score is not None else 45,
    )

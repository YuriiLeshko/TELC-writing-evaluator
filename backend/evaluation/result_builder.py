"""Build concise TELC B2 evaluation payload with per-criterion comments."""

from __future__ import annotations

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


def _build_criterion_ii_comment(communication: CommunicationCheckResult) -> str:
    """Create concise Criterion II comment from communication evidence."""
    positive = _first_or_default(
        communication.positive_feedback,
        "Der Text hat eine klare E-Mail-Struktur und ein überwiegend passendes Register.",
    )
    if communication.sentence_variety == "simple":
        improvement = "Zur Verbesserung sollten abwechslungsreichere Satzstrukturen verwendet werden."
    elif communication.vocabulary_level in {"B1", "A2"}:
        improvement = "Zur Verbesserung sollte ein breiterer und präziserer Wortschatz auf B2-Niveau genutzt werden."
    elif not communication.complex_connectors:
        improvement = "Zur Verbesserung sollten mehr komplexe Konnektoren zur Stärkung der Kohärenz verwendet werden."
    else:
        improvement = _first_or_default(
            communication.improvement_feedback,
            "Zur Verbesserung sollten Übergänge zwischen den Gedanken expliziter formuliert werden.",
        )
    return f"{positive} {improvement}"


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
            "Zur Verbesserung sollte die syntaktische Vielfalt erhöht werden, ohne die Korrektheit zu verlieren.",
        )
    return f"{positive} {improvement}"


def build_final_result(
    *,
    relevance: RelevanceCheckResult,
    key_points: KeyPointCheckResult,
    communication: CommunicationCheckResult,
    accuracy: AccuracyCheckResult,
    criterion_i: CriterionScore,
    criterion_ii: CriterionScore,
    criterion_iii: CriterionScore,
    final_score: FinalScore,
    word_count: WordCountCheck | None = None,
    improved_text: ImprovedTextResult,
) -> WritingEvaluationResult:
    """Build final result with concise criterion-level comments."""
    criterion_i.comment = _build_criterion_i_comment(key_points)
    criterion_ii.comment = _build_criterion_ii_comment(communication)
    criterion_iii.comment = _build_criterion_iii_comment(accuracy)
    if word_count is not None and not word_count.meets_requirement:
        note = " Die Endpunktzahl ist jedoch 0, weil der Text unter 150 Wörtern liegt."
        criterion_i.comment += note
        criterion_ii.comment += note
        criterion_iii.comment += note

    return WritingEvaluationResult(
        topic_mismatch=relevance.topic_mismatch,
        situation_mismatch=relevance.situation_mismatch,
        criterion_I=criterion_i,
        criterion_II=criterion_ii,
        criterion_III=criterion_iii,
        word_count=word_count,
        improved_text=improved_text,
        raw_score=final_score.raw_score,
        final_score=final_score.final_score,
        max_score=final_score.max_score,
    )

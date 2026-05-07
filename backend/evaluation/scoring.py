"""Deterministic scoring logic for TELC B2 writing evaluation.

Purpose
-------
This module converts structured evaluation outputs into TELC B2 writing scores
using fully deterministic Python rules. It is responsible only for score
assignment and score aggregation.

"""

from __future__ import annotations

from typing import Literal

from backend.evaluation.schemas import (
    AccuracyCheckResult,
    CommunicationCheckResult,
    CriterionScore,
    FinalScore,
    KeyPointCheckResult,
    RelevanceCheckResult,
)

MINIMUM_WORD_COUNT = 150

GRADE_POINTS = {
    "A": 5,
    "B": 3,
    "C": 1,
    "D": 0,
}


def make_score(grade: Literal["A", "B", "C", "D"]) -> CriterionScore:
    """Create a validated criterion score from a TELC grade."""
    return CriterionScore(grade=grade, points=GRADE_POINTS[grade])


def score_criterion_i(
    relevance: RelevanceCheckResult,
    key_points: KeyPointCheckResult,
) -> CriterionScore:
    """Score Criterion I (task achievement) deterministically."""
    if relevance.topic_mismatch:
        return make_score("D")

    if relevance.situation_mismatch:
        return make_score("D")

    fulfilled_count = len(key_points.fulfilled_key_points)
    own_idea_count = len(key_points.own_ideas)

    if fulfilled_count >= 3 or (fulfilled_count == 2 and own_idea_count >= 1):
        return make_score("A")

    if fulfilled_count == 2 or (fulfilled_count == 1 and own_idea_count >= 1):
        return make_score("B")

    if fulfilled_count == 1:
        return make_score("C")

    return make_score("D")


def score_criterion_ii(
    relevance: RelevanceCheckResult,
    communication: CommunicationCheckResult,
) -> CriterionScore:
    """Score Criterion II (communicative design) deterministically."""
    if relevance.topic_mismatch:
        return make_score("D")

    if communication.coherence_quality == "missing":
        return make_score("D")

    if communication.register_quality in {"weak", "missing"}:
        return make_score("D")

    is_a = (
        communication.email_structure_quality in {"excellent", "good"}
        and communication.register_quality == "excellent"
        and communication.coherence_quality == "excellent"
        and communication.cohesion_quality in {"excellent", "good"}
        and communication.vocabulary_level == "B2"
        and communication.sentence_variety_quality in {"excellent", "good"}
    )
    if is_a:
        return make_score("A")

    is_b = (
        communication.register_quality in {"good", "acceptable"}
        and communication.coherence_quality in {"good", "acceptable"}
        and communication.cohesion_quality in {"good", "acceptable", "weak"}
        and communication.email_structure_quality in {"excellent", "good", "acceptable"}
        and communication.vocabulary_level in {"B2", "B1+"}
        and communication.coherence_quality != "weak"
    )
    if is_b:
        return make_score("B")

    is_c = (
        communication.coherence_quality == "weak"
        or communication.vocabulary_level == "B1"
        or communication.sentence_variety_quality == "weak"
    )
    if is_c:
        return make_score("C")

    return make_score("D")


def score_criterion_iii(
    relevance: RelevanceCheckResult,
    accuracy: AccuracyCheckResult,
) -> CriterionScore:
    """Score Criterion III (formal accuracy) deterministically."""
    if relevance.topic_mismatch:
        return make_score("D")

    if accuracy.comprehension_affected:
        return make_score("D")

    systematic_error_count = len(accuracy.systematic_errors)

    is_a = (
        accuracy.grammar_control == "strong"
        and systematic_error_count <= 1
        and accuracy.spelling_quality == "good"
        and accuracy.punctuation_quality == "good"
    )
    if is_a:
        return make_score("A")

    is_b = (
        accuracy.grammar_control == "good"
        and systematic_error_count <= 3
        and accuracy.spelling_quality in {"good", "acceptable"}
        and accuracy.punctuation_quality in {"good", "acceptable"}
    )
    if is_b:
        return make_score("B")

    is_c = accuracy.grammar_control in {"unstable", "basic"} and not accuracy.comprehension_affected
    if is_c:
        return make_score("C")

    return make_score("D")


def calculate_final_score(
    criterion_i: CriterionScore,
    criterion_ii: CriterionScore,
    criterion_iii: CriterionScore,
) -> FinalScore:
    """Calculate raw and scaled TELC final scores."""
    raw_score = criterion_i.points + criterion_ii.points + criterion_iii.points
    final_score = raw_score * 3
    return FinalScore(raw_score=raw_score, final_score=final_score, max_score=45)


def apply_word_count_override(
    word_count: int,
    minimum_required: int,
    criterion_i: CriterionScore,
    criterion_ii: CriterionScore,
    criterion_iii: CriterionScore,
) -> tuple[CriterionScore, CriterionScore, CriterionScore]:
    """Apply TELC minimum word count hard override to criterion scores.

    If word count is below required minimum:
    - override all criteria to D
    - otherwise return original scores unchanged
    """
    if word_count < minimum_required:
        return make_score("D"), make_score("D"), make_score("D")
    return criterion_i, criterion_ii, criterion_iii


def score_all_criteria(
    relevance: RelevanceCheckResult,
    key_points: KeyPointCheckResult,
    communication: CommunicationCheckResult,
    accuracy: AccuracyCheckResult,
) -> tuple[CriterionScore, CriterionScore, CriterionScore, FinalScore]:
    """Score all TELC writing criteria and return the aggregated results."""
    criterion_i = score_criterion_i(relevance=relevance, key_points=key_points)
    criterion_ii = score_criterion_ii(relevance=relevance, communication=communication)
    criterion_iii = score_criterion_iii(relevance=relevance, accuracy=accuracy)
    final_score = calculate_final_score(
        criterion_i=criterion_i,
        criterion_ii=criterion_ii,
        criterion_iii=criterion_iii,
    )
    return criterion_i, criterion_ii, criterion_iii, final_score


if __name__ == "__main__":
    relevance = RelevanceCheckResult(
        topic_mismatch=False,
        situation_mismatch=False,
        explanation="The text matches the task and intended situation.",
    )

    key_points = KeyPointCheckResult(
        fulfilled_key_points=[
            "Problem described",
            "Consequences explained",
        ],
        own_ideas=[
            "Suggested a voucher as compensation",
        ],
        invalid_points=[],
        explanation="Two required points and one relevant own idea are present.",
    )

    communication = CommunicationCheckResult(
        email_structure_quality="good",
        coherence_quality="good",
        cohesion_quality="good",
        register_quality="good",
        sentence_variety_quality="good",
        vocabulary_level="B2",
        explanation="The email is well structured and appropriate in tone.",
    )

    accuracy = AccuracyCheckResult(
        grammar_control="good",
        systematic_errors=["Occasional article agreement issue"],
        spelling_quality="good",
        punctuation_quality="acceptable",
        comprehension_affected=False,
        explanation="Language is mostly accurate and remains clear throughout.",
    )

    criterion_i_result, criterion_ii_result, criterion_iii_result, final_score_result = score_all_criteria(
        relevance=relevance,
        key_points=key_points,
        communication=communication,
        accuracy=accuracy,
    )

    print("Criterion I:", criterion_i_result.model_dump())
    print("Criterion II:", criterion_ii_result.model_dump())
    print("Criterion III:", criterion_iii_result.model_dump())
    print("Final Score:", final_score_result.model_dump())

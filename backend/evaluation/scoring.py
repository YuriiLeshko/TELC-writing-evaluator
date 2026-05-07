"""Deterministic scoring logic for TELC B2 writing evaluation.

Purpose
-------
This module converts structured evaluation outputs into TELC B2 writing scores
using fully deterministic Python rules. It is responsible only for score
assignment and score aggregation.

Normative intent is aligned with ``task_examples&criteria/criteria.md`` (bands
for criteria I–III and Final Score = (I + II + III) × 3). Checker outputs feed
deterministic thresholds; nuanced rubric wording may not map 1:1 to every edge
case—in particular criterion III distinguishes A/B/C only within the hardened
gates below unless extended later.

"""

from __future__ import annotations

from typing import Literal

from backend.evaluation.schemas import (
    AccuracyCheckResult,
    CommunicationCheckResult,
    CriterionScore,
    FinalScore,
    KeyPointCheckResult,
    KeyPointDetail,
    RelevanceCheckResult,
)

GRADE_POINTS = {
    "A": 5,
    "B": 3,
    "C": 1,
    "D": 0,
}

FULFILLED_KEY_POINT_LEVELS = {"B2"}

COMMUNICATION_QUALITY_FIELDS = (
    "email_structure_quality",
    "coherence_quality",
    "cohesion_quality",
    "register_quality",
    "sentence_variety_quality",
)

ACCURACY_SCORING_ASPECTS: tuple[
    Literal[
        "grammar",
        "syntax",
        "word_order",
        "verb_forms",
        "agreement",
        "spelling",
        "punctuation",
        "capitalization",
        "comprehension",
    ],
    ...,
] = (
    "grammar",
    "syntax",
    "word_order",
    "verb_forms",
    "agreement",
    "spelling",
    "punctuation",
    "capitalization",
    "comprehension",
)

ACCURACY_CORE_ASPECTS: frozenset[str] = frozenset(
    {"grammar", "syntax", "word_order", "verb_forms", "agreement"}
)


def make_score(grade: Literal["A", "B", "C", "D"]) -> CriterionScore:
    """Create a validated criterion score from a TELC grade."""
    return CriterionScore(grade=grade, points=GRADE_POINTS[grade])


def _is_valid_fulfilled_key_point(detail: KeyPointDetail) -> bool:
    """Return True if this expected key-point row counts toward Criterion I fulfillment."""
    return (
        detail.type == "expected"
        and detail.status == "fulfilled"
        and detail.sentence_count >= 2
        and detail.situation_appropriate is not False
        and detail.language_level in FULFILLED_KEY_POINT_LEVELS
    )


def _count_valid_fulfilled_key_points(key_points: KeyPointCheckResult) -> int:
    return sum(
        1 for detail in key_points.key_point_details if _is_valid_fulfilled_key_point(detail)
    )


def _communication_quality_values(communication: CommunicationCheckResult) -> list[str]:
    return [getattr(communication, name) for name in COMMUNICATION_QUALITY_FIELDS]


def score_criterion_i(
    relevance: RelevanceCheckResult,
    key_points: KeyPointCheckResult,
) -> CriterionScore:
    """Score Criterion I (task achievement) deterministically."""
    if relevance.topic_mismatch:
        return make_score("D")

    if relevance.situation_mismatch:
        return make_score("D")

    fulfilled_count = _count_valid_fulfilled_key_points(key_points)
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

    if communication.register_quality in {"weak", "missing"}:
        return make_score("D")

    if communication.coherence_quality == "missing":
        return make_score("D")

    if communication.email_structure_quality == "missing":
        return make_score("D")

    if communication.vocabulary_level == "A2":
        return make_score("D")

    qualities = _communication_quality_values(communication)
    excellent_or_good = {"excellent", "good"}
    excellent_count = sum(1 for q in qualities if q == "excellent")

    if all(q in excellent_or_good for q in qualities):
        if excellent_count >= 3 and communication.vocabulary_level == "B2":
            return make_score("A")
        if (
            excellent_count < 3
            and communication.vocabulary_level in {"B2", "B1+"}
        ):
            return make_score("B")

    if any(q in {"acceptable", "weak"} for q in qualities) or communication.vocabulary_level == "B1":
        return make_score("C")

    return make_score("D")


def score_criterion_iii(
    relevance: RelevanceCheckResult,
    accuracy: AccuracyCheckResult,
) -> CriterionScore:
    """Score Criterion III (formal accuracy) using aspect_ratings and global flags."""
    if relevance.topic_mismatch:
        return make_score("D")

    if accuracy.comprehension_affected:
        return make_score("D")

    ar = accuracy.aspect_ratings
    values = [getattr(ar, name) for name in ACCURACY_SCORING_ASPECTS]
    problematic_count = sum(1 for v in values if v == "problematic")
    weak_count = sum(1 for v in values if v == "weak")

    comprehension_rating = getattr(ar, "comprehension")
    if comprehension_rating == "problematic":
        return make_score("D")

    if problematic_count >= 2:
        return make_score("D")

    if any(getattr(ar, asp) == "problematic" for asp in ACCURACY_CORE_ASPECTS):
        return make_score("D")

    systematic_error_count = len(accuracy.systematic_errors)

    if (
        problematic_count == 0
        and weak_count == 0
        and ar.grammar == "strong"
        and ar.spelling == "strong"
        and ar.punctuation == "strong"
        and systematic_error_count <= 1
    ):
        return make_score("A")

    if (
        problematic_count == 0
        and weak_count <= 1
        and ar.grammar in {"strong", "adequate"}
        and ar.comprehension in {"strong", "adequate"}
        and systematic_error_count <= 3
    ):
        return make_score("B")

    return make_score("C")


def calculate_final_score(
    criterion_i: CriterionScore,
    criterion_ii: CriterionScore,
    criterion_iii: CriterionScore,
) -> FinalScore:
    """Calculate raw and scaled TELC final scores.

    Raises
    ------
    ValueError
        If any criterion has ``points is None`` (failed analysis); scores with
        missing points must not be aggregated.
    """
    pi, pii, piii = criterion_i.points, criterion_ii.points, criterion_iii.points
    if pi is None or pii is None or piii is None:
        missing = []
        if pi is None:
            missing.append("criterion_i")
        if pii is None:
            missing.append("criterion_ii")
        if piii is None:
            missing.append("criterion_iii")
        joined = ", ".join(missing)
        raise ValueError(
            "Final score calculation requires numeric points on all criteria; "
            f"these have points=None (failed analyses): {joined}"
        )
    raw_score = pi + pii + piii
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
    """Score all TELC writing criteria for fully successful analyses only."""
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
    from backend.evaluation.schemas import KeyPointDetail

    relevance = RelevanceCheckResult(
        topic_mismatch=False,
        situation_mismatch=False,
        explanation="The text matches the task and intended situation.",
        positive_feedback=["Passt zum Auftrag."],
        improvement_feedback=["Präzisierung möglich."],
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
        positive_feedback=["Inhalt klar."],
        improvement_feedback=["Mehr Ausführung möglich."],
        key_point_details=[
            KeyPointDetail(
                number=1,
                type="expected",
                key_point="Problem described",
                status="fulfilled",
                sentence_count=2,
                situation_appropriate=True,
                language_level="B2",
                comment="Erfüllt.",
            ),
            KeyPointDetail(
                number=2,
                type="expected",
                key_point="Consequences explained",
                status="fulfilled",
                sentence_count=2,
                situation_appropriate=True,
                language_level="B2",
                comment="Erfüllt.",
            ),
        ],
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
        positive_feedback=["Klar lesbar."],
        improvement_feedback=["Verben prüfen."],
        aspect_ratings={
            "grammar": "strong",
            "syntax": "strong",
            "word_order": "adequate",
            "verb_forms": "adequate",
            "agreement": "adequate",
            "spelling": "strong",
            "punctuation": "strong",
            "capitalization": "adequate",
            "comprehension": "strong",
        },
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

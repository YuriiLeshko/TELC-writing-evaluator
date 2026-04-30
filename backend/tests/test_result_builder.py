from __future__ import annotations

from backend.evaluation.result_builder import build_final_result
from backend.evaluation.schemas import (
    AccuracyCheckResult,
    CommunicationCheckResult,
    CriterionScore,
    FinalScore,
    GrammarErrorSpan,
    ImprovedTextResult,
    KeyPointCheckResult,
    RelevanceCheckResult,
    WordCountCheck,
)


def _inputs() -> tuple[
    RelevanceCheckResult,
    KeyPointCheckResult,
    CommunicationCheckResult,
    AccuracyCheckResult,
]:
    relevance = RelevanceCheckResult(
        topic_mismatch=False,
        situation_mismatch=False,
        explanation="Passt.",
        positive_feedback=["Thema passt."],
        improvement_feedback=["Situation klarer benennen."],
    )
    key_points = KeyPointCheckResult(
        fulfilled_key_points=["P1", "P2"],
        own_ideas=["Eigene Idee"],
        invalid_points=[],
        explanation="Zwei Leitpunkte.",
        positive_feedback=["Leitpunkte gut umgesetzt."],
        improvement_feedback=["Mehr Details nennen."],
    )
    communication = CommunicationCheckResult(
        has_subject=True,
        has_greeting=True,
        has_introduction=True,
        has_body_structure=True,
        has_conclusion=True,
        has_closing=True,
        register_quality="appropriate",
        coherence_quality="good",
        vocabulary_level="B2",
        sentence_variety="some_variety",
        explanation="Strukturiert.",
        positive_feedback=["Gute Struktur."],
        improvement_feedback=["Mehr Konnektoren verwenden."],
    )
    accuracy = AccuracyCheckResult(
        grammar_control="good",
        systematic_errors=["Kasusfehler"],
        spelling_quality="acceptable",
        punctuation_quality="acceptable",
        comprehension_affected=False,
        explanation="Verstaendlich.",
        positive_feedback=["Verstaendlich formuliert."],
        improvement_feedback=["Kasus genauer beachten."],
        highlighted_errors=[
            GrammarErrorSpan(
                text="ein Kopfhörer",
                correction="einen Kopfhörer",
                error_type="Kasusfehler",
                explanation="Akkusativ erforderlich.",
            )
        ],
    )
    return relevance, key_points, communication, accuracy


def test_build_final_result_normal_case() -> None:
    relevance, key_points, communication, accuracy = _inputs()
    result = build_final_result(
        relevance=relevance,
        key_points=key_points,
        communication=communication,
        accuracy=accuracy,
        criterion_i=CriterionScore(grade="B", points=3),
        criterion_ii=CriterionScore(grade="B", points=3),
        criterion_iii=CriterionScore(grade="B", points=3),
        final_score=FinalScore(raw_score=9, final_score=27, max_score=45),
        word_count=WordCountCheck(value=160, minimum_required=150, meets_requirement=True),
        improved_text=ImprovedTextResult(improved_text="Verbessert", changes_summary=["Satzbau"]),
    )
    dumped = result.model_dump(mode="json")
    assert "comment" in dumped["criterion_I"]
    assert dumped["criterion_III"]["highlighted_errors"][0]["error_type"] == "Kasusfehler"
    assert "explanations" not in dumped
    assert dumped["word_count"]["value"] == 160


def test_build_final_result_low_word_count_note() -> None:
    relevance, key_points, communication, accuracy = _inputs()
    result = build_final_result(
        relevance=relevance,
        key_points=key_points,
        communication=communication,
        accuracy=accuracy,
        criterion_i=CriterionScore(grade="D", points=0),
        criterion_ii=CriterionScore(grade="D", points=0),
        criterion_iii=CriterionScore(grade="D", points=0),
        final_score=FinalScore(raw_score=0, final_score=0, max_score=45),
        word_count=WordCountCheck(value=120, minimum_required=150, meets_requirement=False),
        improved_text=ImprovedTextResult(improved_text="Verbessert", changes_summary=["Erweitert"]),
    )
    assert result.word_count is not None
    assert result.word_count.meets_requirement is False
    assert "unter 150 Wörtern" in (result.criterion_I.comment or "")


def test_build_final_result_topic_mismatch_serializes() -> None:
    relevance, key_points, communication, accuracy = _inputs()
    relevance.topic_mismatch = True
    result = build_final_result(
        relevance=relevance,
        key_points=key_points,
        communication=communication,
        accuracy=accuracy,
        criterion_i=CriterionScore(grade="D", points=0),
        criterion_ii=CriterionScore(grade="D", points=0),
        criterion_iii=CriterionScore(grade="D", points=0),
        final_score=FinalScore(raw_score=0, final_score=0, max_score=45),
        improved_text=ImprovedTextResult(improved_text="Text", changes_summary=["Korrigiert"]),
    )
    dumped = result.model_dump(mode="json")
    assert dumped["topic_mismatch"] is True
    assert dumped["final_score"] == 0

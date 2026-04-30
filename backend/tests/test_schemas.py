from __future__ import annotations

import pytest
from pydantic import ValidationError

from backend.evaluation.schemas import (
    CriterionScore,
    GrammarErrorSpan,
    ImprovedTextResult,
    WordCountCheck,
    WritingEvaluationInput,
    WritingEvaluationResult,
)


def test_writing_evaluation_input_validates() -> None:
    obj = WritingEvaluationInput(
        task_text="Task",
        expected_key_points=["Punkt 1", "Punkt 2"],
        candidate_text="Antwort",
    )
    assert obj.task_text == "Task"


def test_writing_evaluation_input_forbids_extra_fields() -> None:
    with pytest.raises(ValidationError):
        WritingEvaluationInput(
            task_text="Task",
            expected_key_points=["Punkt 1"],
            candidate_text="Antwort",
            extra="forbidden",
        )


def test_criterion_score_grade_points_mapping() -> None:
    assert CriterionScore(grade="A", points=5).points == 5
    with pytest.raises(ValidationError):
        CriterionScore(grade="B", points=5)


def test_word_count_check_validation() -> None:
    wc = WordCountCheck(value=160, minimum_required=150, meets_requirement=True)
    assert wc.meets_requirement is True


def test_improved_text_result_validation() -> None:
    improved = ImprovedTextResult(improved_text="Verbesserter Text", changes_summary=["Klarer strukturiert"])
    assert improved.improved_text.startswith("Verbesserter")


def test_grammar_error_span_validation() -> None:
    span = GrammarErrorSpan(
        text="ein Kopfhörer",
        correction="einen Kopfhörer",
        error_type="Kasusfehler",
        explanation="Akkusativ nach Verb.",
    )
    assert span.error_type == "Kasusfehler"


def test_writing_evaluation_result_serialization() -> None:
    criterion_iii = CriterionScore(
        grade="C",
        points=1,
        comment="Kommentar",
        highlighted_errors=[
            GrammarErrorSpan(
                text="ein Kopfhörer",
                correction="einen Kopfhörer",
                error_type="Kasusfehler",
                explanation="Akkusativ nach Verb.",
            )
        ],
    )
    result = WritingEvaluationResult(
        topic_mismatch=False,
        situation_mismatch=False,
        criterion_I=CriterionScore(grade="A", points=5, comment="Gut"),
        criterion_II=CriterionScore(grade="B", points=3, comment="Solide"),
        criterion_III=criterion_iii,
        word_count=WordCountCheck(value=170, minimum_required=150, meets_requirement=True),
        improved_text=ImprovedTextResult(improved_text="Text", changes_summary=["Verbessert"]),
        raw_score=9,
        final_score=27,
        max_score=45,
    )
    dumped = result.model_dump(mode="json")
    assert dumped["criterion_III"]["highlighted_errors"][0]["error_type"] == "Kasusfehler"
    assert dumped["criterion_I"]["comment"] == "Gut"

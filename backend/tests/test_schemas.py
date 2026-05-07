from __future__ import annotations

import pytest
from pydantic import ValidationError

from backend.evaluation.schemas import (
    AccuracyCheckResult,
    AccuracyAspectRatings,
    CommunicationIndicator,
    CommunicationCheckResult,
    CriterionScore,
    GrammarErrorSpan,
    ImprovedTextResult,
    KeyPointCheckResult,
    KeyPointDetail,
    TaskAchievementSummary,
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


def test_grammar_error_span_rejects_aspect_field() -> None:
    with pytest.raises(ValidationError):
        GrammarErrorSpan(
            text="ein Kopfhörer",
            correction="einen Kopfhörer",
            error_type="Kasusfehler",
            explanation="Akkusativ nach Verb.",
            aspect="word_order",
        )


def test_key_point_detail_validation() -> None:
    detail = KeyPointDetail(
        number=1,
        type="expected",
        key_point="Problem beschreiben",
        status="fulfilled",
        sentence_count=2,
        situation_appropriate=True,
        language_level="B2",
        comment="Der Leitpunkt wird klar und passend ausgearbeitet.",
    )
    assert detail.status == "fulfilled"


def test_key_point_check_result_accepts_key_point_details() -> None:
    result = KeyPointCheckResult(
        fulfilled_key_points=["Problem beschreiben"],
        own_ideas=[],
        invalid_points=[],
        explanation="Leitpunkte teilweise erfüllt.",
        key_point_details=[
            KeyPointDetail(
                number=1,
                type="expected",
                key_point="Problem beschreiben",
                status="fulfilled",
                sentence_count=2,
                situation_appropriate=True,
                language_level="B1+",
                comment="Der Punkt ist vorhanden und ausreichend entwickelt.",
            )
        ],
    )
    assert len(result.key_point_details) == 1


def test_communication_indicator_validation() -> None:
    detail = CommunicationIndicator(
        aspect="register",
        label="Register und Stil",
        rating="acceptable",
        comment="Das Register ist überwiegend passend, aber nicht durchgehend stabil.",
    )
    assert detail.aspect == "register"


def test_communication_check_result_uses_new_fields() -> None:
    result = CommunicationCheckResult(
        email_structure_quality="good",
        coherence_quality="acceptable",
        cohesion_quality="good",
        register_quality="good",
        vocabulary_level="B1+",
        sentence_variety_quality="acceptable",
        explanation="Die kommunikative Gestaltung ist insgesamt verständlich.",
        communication_indicators=[],
    )
    assert result.email_structure_quality == "good"


def test_communication_check_result_rejects_old_boolean_fields() -> None:
    with pytest.raises(ValidationError):
        CommunicationCheckResult(
            has_subject=True,
            coherence_quality="good",
            cohesion_quality="good",
            register_quality="good",
            vocabulary_level="B2",
            sentence_variety_quality="good",
            explanation="Test",
        )


def test_accuracy_aspect_ratings_validation() -> None:
    ratings = AccuracyAspectRatings(
        grammar="adequate",
        syntax="strong",
        word_order="strong",
        verb_forms="strong",
        agreement="adequate",
        spelling="strong",
        punctuation="strong",
        capitalization="adequate",
        comprehension="strong",
    )
    assert ratings.grammar == "adequate"


def test_accuracy_aspect_ratings_forbids_extra_fields() -> None:
    with pytest.raises(ValidationError):
        AccuracyAspectRatings(
            grammar="adequate",
            syntax="strong",
            word_order="strong",
            verb_forms="strong",
            agreement="adequate",
            spelling="strong",
            punctuation="strong",
            capitalization="adequate",
            comprehension="strong",
            extra_field="forbidden",
        )


def test_accuracy_check_result_accepts_aspect_ratings() -> None:
    result = AccuracyCheckResult(
        grammar_control="good",
        systematic_errors=["Wortstellung"],
        spelling_quality="acceptable",
        punctuation_quality="acceptable",
        comprehension_affected=False,
        explanation="Insgesamt verständlich.",
        aspect_ratings=AccuracyAspectRatings(
            grammar="adequate",
            syntax="strong",
            word_order="weak",
            verb_forms="strong",
            agreement="adequate",
            spelling="adequate",
            punctuation="adequate",
            capitalization="adequate",
            comprehension="strong",
        ),
        highlighted_errors=[
            GrammarErrorSpan(
                text="ein Kopfhörer",
                correction="einen Kopfhörer",
                error_type="Kasusfehler",
                explanation="Akkusativ nach Verb.",
            )
        ],
    )
    assert result.aspect_ratings.word_order == "weak"


def test_accuracy_check_result_rejects_accuracy_details_field() -> None:
    with pytest.raises(ValidationError):
        AccuracyCheckResult(
            grammar_control="good",
            systematic_errors=[],
            spelling_quality="acceptable",
            punctuation_quality="acceptable",
            comprehension_affected=False,
            explanation="Insgesamt verständlich.",
            aspect_ratings=AccuracyAspectRatings(
                grammar="adequate",
                syntax="strong",
                word_order="weak",
                verb_forms="strong",
                agreement="adequate",
                spelling="adequate",
                punctuation="adequate",
                capitalization="adequate",
                comprehension="strong",
            ),
            accuracy_details=[],
            highlighted_errors=[],
        )


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
        criterion_I=CriterionScore(
            grade="A",
            points=5,
            comment="Gut",
            scaled_points=15,
            max_scaled_points=15,
            key_point_details=[
                KeyPointDetail(
                    number=1,
                    type="expected",
                    key_point="Problem beschreiben",
                    status="fulfilled",
                    sentence_count=3,
                    situation_appropriate=True,
                    language_level="B2",
                    comment="Sehr präzise und ausführlich dargestellt.",
                )
            ],
            task_achievement_summary=TaskAchievementSummary(
                fulfilled_count=1,
                partially_fulfilled_count=0,
                not_fulfilled_count=0,
                own_idea_count=0,
                overall_level="B2",
                summary_comment="1 erfüllt, 0 teilweise erfüllt, 0 nicht erfüllt.",
            ),
        ),
        criterion_II=CriterionScore(
            grade="B",
            points=3,
            comment="Solide",
            scaled_points=9,
            max_scaled_points=15,
            analysis_status="success",
            analysis_error=None,
            communication_indicators=[
                CommunicationIndicator(
                    aspect="structure",
                    label="Struktur",
                    rating="excellent",
                    comment="Die Makrostruktur ist klar und nachvollziehbar.",
                )
            ],
        ),
        criterion_III=CriterionScore(
            grade="C",
            points=1,
            comment="Kommentar",
            scaled_points=3,
            max_scaled_points=15,
            highlighted_errors=criterion_iii.highlighted_errors,
        ),
        word_count=WordCountCheck(value=170, minimum_required=150, meets_requirement=True),
        improved_text=ImprovedTextResult(improved_text="Text", changes_summary=["Verbessert"]),
        raw_score=9,
        final_score=27,
        max_score=45,
    )
    dumped = result.model_dump(mode="json")
    assert dumped["criterion_III"]["highlighted_errors"][0]["error_type"] == "Kasusfehler"
    assert dumped["criterion_I"]["comment"] == "Gut"
    assert dumped["criterion_I"]["scaled_points"] == 15
    assert dumped["criterion_I"]["max_scaled_points"] == 15
    assert dumped["criterion_I"]["key_point_details"][0]["status"] == "fulfilled"
    assert dumped["criterion_II"]["scaled_points"] == 9
    assert dumped["criterion_II"]["max_scaled_points"] == 15
    assert dumped["criterion_II"]["analysis_status"] == "success"
    assert dumped["criterion_II"]["communication_indicators"][0]["aspect"] == "structure"
    assert dumped["criterion_III"]["scaled_points"] == 3
    assert dumped["criterion_III"]["max_scaled_points"] == 15
    assert "accuracy_details" not in dumped["criterion_III"]
    assert "aspect" not in dumped["criterion_III"]["highlighted_errors"][0]

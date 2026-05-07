from __future__ import annotations

from backend.evaluation.result_builder import (
    _build_criterion_iii_comment,
    build_final_result,
)
from backend.evaluation.schemas import (
    AccuracyCheckResult,
    CommunicationIndicator,
    CommunicationCheckResult,
    CriterionScore,
    FinalScore,
    GrammarErrorSpan,
    ImprovedTextResult,
    KeyPointCheckResult,
    KeyPointDetail,
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
        key_point_details=[
            KeyPointDetail(
                number=1,
                type="expected",
                key_point="P1",
                status="fulfilled",
                sentence_count=2,
                situation_appropriate=True,
                language_level="B2",
                comment="P1 wird klar und detailliert erläutert.",
            ),
            KeyPointDetail(
                number=2,
                type="expected",
                key_point="P2",
                status="fulfilled",
                sentence_count=2,
                situation_appropriate=True,
                language_level="B1+",
                comment="P2 ist vorhanden und ausreichend entwickelt.",
            ),
        ],
    )
    communication = CommunicationCheckResult(
        email_structure_quality="good",
        coherence_quality="good",
        cohesion_quality="acceptable",
        register_quality="good",
        vocabulary_level="B2",
        sentence_variety_quality="acceptable",
        explanation="Strukturiert.",
        communication_indicators=[
            CommunicationIndicator(
                aspect="structure",
                label="Struktur",
                rating="excellent",
                comment="Die Struktur ist klar und logisch aufgebaut.",
            ),
            CommunicationIndicator(
                aspect="sentence_variety",
                label="Satzvielfalt",
                rating="acceptable",
                comment="Es gibt etwas Variation, aber noch Wiederholungen.",
            ),
        ],
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
        aspect_ratings={
            "grammar": "adequate",
            "syntax": "strong",
            "word_order": "adequate",
            "verb_forms": "adequate",
            "agreement": "adequate",
            "spelling": "adequate",
            "punctuation": "adequate",
            "capitalization": "adequate",
            "comprehension": "strong",
        },
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
    assert dumped["criterion_I"]["scaled_points"] == 9
    assert dumped["criterion_I"]["max_scaled_points"] == 15
    assert len(dumped["criterion_I"]["key_point_details"]) == 2
    assert dumped["criterion_I"]["task_achievement_summary"]["fulfilled_count"] == 2
    assert dumped["criterion_I"]["task_achievement_summary"]["own_idea_count"] == 1
    assert dumped["criterion_II"]["scaled_points"] == 9
    assert dumped["criterion_II"]["max_scaled_points"] == 15
    assert dumped["criterion_I"]["analysis_status"] == "success"
    assert dumped["criterion_I"]["analysis_error"] is None
    assert dumped["criterion_II"]["analysis_status"] == "success"
    assert dumped["criterion_II"]["analysis_error"] is None
    assert len(dumped["criterion_II"]["communication_indicators"]) == 2
    assert dumped["criterion_III"]["scaled_points"] == 9
    assert dumped["criterion_III"]["max_scaled_points"] == 15
    assert dumped["criterion_III"]["analysis_status"] == "success"
    assert dumped["criterion_III"]["analysis_error"] is None
    assert "accuracy_details" not in dumped["criterion_III"]
    assert "aspect_ratings" not in dumped["criterion_III"]
    assert dumped["criterion_III"]["highlighted_errors"][0]["error_type"] == "Kasusfehler"
    assert "aspect" not in dumped["criterion_III"]["highlighted_errors"][0]
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


def test_build_final_result_final_score_none() -> None:
    relevance, key_points, communication, accuracy = _inputs()
    result = build_final_result(
        relevance=relevance,
        key_points=key_points,
        communication=communication,
        accuracy=accuracy,
        criterion_i=CriterionScore(grade="B", points=3),
        criterion_ii=CriterionScore(grade="B", points=3),
        criterion_iii=CriterionScore(grade="B", points=3),
        final_score=None,
        improved_text=ImprovedTextResult(improved_text="Verbessert", changes_summary=["OK"]),
        overall_analysis_status="partial",
        overall_analysis_error="Teilanalyse fehlgeschlagen.",
    )
    assert result.raw_score is None
    assert result.final_score is None
    assert result.max_score == 45
    assert result.analysis_status == "partial"
    assert result.analysis_error == "Teilanalyse fehlgeschlagen."


def test_build_final_result_failed_criterion_unchanged_scores() -> None:
    err = "Technische Analyse für Kriterium I fehlgeschlagen."
    failed_i = CriterionScore(
        grade=None,
        points=None,
        analysis_status="failed",
        analysis_error=err,
    )
    result = build_final_result(
        relevance=None,
        key_points=None,
        communication=None,
        accuracy=None,
        criterion_i=failed_i,
        criterion_ii=CriterionScore(
            grade=None,
            points=None,
            analysis_status="failed",
            analysis_error="II fehlgeschlagen.",
        ),
        criterion_iii=CriterionScore(
            grade=None,
            points=None,
            analysis_status="failed",
            analysis_error="III fehlgeschlagen.",
        ),
        final_score=None,
        improved_text=ImprovedTextResult(improved_text="x", changes_summary=["y"]),
        overall_analysis_status="failed",
    )
    assert result.criterion_I.grade is None
    assert result.criterion_I.points is None
    assert result.criterion_I.comment is None
    assert result.topic_mismatch is False
    assert result.situation_mismatch is False


def test_build_criterion_iii_comment_fallback_is_formal_accuracy() -> None:
    acc = AccuracyCheckResult(
        grammar_control="strong",
        systematic_errors=[],
        spelling_quality="good",
        punctuation_quality="good",
        comprehension_affected=False,
        explanation="Kurz.",
        positive_feedback=[],
        improvement_feedback=[],
        example_errors=[],
        aspect_ratings={
            "grammar": "strong",
            "syntax": "strong",
            "word_order": "strong",
            "verb_forms": "strong",
            "agreement": "strong",
            "spelling": "strong",
            "punctuation": "strong",
            "capitalization": "strong",
            "comprehension": "strong",
        },
        highlighted_errors=[],
    )
    text = _build_criterion_iii_comment(acc)
    assert "wiederkehrende formale Fehler" in text
    assert "syntaktische Vielfalt" not in text


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

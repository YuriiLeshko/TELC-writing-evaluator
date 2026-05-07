from __future__ import annotations

import pytest

from backend.evaluation import pipeline
from backend.evaluation.schemas import (
    AccuracyCheckResult,
    CommunicationIndicator,
    CommunicationCheckResult,
    ImprovedTextResult,
    KeyPointCheckResult,
    KeyPointDetail,
    RelevanceCheckResult,
    WritingEvaluationInput,
)


@pytest.fixture
def input_data() -> WritingEvaluationInput:
    return WritingEvaluationInput(
        task_text="Task text",
        expected_key_points=["P1", "P2", "P3"],
        candidate_text="Dies ist ein ausreichend langer Beispieltext " * 15,
    )


@pytest.mark.asyncio
async def test_pipeline_normal_flow(monkeypatch: pytest.MonkeyPatch, input_data: WritingEvaluationInput) -> None:
    calls: list[str] = []

    async def fake_relevance(*args, **kwargs):
        calls.append("relevance")
        return RelevanceCheckResult(
            topic_mismatch=False,
            situation_mismatch=False,
            explanation="Ok",
            positive_feedback=["Passt."],
            improvement_feedback=["Kleiner Hinweis."],
        )

    async def fake_key(*args, **kwargs):
        calls.append("key")
        return KeyPointCheckResult(
            fulfilled_key_points=["P1", "P2"],
            own_ideas=["Idee"],
            invalid_points=[],
            explanation="Ok",
            key_point_details=[
                KeyPointDetail(
                    number=1,
                    type="expected",
                    key_point="P1",
                    status="fulfilled",
                    sentence_count=2,
                    situation_appropriate=True,
                    language_level="B2",
                    comment="P1 ist klar entwickelt.",
                ),
                KeyPointDetail(
                    number=2,
                    type="expected",
                    key_point="P2",
                    status="fulfilled",
                    sentence_count=2,
                    situation_appropriate=True,
                    language_level="B1+",
                    comment="P2 ist ausreichend vorhanden.",
                ),
                KeyPointDetail(
                    number=3,
                    type="expected",
                    key_point="P3",
                    status="not_fulfilled",
                    sentence_count=0,
                    situation_appropriate=False,
                    language_level=None,
                    comment="P3 fehlt.",
                ),
            ],
        )

    async def fake_comm(*args, **kwargs):
        calls.append("comm")
        return CommunicationCheckResult(
            email_structure_quality="good",
            coherence_quality="good",
            cohesion_quality="acceptable",
            register_quality="good",
            vocabulary_level="B2",
            sentence_variety_quality="acceptable",
            explanation="Ok",
            communication_indicators=[
                CommunicationIndicator(
                    aspect="coherence",
                    label="Zusammenhang",
                    rating="acceptable",
                    comment="Der Zusammenhang ist erkennbar, aber ausbaufähig.",
                )
            ],
        )

    async def fake_acc(*args, **kwargs):
        calls.append("acc")
        return AccuracyCheckResult(
            grammar_control="good",
            systematic_errors=[],
            spelling_quality="good",
            punctuation_quality="good",
            comprehension_affected=False,
            explanation="Ok",
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

    async def fake_improved(*args, **kwargs):
        calls.append("improved")
        return ImprovedTextResult(improved_text="Verbessert", changes_summary=["Satzbau"])

    monkeypatch.setattr(pipeline, "check_relevance", fake_relevance)
    monkeypatch.setattr(pipeline, "check_key_points", fake_key)
    monkeypatch.setattr(pipeline, "check_communication", fake_comm)
    monkeypatch.setattr(pipeline, "check_accuracy", fake_acc)
    monkeypatch.setattr(pipeline, "generate_improved_text", fake_improved)

    result = await pipeline.evaluate_writing(input_data=input_data, llm_client=object())
    assert result.final_score >= 0
    assert result.improved_text.improved_text == "Verbessert"
    assert result.criterion_I.scaled_points == result.criterion_I.points * 3
    assert result.criterion_I.max_scaled_points == 15
    assert result.criterion_I.key_point_details is not None
    assert len(result.criterion_I.key_point_details) == 3
    assert result.criterion_II.scaled_points == result.criterion_II.points * 3
    assert result.criterion_II.max_scaled_points == 15
    assert result.criterion_II.analysis_status == "success"
    assert result.criterion_II.communication_indicators is not None
    assert len(result.criterion_II.communication_indicators) == 1
    assert result.criterion_III.scaled_points == result.criterion_III.points * 3
    assert result.criterion_III.max_scaled_points == 15
    assert result.criterion_III.highlighted_errors is not None
    assert len(result.criterion_III.highlighted_errors) == 0
    assert calls[0] == "relevance"
    assert "improved" in calls


@pytest.mark.asyncio
async def test_pipeline_topic_mismatch_short_circuit(monkeypatch: pytest.MonkeyPatch, input_data: WritingEvaluationInput) -> None:
    calls: list[str] = []

    async def fake_relevance(*args, **kwargs):
        calls.append("relevance")
        return RelevanceCheckResult(
            topic_mismatch=True,
            situation_mismatch=True,
            explanation="Thema verfehlt",
            positive_feedback=["Thema verfehlt."],
            improvement_feedback=["Aufgabenbezug herstellen."],
        )

    async def fake_fail(*args, **kwargs):
        calls.append("unexpected")
        raise AssertionError("Should not be called")

    async def fake_improved(*args, **kwargs):
        calls.append("improved")
        return ImprovedTextResult(improved_text="Verbessert", changes_summary=["Hinweis"])

    monkeypatch.setattr(pipeline, "check_relevance", fake_relevance)
    monkeypatch.setattr(pipeline, "check_key_points", fake_fail)
    monkeypatch.setattr(pipeline, "check_communication", fake_fail)
    monkeypatch.setattr(pipeline, "check_accuracy", fake_fail)
    monkeypatch.setattr(pipeline, "generate_improved_text", fake_improved)

    result = await pipeline.evaluate_writing(input_data=input_data, llm_client=object())
    assert result.criterion_I.grade == "D"
    assert result.criterion_II.grade == "D"
    assert result.criterion_III.grade == "D"
    assert calls == ["relevance"]


@pytest.mark.asyncio
async def test_pipeline_low_word_count_override(monkeypatch: pytest.MonkeyPatch) -> None:
    short_input = WritingEvaluationInput(
        task_text="Task text",
        expected_key_points=["P1", "P2", "P3"],
        candidate_text="Kurz text",
    )

    async def fake_relevance(*args, **kwargs):
        return RelevanceCheckResult(
            topic_mismatch=False,
            situation_mismatch=False,
            explanation="Ok",
            positive_feedback=["Passt."],
            improvement_feedback=["Kleiner Hinweis."],
        )

    async def fake_key(*args, **kwargs):
        return KeyPointCheckResult(
            fulfilled_key_points=["P1", "P2", "P3"],
            own_ideas=[],
            invalid_points=[],
            explanation="Ok",
            key_point_details=[
                KeyPointDetail(
                    number=1,
                    type="expected",
                    key_point="P1",
                    status="fulfilled",
                    sentence_count=2,
                    situation_appropriate=True,
                    language_level="B2",
                    comment="P1 vorhanden.",
                ),
                KeyPointDetail(
                    number=2,
                    type="expected",
                    key_point="P2",
                    status="fulfilled",
                    sentence_count=2,
                    situation_appropriate=True,
                    language_level="B2",
                    comment="P2 vorhanden.",
                ),
                KeyPointDetail(
                    number=3,
                    type="expected",
                    key_point="P3",
                    status="fulfilled",
                    sentence_count=2,
                    situation_appropriate=True,
                    language_level="B2",
                    comment="P3 vorhanden.",
                ),
            ],
        )

    async def fake_comm(*args, **kwargs):
        return CommunicationCheckResult(
            email_structure_quality="excellent",
            coherence_quality="excellent",
            cohesion_quality="excellent",
            register_quality="excellent",
            vocabulary_level="B2",
            sentence_variety_quality="excellent",
            explanation="Ok",
            communication_indicators=[
                CommunicationIndicator(
                    aspect="register",
                    label="Register und Stil",
                    rating="excellent",
                    comment="Das Register ist situativ passend.",
                )
            ],
        )

    async def fake_acc(*args, **kwargs):
        return AccuracyCheckResult(
            grammar_control="strong",
            systematic_errors=[],
            spelling_quality="good",
            punctuation_quality="good",
            comprehension_affected=False,
            explanation="Ok",
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

    async def fake_improved(*args, **kwargs):
        return ImprovedTextResult(improved_text="Verbessert", changes_summary=["Hinweis"])

    monkeypatch.setattr(pipeline, "check_relevance", fake_relevance)
    monkeypatch.setattr(pipeline, "check_key_points", fake_key)
    monkeypatch.setattr(pipeline, "check_communication", fake_comm)
    monkeypatch.setattr(pipeline, "check_accuracy", fake_acc)
    monkeypatch.setattr(pipeline, "generate_improved_text", fake_improved)

    result = await pipeline.evaluate_writing(input_data=short_input, llm_client=object())
    assert result.criterion_I.grade == "D"
    assert result.criterion_II.grade == "D"
    assert result.criterion_III.grade == "D"
    assert result.final_score == 0


@pytest.mark.asyncio
async def test_pipeline_communication_fallback_not_forced_to_d(
    monkeypatch: pytest.MonkeyPatch, input_data: WritingEvaluationInput
) -> None:
    long_input_data = WritingEvaluationInput(
        task_text=input_data.task_text,
        expected_key_points=input_data.expected_key_points,
        candidate_text="Dies ist ein ausreichend langer Beispieltext " * 30,
    )

    async def fake_relevance(*args, **kwargs):
        return RelevanceCheckResult(
            topic_mismatch=False,
            situation_mismatch=False,
            explanation="Ok",
            positive_feedback=["Passt."],
            improvement_feedback=["Kleiner Hinweis."],
        )

    async def fake_key(*args, **kwargs):
        return KeyPointCheckResult(
            fulfilled_key_points=["P1", "P2"],
            own_ideas=[],
            invalid_points=[],
            explanation="Ok",
        )

    async def fake_comm(*args, **kwargs):
        raise RuntimeError("LLM communication failed")

    async def fake_acc(*args, **kwargs):
        return AccuracyCheckResult(
            grammar_control="good",
            systematic_errors=[],
            spelling_quality="good",
            punctuation_quality="good",
            comprehension_affected=False,
            explanation="Ok",
            aspect_ratings={
                "grammar": "adequate",
                "syntax": "adequate",
                "word_order": "adequate",
                "verb_forms": "adequate",
                "agreement": "adequate",
                "spelling": "adequate",
                "punctuation": "adequate",
                "capitalization": "adequate",
                "comprehension": "adequate",
            },
        )

    async def fake_improved(*args, **kwargs):
        return ImprovedTextResult(improved_text="Verbessert", changes_summary=["Hinweis"])

    monkeypatch.setattr(pipeline, "check_relevance", fake_relevance)
    monkeypatch.setattr(pipeline, "check_key_points", fake_key)
    monkeypatch.setattr(pipeline, "check_communication", fake_comm)
    monkeypatch.setattr(pipeline, "check_accuracy", fake_acc)
    monkeypatch.setattr(pipeline, "generate_improved_text", fake_improved)

    result = await pipeline.evaluate_writing(input_data=long_input_data, llm_client=object())
    assert result.analysis_status == "partial"
    assert result.final_score is None
    assert result.criterion_II.grade is None
    assert result.criterion_II.points is None
    assert result.criterion_II.analysis_status == "failed"
    assert result.criterion_II.analysis_error is not None
    assert result.criterion_II.communication_indicators == []


@pytest.mark.asyncio
async def test_pipeline_retries_checker_then_succeeds(
    monkeypatch: pytest.MonkeyPatch, input_data: WritingEvaluationInput
) -> None:
    calls = {"key": 0}

    async def fake_relevance(*args, **kwargs):
        return RelevanceCheckResult(
            topic_mismatch=False,
            situation_mismatch=False,
            explanation="Ok",
            positive_feedback=["Passt."],
            improvement_feedback=["Kleiner Hinweis."],
        )

    async def flaky_key(*args, **kwargs):
        calls["key"] += 1
        if calls["key"] < 3:
            raise RuntimeError("temporary key failure")
        return KeyPointCheckResult(
            fulfilled_key_points=["P1", "P2"],
            own_ideas=[],
            invalid_points=[],
            explanation="Ok",
        )

    async def fake_comm(*args, **kwargs):
        return CommunicationCheckResult(
            email_structure_quality="good",
            coherence_quality="good",
            cohesion_quality="good",
            register_quality="good",
            vocabulary_level="B2",
            sentence_variety_quality="good",
            explanation="Ok",
        )

    async def fake_acc(*args, **kwargs):
        return AccuracyCheckResult(
            grammar_control="good",
            systematic_errors=[],
            spelling_quality="good",
            punctuation_quality="good",
            comprehension_affected=False,
            explanation="Ok",
            aspect_ratings={
                "grammar": "adequate",
                "syntax": "adequate",
                "word_order": "adequate",
                "verb_forms": "adequate",
                "agreement": "adequate",
                "spelling": "adequate",
                "punctuation": "adequate",
                "capitalization": "adequate",
                "comprehension": "adequate",
            },
        )

    async def fake_improved(*args, **kwargs):
        return ImprovedTextResult(improved_text="Verbessert", changes_summary=["Hinweis"])

    monkeypatch.setattr(pipeline, "check_relevance", fake_relevance)
    monkeypatch.setattr(pipeline, "check_key_points", flaky_key)
    monkeypatch.setattr(pipeline, "check_communication", fake_comm)
    monkeypatch.setattr(pipeline, "check_accuracy", fake_acc)
    monkeypatch.setattr(pipeline, "generate_improved_text", fake_improved)

    result = await pipeline.evaluate_writing(input_data=input_data, llm_client=object())
    assert calls["key"] == 3
    assert result.analysis_status == "success"
    assert result.criterion_I.grade is not None
    assert result.final_score is not None


@pytest.mark.asyncio
async def test_pipeline_failed_checker_marks_criterion_failed_not_d(
    monkeypatch: pytest.MonkeyPatch, input_data: WritingEvaluationInput
) -> None:
    async def fake_relevance(*args, **kwargs):
        return RelevanceCheckResult(
            topic_mismatch=False,
            situation_mismatch=False,
            explanation="Ok",
            positive_feedback=["Passt."],
            improvement_feedback=["Kleiner Hinweis."],
        )

    async def failing_key(*args, **kwargs):
        raise RuntimeError("key checker hard failure")

    async def fake_comm(*args, **kwargs):
        return CommunicationCheckResult(
            email_structure_quality="good",
            coherence_quality="good",
            cohesion_quality="good",
            register_quality="good",
            vocabulary_level="B2",
            sentence_variety_quality="good",
            explanation="Ok",
        )

    async def fake_acc(*args, **kwargs):
        return AccuracyCheckResult(
            grammar_control="good",
            systematic_errors=[],
            spelling_quality="good",
            punctuation_quality="good",
            comprehension_affected=False,
            explanation="Ok",
            aspect_ratings={
                "grammar": "adequate",
                "syntax": "adequate",
                "word_order": "adequate",
                "verb_forms": "adequate",
                "agreement": "adequate",
                "spelling": "adequate",
                "punctuation": "adequate",
                "capitalization": "adequate",
                "comprehension": "adequate",
            },
        )

    async def fake_improved(*args, **kwargs):
        return ImprovedTextResult(improved_text="Verbessert", changes_summary=["Hinweis"])

    monkeypatch.setattr(pipeline, "check_relevance", fake_relevance)
    monkeypatch.setattr(pipeline, "check_key_points", failing_key)
    monkeypatch.setattr(pipeline, "check_communication", fake_comm)
    monkeypatch.setattr(pipeline, "check_accuracy", fake_acc)
    monkeypatch.setattr(pipeline, "generate_improved_text", fake_improved)

    result = await pipeline.evaluate_writing(input_data=input_data, llm_client=object())
    assert result.analysis_status == "partial"
    assert result.criterion_I.analysis_status == "failed"
    assert result.criterion_I.grade is None
    assert result.criterion_I.points is None
    assert result.final_score is None


@pytest.mark.asyncio
async def test_pipeline_relevance_failure_aborts_without_fake_success(
    monkeypatch: pytest.MonkeyPatch, input_data: WritingEvaluationInput
) -> None:
    async def failing_relevance(*args, **kwargs):
        raise RuntimeError("relevance hard failure")

    monkeypatch.setattr(pipeline, "check_relevance", failing_relevance)

    result = await pipeline.evaluate_writing(input_data=input_data, llm_client=object())
    assert result.analysis_status == "failed"
    assert result.final_score is None
    assert result.criterion_I.analysis_status == "failed"
    assert result.criterion_II.analysis_status == "failed"
    assert result.criterion_III.analysis_status == "failed"

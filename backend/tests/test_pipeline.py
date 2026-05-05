from __future__ import annotations

import pytest

from backend.evaluation import pipeline
from backend.evaluation.schemas import (
    AccuracyCheckResult,
    AccuracyDetail,
    CommunicationDetail,
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
        return RelevanceCheckResult(topic_mismatch=False, situation_mismatch=False, explanation="Ok")

    async def fake_key(*args, **kwargs):
        calls.append("key")
        return KeyPointCheckResult(
            fulfilled_key_points=["P1", "P2"],
            own_ideas=["Idee"],
            invalid_points=[],
            explanation="Ok",
            key_point_details=[
                KeyPointDetail(
                    key_point="P1",
                    covered=True,
                    status="fulfilled",
                    coverage_quality="strong",
                    sentence_count=2,
                    development="detailed",
                    relevance="direct",
                    situation_appropriate=True,
                    language_level="B2",
                    comment="P1 ist klar entwickelt.",
                ),
                KeyPointDetail(
                    key_point="P2",
                    covered=True,
                    status="fulfilled",
                    coverage_quality="adequate",
                    sentence_count=2,
                    development="sufficient",
                    relevance="direct",
                    situation_appropriate=True,
                    language_level="B1+",
                    comment="P2 ist ausreichend vorhanden.",
                ),
                KeyPointDetail(
                    key_point="P3",
                    covered=False,
                    status="not_fulfilled",
                    coverage_quality="missing",
                    sentence_count=0,
                    development="missing",
                    relevance="irrelevant",
                    situation_appropriate=False,
                    language_level=None,
                    comment="P3 fehlt.",
                ),
            ],
        )

    async def fake_comm(*args, **kwargs):
        calls.append("comm")
        return CommunicationCheckResult(
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
            explanation="Ok",
            communication_details=[
                CommunicationDetail(
                    aspect="coherence",
                    label="Gedanklicher Zusammenhang",
                    status="adequate",
                    level=None,
                    present_items=["logische Reihenfolge"],
                    missing_items=["klarere Übergänge"],
                    evidence=["Deshalb bin ich mit der Lieferung nicht zufrieden."],
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
            accuracy_details=[
                AccuracyDetail(
                    aspect="grammar",
                    label="Grammatik",
                    status="strong",
                    error_count=0,
                    evidence=[],
                    comment="Keine klaren Grammatikprobleme.",
                )
            ],
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
    assert result.criterion_II.communication_details is not None
    assert len(result.criterion_II.communication_details) == 1
    assert result.criterion_III.scaled_points == result.criterion_III.points * 3
    assert result.criterion_III.max_scaled_points == 15
    assert result.criterion_III.accuracy_details is not None
    assert len(result.criterion_III.accuracy_details) == 1
    assert calls[0] == "relevance"
    assert "improved" in calls


@pytest.mark.asyncio
async def test_pipeline_topic_mismatch_short_circuit(monkeypatch: pytest.MonkeyPatch, input_data: WritingEvaluationInput) -> None:
    calls: list[str] = []

    async def fake_relevance(*args, **kwargs):
        calls.append("relevance")
        return RelevanceCheckResult(topic_mismatch=True, situation_mismatch=True, explanation="Thema verfehlt")

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
    assert calls == ["relevance", "improved"]


@pytest.mark.asyncio
async def test_pipeline_low_word_count_override(monkeypatch: pytest.MonkeyPatch) -> None:
    short_input = WritingEvaluationInput(
        task_text="Task text",
        expected_key_points=["P1", "P2", "P3"],
        candidate_text="Kurz text",
    )

    async def fake_relevance(*args, **kwargs):
        return RelevanceCheckResult(topic_mismatch=False, situation_mismatch=False, explanation="Ok")

    async def fake_key(*args, **kwargs):
        return KeyPointCheckResult(
            fulfilled_key_points=["P1", "P2", "P3"],
            own_ideas=[],
            invalid_points=[],
            explanation="Ok",
            key_point_details=[
                KeyPointDetail(
                    key_point="P1",
                    covered=True,
                    status="fulfilled",
                    coverage_quality="strong",
                    sentence_count=2,
                    development="detailed",
                    relevance="direct",
                    situation_appropriate=True,
                    language_level="B2",
                    comment="P1 vorhanden.",
                ),
                KeyPointDetail(
                    key_point="P2",
                    covered=True,
                    status="fulfilled",
                    coverage_quality="strong",
                    sentence_count=2,
                    development="detailed",
                    relevance="direct",
                    situation_appropriate=True,
                    language_level="B2",
                    comment="P2 vorhanden.",
                ),
                KeyPointDetail(
                    key_point="P3",
                    covered=True,
                    status="fulfilled",
                    coverage_quality="strong",
                    sentence_count=2,
                    development="detailed",
                    relevance="direct",
                    situation_appropriate=True,
                    language_level="B2",
                    comment="P3 vorhanden.",
                ),
            ],
        )

    async def fake_comm(*args, **kwargs):
        return CommunicationCheckResult(
            has_subject=True,
            has_greeting=True,
            has_introduction=True,
            has_body_structure=True,
            has_conclusion=True,
            has_closing=True,
            register_quality="appropriate",
            coherence_quality="strong",
            vocabulary_level="B2",
            sentence_variety="varied",
            explanation="Ok",
            communication_details=[
                CommunicationDetail(
                    aspect="register",
                    label="Register und Stil",
                    status="strong",
                    level=None,
                    present_items=["formelle Anrede"],
                    missing_items=[],
                    evidence=["Sehr geehrte Damen und Herren"],
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
            accuracy_details=[
                AccuracyDetail(
                    aspect="comprehension",
                    label="Verständlichkeit",
                    status="strong",
                    error_count=0,
                    evidence=[],
                    comment="Trotz kurzer Länge verständlich.",
                )
            ],
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

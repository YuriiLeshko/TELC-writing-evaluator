from __future__ import annotations

import pytest
from pydantic import ValidationError

from backend.evaluation.checks.accuracy import check_accuracy
from backend.evaluation.checks.communication import check_communication
from backend.evaluation.checks.key_points import check_key_points
from backend.evaluation.checks.relevance import check_relevance
from backend.evaluation.schemas import (
    AccuracyCheckResult,
    CommunicationCheckResult,
    KeyPointCheckResult,
    RelevanceCheckResult,
    WritingEvaluationInput,
)
from backend.tests.conftest import FakeLLMClient


@pytest.fixture
def input_data() -> WritingEvaluationInput:
    return WritingEvaluationInput(
        task_text="Task text",
        expected_key_points=["P1", "P2"],
        candidate_text="Candidate text",
    )


@pytest.mark.asyncio
async def test_check_relevance_with_fake_llm(input_data: WritingEvaluationInput) -> None:
    client = FakeLLMClient(
        [
            {
                "topic_mismatch": False,
                "situation_mismatch": False,
                "explanation": "Passt.",
                "positive_feedback": ["Thema passt."],
                "improvement_feedback": ["Situation klarer benennen."],
            }
        ]
    )
    result = await check_relevance(client, input_data)
    assert isinstance(result, RelevanceCheckResult)
    assert len(client.calls) == 1
    assert client.calls[0]["temperature"] == 0.0


@pytest.mark.asyncio
async def test_check_key_points_with_fake_llm(input_data: WritingEvaluationInput) -> None:
    client = FakeLLMClient(
        [
            {
                "fulfilled_key_points": ["P1"],
                "own_ideas": ["Eigene Idee"],
                "invalid_points": [],
                "explanation": "Teilweise.",
                "positive_feedback": ["P1 enthalten."],
                "improvement_feedback": ["P2 fehlt."],
            }
        ]
    )
    result = await check_key_points(client, input_data)
    assert isinstance(result, KeyPointCheckResult)
    assert len(client.calls) == 1
    assert client.calls[0]["temperature"] == 0.0


@pytest.mark.asyncio
async def test_check_communication_with_fake_llm(input_data: WritingEvaluationInput) -> None:
    client = FakeLLMClient(
        [
            {
                "has_subject": True,
                "has_greeting": True,
                "has_introduction": True,
                "has_body_structure": True,
                "has_conclusion": True,
                "has_closing": True,
                "register_quality": "appropriate",
                "coherence_quality": "good",
                "vocabulary_level": "B2",
                "sentence_variety": "some_variety",
                "explanation": "Gut.",
                "positive_feedback": ["Struktur gut."],
                "improvement_feedback": ["Mehr Konnektoren."],
                "linking_devices": ["deshalb"],
                "complex_connectors": ["obwohl"],
                "language_level_comment": "Nahe B2.",
            }
        ]
    )
    result = await check_communication(client, input_data)
    assert isinstance(result, CommunicationCheckResult)
    assert len(client.calls) == 1
    assert client.calls[0]["temperature"] == 0.0


@pytest.mark.asyncio
async def test_check_accuracy_with_fake_llm(input_data: WritingEvaluationInput) -> None:
    client = FakeLLMClient(
        [
            {
                "grammar_control": "good",
                "systematic_errors": ["Kasus"],
                "spelling_quality": "acceptable",
                "punctuation_quality": "acceptable",
                "comprehension_affected": False,
                "explanation": "Verstaendlich.",
                "positive_feedback": ["Lesbar."],
                "improvement_feedback": ["Kasus pruefen."],
                "example_errors": ["ein Kopfhörer -> einen Kopfhörer"],
                "technical_notes": ["Einige Fehler."],
                "highlighted_errors": [
                    {
                        "text": "ein Kopfhörer",
                        "correction": "einen Kopfhörer",
                        "error_type": "Kasusfehler",
                        "explanation": "Akkusativ erforderlich.",
                    }
                ],
            }
        ]
    )
    result = await check_accuracy(client, input_data)
    assert isinstance(result, AccuracyCheckResult)
    assert result.highlighted_errors[0].error_type == "Kasusfehler"
    assert len(client.calls) == 1
    assert client.calls[0]["temperature"] == 0.0


@pytest.mark.asyncio
async def test_checker_invalid_response_raises_validation_error(input_data: WritingEvaluationInput) -> None:
    client = FakeLLMClient([{"topic_mismatch": False}])
    with pytest.raises(ValidationError):
        await check_relevance(client, input_data)

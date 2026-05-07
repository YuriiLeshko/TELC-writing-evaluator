from __future__ import annotations

import pytest
from pydantic import ValidationError

from backend.evaluation.checks.accuracy import check_accuracy
from backend.evaluation.checks.communication import CommunicationAnalysisFailed, check_communication
from backend.evaluation.checks.communication import _normalize_rating, _normalize_vocabulary_level
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
                "key_point_details": [
                    {
                        "number": 1,
                        "type": "expected",
                        "key_point": "P1",
                        "status": "fulfilled",
                        "sentence_count": 2,
                        "situation_appropriate": True,
                        "language_level": "B1+",
                        "comment": "P1 ist ausreichend ausgearbeitet.",
                    },
                    {
                        "number": 2,
                        "type": "expected",
                        "key_point": "P2",
                        "status": "not_fulfilled",
                        "sentence_count": 0,
                        "situation_appropriate": False,
                        "language_level": None,
                        "comment": "P2 fehlt im Text.",
                    },
                ],
            }
        ]
    )
    result = await check_key_points(client, input_data)
    assert isinstance(result, KeyPointCheckResult)
    assert len(result.key_point_details) == 3
    assert result.key_point_details[0].number == 1
    assert result.key_point_details[0].type == "expected"
    assert result.key_point_details[2].type == "own_idea"
    assert len(client.calls) == 1
    assert client.calls[0]["temperature"] == 0.0


@pytest.mark.asyncio
async def test_check_key_points_derives_missing_number(input_data: WritingEvaluationInput) -> None:
    client = FakeLLMClient(
        [
            {
                "fulfilled_key_points": ["P1"],
                "own_ideas": [],
                "invalid_points": [],
                "explanation": "Teilweise.",
                "positive_feedback": [],
                "improvement_feedback": [],
                "key_point_details": [
                    {
                        "key_point": "P1",
                        "status": "fulfilled",
                        "sentence_count": 2,
                        "situation_appropriate": True,
                        "language_level": "B2",
                        "comment": "P1 erfüllt.",
                    }
                ],
            }
        ]
    )
    result = await check_key_points(client, input_data)
    assert result.key_point_details[0].number == 1
    assert result.key_point_details[1].number == 2
    assert result.key_point_details[1].status == "not_fulfilled"


@pytest.mark.asyncio
async def test_check_key_points_applies_deterministic_status_rules(
    input_data: WritingEvaluationInput,
) -> None:
    client = FakeLLMClient(
        [
            {
                # Intentionally contradictory LLM output; checker must normalize deterministically.
                "fulfilled_key_points": ["P1", "P2"],
                "own_ideas": ["Eigene Idee"],
                "invalid_points": [],
                "explanation": "Teilweise.",
                "positive_feedback": ["Punkte erkannt."],
                "improvement_feedback": ["Mehr ausführen."],
                "key_point_details": [
                    {
                        "number": 1,
                        "type": "expected",
                        "key_point": "P1",
                        "status": "fulfilled",
                        "sentence_count": 1,
                        "situation_appropriate": "ja",
                        "language_level": "B2",
                        "comment": "Nur kurz erwähnt.",
                    },
                    {
                        "number": 2,
                        "type": "expected",
                        "key_point": "P2",
                        "status": "fulfilled",
                        "sentence_count": 0,
                        "situation_appropriate": "true",
                        "language_level": "B1+",
                        "comment": "Nicht ausgebaut.",
                    },
                    {
                        "number": 99,
                        "type": "expected",
                        "key_point": "P2",
                        "status": "fulfilled",
                        "sentence_count": 3,
                        "situation_appropriate": "nein",
                        "language_level": "B1+",
                        "comment": "Situativ unpassend.",
                    },
                    {
                        "number": None,
                        "type": "own_idea",
                        "key_point": "Soll ignoriert werden",
                        "status": "fulfilled",
                        "sentence_count": 5,
                        "situation_appropriate": True,
                        "language_level": "B2",
                        "comment": "LLM should not return own ideas in expected details.",
                    },
                ],
            }
        ]
    )
    result = await check_key_points(client, input_data)

    expected_details = [d for d in result.key_point_details if d.type == "expected"]
    own_idea_details = [d for d in result.key_point_details if d.type == "own_idea"]

    # fulfilled + sentence_count=1 -> partially_fulfilled
    assert expected_details[0].key_point == "P1"
    assert expected_details[0].status == "partially_fulfilled"

    # sentence_count=0 -> not_fulfilled
    assert expected_details[1].key_point == "P2"
    assert expected_details[1].status == "not_fulfilled"

    # fulfilled_key_points rebuilt from normalized expected details
    assert result.fulfilled_key_points == []

    # own ideas are appended as own_idea details exactly once
    assert len(own_idea_details) == 1
    assert own_idea_details[0].key_point == "Eigene Idee"
    assert own_idea_details[0].type == "own_idea"


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
                "communication_indicators": [
                    {
                        "aspect": "email_elements",
                        "label": "E-Mail-Elemente",
                        "rating": "good",
                        "comment": "Die zentralen E-Mail-Bausteine sind weitgehend vorhanden.",
                    },
                    {
                        "aspect": "vocabulary",
                        "label": "Wortschatz",
                        "rating": "acceptable",
                        "comment": "Der Wortschatz passt, bleibt aber teils allgemein.",
                    },
                ],
            }
        ]
    )
    result = await check_communication(client, input_data)
    assert isinstance(result, CommunicationCheckResult)
    assert result.email_structure_quality == "excellent"
    assert result.coherence_quality == "good"
    assert result.cohesion_quality == "missing"
    assert result.register_quality == "good"
    assert result.sentence_variety_quality == "acceptable"
    assert len(result.communication_indicators) == 7
    expected_aspects = {
        "email_elements",
        "structure",
        "coherence",
        "cohesion",
        "register",
        "vocabulary",
        "sentence_variety",
    }
    assert {item.aspect for item in result.communication_indicators} == expected_aspects
    assert len(client.calls) == 1
    assert client.calls[0]["temperature"] == 0.0


@pytest.mark.asyncio
async def test_check_communication_normalizes_missing_label_and_rating(input_data: WritingEvaluationInput) -> None:
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
                "communication_indicators": [
                    {
                        "aspect": "coherence",
                        "rating": "good",
                        "comment": "Teilweise klar verbunden.",
                    }
                ],
            }
        ]
    )
    result = await check_communication(client, input_data)
    assert len(result.communication_indicators) == 7
    coherence = [item for item in result.communication_indicators if item.aspect == "coherence"][0]
    assert coherence.label == "Zusammenhang"
    assert coherence.rating == "good"


@pytest.mark.asyncio
async def test_check_communication_retries_and_then_raises(input_data: WritingEvaluationInput) -> None:
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
                "communication_indicators": "invalid",
            },
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
                "communication_indicators": "still-invalid",
            },
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
                "communication_indicators": "nope",
            },
        ]
    )
    with pytest.raises(CommunicationAnalysisFailed):
        await check_communication(client, input_data)
    assert len(client.calls) == 3


@pytest.mark.asyncio
async def test_check_communication_retries_then_succeeds(input_data: WritingEvaluationInput) -> None:
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
                "communication_indicators": "invalid",
            },
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
                "communication_indicators": [
                    {
                        "aspect": "email_elements",
                        "label": "E-Mail-Elemente",
                        "rating": "good",
                        "comment": "Die Grundelemente sind vorhanden.",
                    }
                ],
            },
        ]
    )
    result = await check_communication(client, input_data)
    assert len(client.calls) == 2
    assert len(result.communication_indicators) == 7


def test_communication_normalizers_return_valid_schema_values() -> None:
    assert _normalize_rating(None) == "missing"
    assert _normalize_rating("strong") == "excellent"
    assert _normalize_rating("ok") == "acceptable"
    assert _normalize_rating("poor") == "weak"
    assert _normalize_rating("unknown-value") == "weak"

    assert _normalize_vocabulary_level(" b2 ") == "B2"
    assert _normalize_vocabulary_level("b1+") == "B1+"
    assert _normalize_vocabulary_level("invalid") == "B1"


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
                "accuracy_details": [
                    {
                        "aspect": "grammar",
                        "status": "adequate",
                        "error_count": 1,
                        "comment": "Nur ein klarer Kasusfehler.",
                    },
                    {
                        "aspect": "comprehension",
                        "status": "strong",
                        "comment": "Die Verständlichkeit ist nicht beeinträchtigt.",
                    },
                ],
                "highlighted_errors": [
                    {
                        "text": "Candidate",
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
    assert len(result.accuracy_details) == 6
    grammar = [item for item in result.accuracy_details if item.aspect == "grammar"][0]
    assert grammar.label == "Grammatik"
    assert grammar.error_count == 1
    assert result.highlighted_errors[0].error_type == "Kasusfehler"
    assert result.highlighted_errors[0].aspect is None
    assert len(client.calls) == 1
    assert client.calls[0]["temperature"] == 0.0


@pytest.mark.asyncio
async def test_check_accuracy_derives_missing_label_and_error_count(input_data: WritingEvaluationInput) -> None:
    client = FakeLLMClient(
        [
            {
                "grammar_control": "good",
                "systematic_errors": [],
                "spelling_quality": "acceptable",
                "punctuation_quality": "acceptable",
                "comprehension_affected": False,
                "explanation": "Verstaendlich.",
                "positive_feedback": [],
                "improvement_feedback": [],
                "example_errors": [],
                "technical_notes": [],
                "accuracy_details": [
                    {
                        "aspect": "word_order",
                        "status": "acceptable",
                        "comment": "Teilweise uneinheitlich.",
                    }
                ],
                "highlighted_errors": [],
            }
        ]
    )
    result = await check_accuracy(client, input_data)
    word_order = [item for item in result.accuracy_details if item.aspect == "word_order"][0]
    assert word_order.label == "Wortstellung"
    assert word_order.status == "adequate"
    assert word_order.error_count == 0


@pytest.mark.asyncio
async def test_checker_invalid_response_raises_validation_error(input_data: WritingEvaluationInput) -> None:
    client = FakeLLMClient([{"topic_mismatch": False}])
    with pytest.raises(ValidationError):
        await check_relevance(client, input_data)

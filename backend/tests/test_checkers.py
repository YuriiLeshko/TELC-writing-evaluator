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
                "communication_details": [
                    {
                        "aspect": "email_elements",
                        "label": "E-Mail-Elemente",
                        "status": "strong",
                        "level": None,
                        "present_items": ["Betreff", "Anrede", "Hauptteil", "Grußformel"],
                        "missing_items": ["Schluss"],
                        "evidence": ["Betreff: Beschädigte Lieferung", "Sehr geehrte Damen und Herren"],
                        "comment": "Die zentralen E-Mail-Bausteine sind weitgehend vorhanden.",
                    },
                    {
                        "aspect": "vocabulary",
                        "label": "Wortschatz",
                        "status": "adequate",
                        "level": "B1+",
                        "present_items": ["aufgabenbezogene Lexik"],
                        "missing_items": ["präzisere Nuancen"],
                        "evidence": ["beschädigt", "zurückerstatten"],
                        "comment": "Der Wortschatz passt, bleibt aber teils allgemein.",
                    },
                ],
            }
        ]
    )
    result = await check_communication(client, input_data)
    assert isinstance(result, CommunicationCheckResult)
    assert len(result.communication_details) == 7
    expected_aspects = {
        "email_elements",
        "structure",
        "coherence",
        "cohesion",
        "register",
        "vocabulary",
        "sentence_variety",
    }
    assert {item.aspect for item in result.communication_details} == expected_aspects
    assert len(client.calls) == 1
    assert client.calls[0]["temperature"] == 0.0


@pytest.mark.asyncio
async def test_check_communication_normalizes_missing_label_and_arrays(input_data: WritingEvaluationInput) -> None:
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
                "positive_feedback": [],
                "improvement_feedback": [],
                "linking_devices": [],
                "complex_connectors": [],
                "language_level_comment": "Nahe B2.",
                "communication_details": [
                    {
                        "aspect": "coherence",
                        "status": "acceptable",
                        "comment": "Teilweise klar verbunden.",
                    }
                ],
            }
        ]
    )
    result = await check_communication(client, input_data)
    assert len(result.communication_details) == 7
    coherence = [item for item in result.communication_details if item.aspect == "coherence"][0]
    assert coherence.label == "Zusammenhang"
    assert coherence.status == "adequate"
    assert coherence.present_items == []
    assert coherence.missing_items == []
    assert coherence.evidence == []
    assert coherence.level is None


@pytest.mark.asyncio
async def test_check_communication_rejects_non_array_details(input_data: WritingEvaluationInput) -> None:
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
                "positive_feedback": [],
                "improvement_feedback": [],
                "linking_devices": [],
                "complex_connectors": [],
                "language_level_comment": "Nahe B2.",
                "communication_details": "invalid",
            }
        ]
    )
    with pytest.raises(ValueError):
        await check_communication(client, input_data)


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

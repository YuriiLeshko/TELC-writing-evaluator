from __future__ import annotations

from backend.evaluation.prompts.accuracy import build_accuracy_user_prompt
from backend.evaluation.prompts.communication import build_communication_user_prompt
from backend.evaluation.prompts.improvement import build_improvement_user_prompt
from backend.evaluation.prompts.key_points import build_key_points_user_prompt
from backend.evaluation.prompts.relevance import build_relevance_user_prompt
from backend.evaluation.schemas import WritingEvaluationInput


def test_relevance_prompt_contains_required_parts() -> None:
    prompt = build_relevance_user_prompt(
        "TASK",
        ["Problem beschreiben", "Lösung verlangen"],
        "CANDIDATE",
    )
    assert "TASK" in prompt
    assert "CANDIDATE" in prompt
    assert "topic_mismatch" in prompt
    assert "German" in prompt
    assert "assign grades" not in prompt.lower()


def test_key_points_prompt_contains_required_parts() -> None:
    prompt = build_key_points_user_prompt("TASK", ["P1", "P2"], "CANDIDATE")
    assert "TASK" in prompt
    assert "CANDIDATE" in prompt
    assert "fulfilled_key_points" in prompt
    assert "key_point_details" in prompt
    assert "do not assign grades" in prompt.lower()
    assert "German" in prompt


def test_communication_prompt_contains_required_parts() -> None:
    prompt = build_communication_user_prompt("TASK", "CANDIDATE")
    assert "TASK" in prompt
    assert "CANDIDATE" in prompt
    assert "register_quality" in prompt
    assert "communication_indicators" in prompt
    assert "do not assign grades" in prompt.lower()
    assert "German" in prompt


def test_accuracy_prompt_contains_highlighted_error_rules() -> None:
    prompt = build_accuracy_user_prompt("CANDIDATE")
    assert "CANDIDATE" in prompt
    assert "accuracy_details" in prompt
    assert "highlighted_errors" in prompt
    assert '"aspect": "grammar | syntax | word_order | spelling | punctuation | comprehension"' in prompt
    assert "do not assign grades" in prompt.lower()
    assert "German" in prompt


def test_improvement_prompt_contains_no_invented_facts_rule() -> None:
    input_data = WritingEvaluationInput(
        task_text="TASK",
        expected_key_points=["P1", "P2"],
        candidate_text="CANDIDATE",
    )
    prompt = build_improvement_user_prompt(input_data)
    assert "CANDIDATE" in prompt
    assert "TASK" in prompt
    assert "Keine konkreten Fakten erfinden" in prompt
    assert "improved_text" in prompt

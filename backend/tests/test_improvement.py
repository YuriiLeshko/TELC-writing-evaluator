from __future__ import annotations

import pytest
from pydantic import ValidationError

from backend.evaluation.improvement import generate_improved_text
from backend.evaluation.schemas import WritingEvaluationInput
from backend.tests.conftest import FakeLLMClient


@pytest.mark.asyncio
async def test_generate_improved_text_success() -> None:
    input_data = WritingEvaluationInput(
        task_text="Task",
        expected_key_points=["P1", "P2"],
        candidate_text="Text",
    )
    client = FakeLLMClient([{"improved_text": "Verbesserter Text"}])
    result = await generate_improved_text(client, input_data)
    assert result.improved_text == "Verbesserter Text"
    assert len(client.calls) == 1
    assert client.calls[0]["temperature"] == 0.2


@pytest.mark.asyncio
async def test_generate_improved_text_invalid_response_raises() -> None:
    input_data = WritingEvaluationInput(
        task_text="Task",
        expected_key_points=["P1", "P2"],
        candidate_text="Text",
    )
    client = FakeLLMClient([{"wrong": "shape"}])
    with pytest.raises(ValidationError):
        await generate_improved_text(client, input_data)

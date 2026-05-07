from __future__ import annotations

import json
from typing import Any

import httpx
import pytest

from backend.services.llm_client import (
    LLMClient,
    LLMClientError,
    LLMJSONParseError,
    LLMResponseError,
)


def _build_client(**kwargs: Any) -> LLMClient:
    return LLMClient(
        api_key="test-key",
        model_name="primary-model",
        fallback_model_name="fallback-model",
        openrouter_url="https://example.invalid/v1/chat/completions",
        **kwargs,
    )


def test_clean_json_response_removes_json_fences_and_whitespace() -> None:
    text = "  ```json\n{\"status\":\"ok\"}\n```  "
    cleaned = LLMClient._clean_json_response(text)
    assert cleaned == "{\"status\":\"ok\"}"


def test_clean_json_response_removes_plain_fences_and_whitespace() -> None:
    text = "  ```\n{\"status\":\"ok\"}\n```  "
    cleaned = LLMClient._clean_json_response(text)
    assert cleaned == "{\"status\":\"ok\"}"


def test_extract_content_returns_valid_openrouter_message_content() -> None:
    payload = {
        "choices": [
            {
                "message": {"content": '{"ok": true}'},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5},
    }
    assert LLMClient._extract_content(payload) == '{"ok": true}'


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"choices": []},
        {"choices": [{}]},
        {"choices": [{"message": {}}]},
        {"choices": [{"message": {"content": 123}}]},
    ],
)
def test_extract_content_raises_for_invalid_structures(payload: dict[str, Any]) -> None:
    with pytest.raises(LLMResponseError):
        LLMClient._extract_content(payload)


@pytest.mark.asyncio
async def test_call_llm_json_returns_dict_when_valid_json(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _build_client()

    async def fake_call_llm(*args: Any, **kwargs: Any) -> str:
        return '{"status":"ok","value":1}'

    monkeypatch.setattr(client, "call_llm", fake_call_llm)
    result = await client.call_llm_json(system_prompt="s", user_prompt="u")
    assert result == {"status": "ok", "value": 1}


@pytest.mark.asyncio
async def test_call_llm_json_parses_fenced_json(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _build_client()

    async def fake_call_llm(*args: Any, **kwargs: Any) -> str:
        return '```json\n{"status":"ok"}\n```'

    monkeypatch.setattr(client, "call_llm", fake_call_llm)
    result = await client.call_llm_json(system_prompt="s", user_prompt="u")
    assert result == {"status": "ok"}


@pytest.mark.asyncio
async def test_call_llm_json_raises_on_invalid_json(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _build_client()

    async def fake_call_llm(*args: Any, **kwargs: Any) -> str:
        return "{invalid-json"

    monkeypatch.setattr(client, "call_llm", fake_call_llm)
    with pytest.raises(LLMJSONParseError):
        await client.call_llm_json(system_prompt="s", user_prompt="u")


@pytest.mark.asyncio
async def test_call_llm_json_raises_on_json_array(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _build_client()

    async def fake_call_llm(*args: Any, **kwargs: Any) -> str:
        return '["not","an","object"]'

    monkeypatch.setattr(client, "call_llm", fake_call_llm)
    with pytest.raises(LLMJSONParseError):
        await client.call_llm_json(system_prompt="s", user_prompt="u")


@pytest.mark.asyncio
async def test_make_request_success(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _build_client(retry_attempts=2)
    post_calls = {"count": 0}

    class MockResponse:
        status_code = 200
        text = "ok"

        @staticmethod
        def json() -> dict[str, Any]:
            return {
                "choices": [{"message": {"content": "hello"}, "finish_reason": "stop"}],
                "usage": {"prompt_tokens": 1, "completion_tokens": 1},
            }

    class MockAsyncClient:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

        async def __aenter__(self) -> "MockAsyncClient":
            return self

        async def __aexit__(self, exc_type, exc, tb) -> None:
            return None

        async def post(self, *args: Any, **kwargs: Any) -> MockResponse:
            post_calls["count"] += 1
            return MockResponse()

    monkeypatch.setattr(httpx, "AsyncClient", MockAsyncClient)
    result = await client._make_request(
        model_name="primary-model",
        system_prompt="s",
        user_prompt="u",
        temperature=0.0,
        max_tokens=10,
    )
    assert result == "hello"
    assert post_calls["count"] == 1


@pytest.mark.asyncio
async def test_make_request_non_200_retries_then_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _build_client(retry_attempts=3)
    post_calls = {"count": 0}
    sleep_calls = {"count": 0}

    class MockResponse:
        status_code = 500
        text = "server error"

        @staticmethod
        def json() -> dict[str, Any]:
            return {}

    class MockAsyncClient:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

        async def __aenter__(self) -> "MockAsyncClient":
            return self

        async def __aexit__(self, exc_type, exc, tb) -> None:
            return None

        async def post(self, *args: Any, **kwargs: Any) -> MockResponse:
            post_calls["count"] += 1
            return MockResponse()

    async def fake_sleep(seconds: float) -> None:
        sleep_calls["count"] += 1

    monkeypatch.setattr(httpx, "AsyncClient", MockAsyncClient)
    monkeypatch.setattr("backend.services.llm_client.asyncio.sleep", fake_sleep)

    with pytest.raises(LLMClientError):
        await client._make_request(
            model_name="primary-model",
            system_prompt="s",
            user_prompt="u",
            temperature=0.0,
            max_tokens=10,
        )
    assert post_calls["count"] == 3
    assert sleep_calls["count"] == 2


@pytest.mark.asyncio
async def test_make_request_invalid_response_json_retries_then_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _build_client(retry_attempts=2)
    post_calls = {"count": 0}

    class MockResponse:
        status_code = 200
        text = "ok"

        @staticmethod
        def json() -> dict[str, Any]:
            raise json.JSONDecodeError("bad json", "x", 0)

    class MockAsyncClient:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

        async def __aenter__(self) -> "MockAsyncClient":
            return self

        async def __aexit__(self, exc_type, exc, tb) -> None:
            return None

        async def post(self, *args: Any, **kwargs: Any) -> MockResponse:
            post_calls["count"] += 1
            return MockResponse()

    async def fake_sleep(seconds: float) -> None:
        return None

    monkeypatch.setattr(httpx, "AsyncClient", MockAsyncClient)
    monkeypatch.setattr("backend.services.llm_client.asyncio.sleep", fake_sleep)

    with pytest.raises(LLMClientError):
        await client._make_request(
            model_name="primary-model",
            system_prompt="s",
            user_prompt="u",
            temperature=0.0,
            max_tokens=10,
        )
    assert post_calls["count"] == 2


@pytest.mark.asyncio
async def test_make_request_empty_content_retries_then_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _build_client(retry_attempts=2)
    post_calls = {"count": 0}

    class MockResponse:
        status_code = 200
        text = "ok"

        @staticmethod
        def json() -> dict[str, Any]:
            return {"choices": [{"message": {"content": "   "}}]}

    class MockAsyncClient:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

        async def __aenter__(self) -> "MockAsyncClient":
            return self

        async def __aexit__(self, exc_type, exc, tb) -> None:
            return None

        async def post(self, *args: Any, **kwargs: Any) -> MockResponse:
            post_calls["count"] += 1
            return MockResponse()

    async def fake_sleep(seconds: float) -> None:
        return None

    monkeypatch.setattr(httpx, "AsyncClient", MockAsyncClient)
    monkeypatch.setattr("backend.services.llm_client.asyncio.sleep", fake_sleep)

    with pytest.raises(LLMClientError):
        await client._make_request(
            model_name="primary-model",
            system_prompt="s",
            user_prompt="u",
            temperature=0.0,
            max_tokens=10,
        )
    assert post_calls["count"] == 2


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "network_exc",
    [
        httpx.TimeoutException("timeout"),
        httpx.RequestError("request failed", request=httpx.Request("POST", "https://example.invalid")),
    ],
)
async def test_make_request_network_errors_retry_then_raise(
    monkeypatch: pytest.MonkeyPatch,
    network_exc: Exception,
) -> None:
    client = _build_client(retry_attempts=3)
    post_calls = {"count": 0}
    sleep_calls = {"count": 0}

    class MockAsyncClient:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

        async def __aenter__(self) -> "MockAsyncClient":
            return self

        async def __aexit__(self, exc_type, exc, tb) -> None:
            return None

        async def post(self, *args: Any, **kwargs: Any) -> Any:
            post_calls["count"] += 1
            raise network_exc

    async def fake_sleep(seconds: float) -> None:
        sleep_calls["count"] += 1

    monkeypatch.setattr(httpx, "AsyncClient", MockAsyncClient)
    monkeypatch.setattr("backend.services.llm_client.asyncio.sleep", fake_sleep)

    with pytest.raises(LLMClientError):
        await client._make_request(
            model_name="primary-model",
            system_prompt="s",
            user_prompt="u",
            temperature=0.0,
            max_tokens=10,
        )
    assert post_calls["count"] == 3
    assert sleep_calls["count"] == 2


@pytest.mark.asyncio
async def test_call_llm_primary_success_returns_primary_result(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _build_client()
    calls: list[str] = []

    async def fake_make_request(*args: Any, **kwargs: Any) -> str:
        calls.append(kwargs["model_name"])
        return "primary-result"

    monkeypatch.setattr(client, "_make_request", fake_make_request)
    result = await client.call_llm(system_prompt="s", user_prompt="u")
    assert result == "primary-result"
    assert calls == ["primary-model"]


@pytest.mark.asyncio
async def test_call_llm_primary_fails_fallback_succeeds(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _build_client()
    calls: list[str] = []

    async def fake_make_request(*args: Any, **kwargs: Any) -> str:
        model_name = kwargs["model_name"]
        calls.append(model_name)
        if model_name == "primary-model":
            raise LLMClientError("primary failed")
        return "fallback-result"

    monkeypatch.setattr(client, "_make_request", fake_make_request)
    result = await client.call_llm(system_prompt="s", user_prompt="u")
    assert result == "fallback-result"
    assert calls == ["primary-model", "fallback-model"]


@pytest.mark.asyncio
async def test_call_llm_both_primary_and_fallback_fail(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _build_client()
    calls: list[str] = []

    async def fake_make_request(*args: Any, **kwargs: Any) -> str:
        calls.append(kwargs["model_name"])
        raise LLMClientError("boom")

    monkeypatch.setattr(client, "_make_request", fake_make_request)
    with pytest.raises(LLMClientError):
        await client.call_llm(system_prompt="s", user_prompt="u")
    assert calls == ["primary-model", "fallback-model"]

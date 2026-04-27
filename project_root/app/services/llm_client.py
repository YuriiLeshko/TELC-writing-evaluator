"""app/services/llm_client.py

Simple async LLM client for OpenRouter API.

Architecture:
This module is responsible only for communication with the LLM provider.
It does not contain FastAPI, database, OCR, or evaluation logic.

Dependencies:
pip install httpx python-dotenv

Required environment variables:
OPENROUTER_API_KEY

Optional environment variables:
MODEL_NAME
FALLBACK_MODEL_NAME

Example .env:
OPENROUTER_API_KEY=your_api_key_here
MODEL_NAME=openai/gpt-oss-120b:free
FALLBACK_MODEL_NAME=meta-llama/llama-3.3-70b-instruct:free
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Any

import httpx
from dotenv import load_dotenv


load_dotenv()

logger = logging.getLogger(__name__)


OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

DEFAULT_MODEL_NAME = "openai/gpt-oss-120b:free"
DEFAULT_FALLBACK_MODEL_NAME = "meta-llama/llama-3.3-70b-instruct:free"

REQUEST_TIMEOUT_SECONDS = 20.0
RETRY_ATTEMPTS = 2
DEFAULT_TEMPERATURE = 0.2
DEFAULT_MAX_TOKENS = 1000


class LLMClientError(Exception):
    """Base exception for LLM client errors."""


class LLMResponseError(LLMClientError):
    """Raised when the LLM response is invalid or unsuccessful."""


class LLMJSONParseError(LLMClientError):
    """Raised when the LLM response cannot be parsed as JSON."""


def _get_required_env(name: str) -> str:
    value = os.getenv(name)

    if value is None or not value.strip():
        raise LLMClientError(f"{name} is required.")

    return value.strip()


def _get_optional_env(name: str, default: str) -> str:
    value = os.getenv(name)

    if value is None or not value.strip():
        return default

    return value.strip()


class LLMClient:
    def __init__(
        self,
        api_key: str | None = None,
        model_name: str | None = None,
        fallback_model_name: str | None = None,
        openrouter_url: str | None = None,
        request_timeout_seconds: float | None = None,
        retry_attempts: int | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> None:
        self.api_key = api_key or _get_required_env("OPENROUTER_API_KEY")

        self.model_name = (
            model_name
            or _get_optional_env("MODEL_NAME", DEFAULT_MODEL_NAME)
        )

        self.fallback_model_name = (
            fallback_model_name
            or _get_optional_env("FALLBACK_MODEL_NAME", DEFAULT_FALLBACK_MODEL_NAME)
        )

        self.openrouter_url = openrouter_url or OPENROUTER_URL

        self.request_timeout_seconds = (
            request_timeout_seconds
            if request_timeout_seconds is not None
            else REQUEST_TIMEOUT_SECONDS
        )

        self.retry_attempts = (
            retry_attempts
            if retry_attempts is not None
            else RETRY_ATTEMPTS
        )

        self.temperature = (
            temperature
            if temperature is not None
            else DEFAULT_TEMPERATURE
        )

        self.max_tokens = (
            max_tokens
            if max_tokens is not None
            else DEFAULT_MAX_TOKENS
        )

    async def call_llm(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        request_temperature = (
            temperature
            if temperature is not None
            else self.temperature
        )

        request_max_tokens = (
            max_tokens
            if max_tokens is not None
            else self.max_tokens
        )

        try:
            return await self._make_request(
                model_name=self.model_name,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=request_temperature,
                max_tokens=request_max_tokens,
            )
        except LLMClientError as primary_error:
            logger.warning(
                "Primary model failed: %s. Switching to fallback model: %s",
                self.model_name,
                self.fallback_model_name,
            )

            try:
                return await self._make_request(
                    model_name=self.fallback_model_name,
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    temperature=request_temperature,
                    max_tokens=request_max_tokens,
                )
            except LLMClientError as fallback_error:
                raise LLMClientError(
                    "Both primary and fallback LLM requests failed."
                ) from fallback_error

    async def call_llm_json(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        response_text = await self.call_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        cleaned = self._clean_json_response(response_text)

        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            logger.error("Failed to parse LLM response as JSON: %s", cleaned)
            raise LLMJSONParseError("LLM response is not valid JSON.") from exc

        if not isinstance(parsed, dict):
            raise LLMJSONParseError("LLM JSON response must be an object.")

        return parsed

    async def _make_request(
        self,
        model_name: str,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int,
    ) -> str:
        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        logger.info("Starting LLM request. Model: %s", model_name)

        last_error: Exception | None = None

        for attempt in range(1, self.retry_attempts + 1):
            try:
                async with httpx.AsyncClient(
                    timeout=self.request_timeout_seconds
                ) as client:
                    response = await client.post(
                        self.openrouter_url,
                        headers=headers,
                        json=payload,
                    )

                if response.status_code != 200:
                    raise LLMResponseError(
                        f"OpenRouter API error: "
                        f"model={model_name}, "
                        f"status={response.status_code}, "
                        f"body={response.text}"
                    )

                try:
                    data: dict[str, Any] = response.json()
                except json.JSONDecodeError as exc:
                    raise LLMResponseError("OpenRouter returned invalid JSON.") from exc

                content = self._extract_content(data)

                if not content.strip():
                    raise LLMResponseError("OpenRouter returned an empty response.")

                logger.info("LLM request completed successfully. Model: %s", model_name)
                return content

            except (httpx.RequestError, httpx.TimeoutException) as exc:
                last_error = exc
                logger.error(
                    "Network error during LLM request. "
                    "Model: %s. Attempt %s/%s: %s",
                    model_name,
                    attempt,
                    self.retry_attempts,
                    exc,
                )

            except LLMResponseError as exc:
                last_error = exc
                logger.error(
                    "LLM response error. "
                    "Model: %s. Attempt %s/%s: %s",
                    model_name,
                    attempt,
                    self.retry_attempts,
                    exc,
                )

            if attempt < self.retry_attempts:
                await asyncio.sleep(1)

        raise LLMClientError(
            f"LLM request failed after retries. Model: {model_name}"
        ) from last_error

    @staticmethod
    def _extract_content(data: dict[str, Any]) -> str:
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMResponseError("Unexpected OpenRouter response structure.") from exc

        if not isinstance(content, str):
            raise LLMResponseError("LLM response content is not a string.")

        return content

    @staticmethod
    def _clean_json_response(text: str) -> str:
        cleaned = text.strip()

        if cleaned.startswith("```json"):
            cleaned = cleaned.removeprefix("```json").strip()

        if cleaned.startswith("```"):
            cleaned = cleaned.removeprefix("```").strip()

        if cleaned.endswith("```"):
            cleaned = cleaned.removesuffix("```").strip()

        return cleaned


async def _test_text_call(client: LLMClient) -> None:
    result = await client.call_llm(
        system_prompt="You are a helpful assistant.",
        user_prompt="Reply with one short sentence: LLM text call works.",
    )

    print("\nTEXT TEST RESULT:")
    print(result)


async def _test_json_call(client: LLMClient) -> None:
    result = await client.call_llm_json(
        system_prompt=(
            "You are a helpful assistant. "
            "Return only valid JSON. No markdown. No explanation."
        ),
        user_prompt=(
            'Return this JSON object: {"status": "ok", "message": "LLM JSON call works"}'
        ),
    )

    print("\nJSON TEST RESULT:")
    print(json.dumps(result, ensure_ascii=False, indent=2))


async def _test() -> None:
    client = LLMClient()

    await _test_text_call(client)
    await _test_json_call(client)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(_test())
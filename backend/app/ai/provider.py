"""
Provider-agnostic LLM adapter with structured output enforcement.
Supports OpenAI, Anthropic, and Google Gemini.
Uses tenacity for exponential-backoff retries.
"""
from __future__ import annotations

import json
from typing import Any, TypeVar, Type

import structlog
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.config import get_settings

logger = structlog.get_logger(__name__)
T = TypeVar("T")

settings = get_settings()


class LLMError(Exception):
    """Base class for LLM provider errors."""


class LLMRateLimitError(LLMError):
    """Rate limit hit — caller should wait."""


class LLMStructuredOutputError(LLMError):
    """LLM returned output that doesn't match expected schema."""


def _build_system_message(instruction: str) -> str:
    return (
        "You are a legal document processing assistant. "
        "You extract structured information from legal documents with high accuracy. "
        "You NEVER invent facts, dates, names, or legal provisions. "
        "If information is missing, you mark it as absent. "
        "You always respond with valid JSON matching the requested schema exactly.\n\n"
        + instruction
    )


class LLMProvider:
    """
    Unified LLM adapter. Instantiate once and inject via dependency.
    All calls return structured JSON validated against a Pydantic schema.
    """

    def __init__(self) -> None:
        self._client: Any = None
        self._provider = settings.LLM_PROVIDER
        self._model = settings.get_default_model()

    def _get_client(self) -> Any:
        if self._client is not None:
            return self._client

        if self._provider == "openai":
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(
                api_key=settings.OPENAI_API_KEY,
                timeout=settings.LLM_TIMEOUT_SECONDS,
                max_retries=0,  # We handle retries ourselves
            )
        elif self._provider == "anthropic":
            from anthropic import AsyncAnthropic
            self._client = AsyncAnthropic(
                api_key=settings.ANTHROPIC_API_KEY,
                timeout=settings.LLM_TIMEOUT_SECONDS,
            )
        elif self._provider == "gemini":
            import google.generativeai as genai
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self._client = genai.GenerativeModel(self._model)
        else:
            raise LLMError(f"Unsupported LLM provider: {self._provider}")

        return self._client

    @retry(
        retry=retry_if_exception_type((LLMRateLimitError, TimeoutError)),
        wait=wait_exponential(multiplier=2, min=4, max=60),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    async def complete_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema: Type[T],
        temperature: float | None = None,
    ) -> T:
        """
        Call the LLM and parse response into a validated Pydantic schema.
        Raises LLMStructuredOutputError if parsing fails after retries.
        """
        temp = temperature if temperature is not None else settings.LLM_TEMPERATURE
        log = logger.bind(provider=self._provider, model=self._model)

        try:
            raw_json = await self._call_provider(
                _build_system_message(system_prompt), user_prompt, temp
            )
            log.debug("llm_response_received", chars=len(raw_json))

            # Parse and validate
            data = json.loads(raw_json)
            return response_schema.model_validate(data)

        except json.JSONDecodeError as e:
            log.error("llm_json_parse_error", error=str(e))
            raise LLMStructuredOutputError(f"LLM returned invalid JSON: {e}") from e
        except Exception as e:
            if "rate_limit" in str(e).lower() or "429" in str(e):
                raise LLMRateLimitError(str(e)) from e
            log.error("llm_call_failed", error=str(e))
            raise LLMError(f"LLM call failed: {e}") from e

    async def _call_provider(self, system: str, user: str, temp: float) -> str:
        client = self._get_client()

        if self._provider == "openai":
            response = await client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=temp,
                response_format={"type": "json_object"},
            )
            return response.choices[0].message.content or "{}"

        elif self._provider == "anthropic":
            response = await client.messages.create(
                model=self._model,
                max_tokens=4096,
                system=system,
                messages=[{"role": "user", "content": user}],
                temperature=temp,
            )
            text = response.content[0].text if response.content else "{}"
            # Extract JSON block if wrapped in markdown
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            return text

        elif self._provider == "gemini":
            prompt = f"System: {system}\n\nUser: {user}\n\nRespond ONLY with valid JSON."
            response = await self._client.generate_content_async(
                prompt,
                generation_config={"temperature": temp, "response_mime_type": "application/json"},
            )
            return response.text

        raise LLMError(f"Unknown provider: {self._provider}")

    async def complete_text(self, system_prompt: str, user_prompt: str) -> str:
        """Plain text completion — used for markdown report generation."""
        return await self._call_provider(
            _build_system_message(system_prompt), user_prompt, 0.1
        )


# Singleton
_llm_provider: LLMProvider | None = None


def get_llm_provider() -> LLMProvider:
    global _llm_provider
    if _llm_provider is None:
        _llm_provider = LLMProvider()
    return _llm_provider

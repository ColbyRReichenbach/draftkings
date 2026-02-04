"""OpenAI provider implementation."""

import json
from typing import Any, Dict, Optional

from openai import OpenAI

from ai_services.provider_base import LLMProvider


class OpenAIProvider(LLMProvider):
    """OpenAI-backed LLM provider."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        """
        Initialize the OpenAI client.

        Args:
            api_key: Optional OpenAI API key (uses env if omitted).
        """
        self.client = OpenAI(api_key=api_key)

    def generate_json(
        self,
        prompt: str,
        model: str,
        temperature: float,
        max_tokens: int,
        system_prompt: str | None = None,
    ) -> Dict[str, Any]:
        """
        Generate a JSON response from OpenAI.

        Args:
            prompt: User prompt.
            model: Model name.
            temperature: Sampling temperature.
            max_tokens: Max tokens for response.
            system_prompt: Optional system prompt.

        Returns:
            Parsed JSON response.
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
            messages=messages,
        )

        content = response.choices[0].message.content or ""
        try:
            return json.loads(content)
        except json.JSONDecodeError as exc:
            raise ValueError(f"OpenAI returned invalid JSON: {exc}") from exc

    def generate_text(
        self,
        prompt: str,
        model: str,
        temperature: float,
        max_tokens: int,
        system_prompt: str | None = None,
    ) -> str:
        """
        Generate a plain text response from OpenAI.

        Args:
            prompt: User prompt.
            model: Model name.
            temperature: Sampling temperature.
            max_tokens: Max tokens for response.
            system_prompt: Optional system prompt.

        Returns:
            Response text.
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            messages=messages,
        )

        return response.choices[0].message.content or ""

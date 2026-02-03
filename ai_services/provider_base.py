"""Provider-agnostic LLM interface."""

from abc import ABC, abstractmethod
from typing import Any, Dict


class LLMProvider(ABC):
    """Abstract LLM provider interface."""

    @abstractmethod
    def generate_json(
        self,
        prompt: str,
        model: str,
        temperature: float,
        max_tokens: int,
        system_prompt: str | None = None,
    ) -> Dict[str, Any]:
        """Generate a JSON response from a prompt."""
        raise NotImplementedError

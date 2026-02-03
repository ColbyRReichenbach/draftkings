"""Configuration for LLM providers and model selection."""

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class LLMConfig:
    """Runtime configuration for LLM usage."""

    provider: str = os.getenv("LLM_PROVIDER", "openai")
    fast_model: str = os.getenv("LLM_MODEL_FAST", "gpt-4o-mini")
    reasoning_model: str = os.getenv("LLM_MODEL_REASONING", "gpt-4.1")
    temperature: float = float(os.getenv("LLM_TEMPERATURE", "0.3"))
    max_tokens: int = int(os.getenv("LLM_MAX_TOKENS", "1500"))

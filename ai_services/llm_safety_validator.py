"""Safety validation for LLM-generated customer nudges."""

from __future__ import annotations

import re
from typing import List, Optional

from ai_services.config import LLMConfig
from ai_services.provider_base import LLMProvider
from ai_services.schemas import NudgeValidationResult


class LLMSafetyValidator:
    """Validates LLM-generated customer nudges for compliance."""

    PROHIBITED_PATTERNS = [
        r"\b(irresponsible|reckless|stupid|foolish)\b",
        r"\b(addicted|addict|problem gambler)\b",
        r"\b(must|required|mandatory|have to)\b",
        r"\b(report to authorities|notify police)\b",
        r"\b(diagnose|treatment|disorder)\b",
        r"\$\d{4,}",
    ]

    REQUIRED_PATTERNS = [
        r"(Responsible Gaming Center|rg\.draftkings\.com)",
        r"(you can|option to|available|choose to)",
        r"(help|support|ensure|safely)",
    ]

    def __init__(
        self,
        provider: Optional[LLMProvider] = None,
        config: Optional[LLMConfig] = None,
        enable_llm_checks: bool = False,
    ) -> None:
        """
        Initialize validator.

        Args:
            provider: Optional LLM provider for tone checks.
            config: Optional LLM config.
            enable_llm_checks: Enable optional LLM-based tone analysis.
        """
        self.provider = provider
        self.config = config
        self.enable_llm_checks = enable_llm_checks

    def validate_nudge(self, nudge_text: str, player_context: dict | None = None) -> NudgeValidationResult:
        """
        Validate a customer nudge.

        Args:
            nudge_text: LLM-generated message.
            player_context: Optional context for factual checks.

        Returns:
            NudgeValidationResult with violations list.
        """
        violations: List[str] = []

        for pattern in self.PROHIBITED_PATTERNS:
            if re.search(pattern, nudge_text, re.IGNORECASE):
                violations.append(f"Prohibited phrase detected: {pattern}")

        for pattern in self.REQUIRED_PATTERNS:
            if not re.search(pattern, nudge_text, re.IGNORECASE):
                violations.append(f"Missing required element: {pattern}")

        if self.enable_llm_checks and self.provider and self.config:
            violations.extend(self._llm_tone_check(nudge_text))

        return NudgeValidationResult(is_valid=len(violations) == 0, violations=violations)

    def _llm_tone_check(self, nudge_text: str) -> List[str]:
        """Optional LLM-based tone check (returns violations)."""
        prompt = f"""Evaluate this responsible gaming message for tone compliance:

MESSAGE: \"{nudge_text}\"

REQUIREMENTS:
- Supportive and non-judgmental
- Emphasizes player autonomy
- No shaming or coercive language

Respond in JSON format:
{{\"is_compliant\": true|false, \"violations\": [\"...\"]}}
"""
        raw = self.provider.generate_json(
            prompt=prompt,
            model=self.config.fast_model,
            temperature=0.0,
            max_tokens=300,
            system_prompt="You are a compliance reviewer for responsible gaming messages.",
        )
        violations = raw.get("violations", [])
        if not isinstance(violations, list):
            return ["LLM tone check returned invalid violations format."]
        return [str(v) for v in violations]

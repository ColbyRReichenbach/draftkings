"""Unit tests for LLMSafetyValidator."""

from ai_services.llm_safety_validator import LLMSafetyValidator


def test_validate_nudge_detects_missing_required_elements() -> None:
    validator = LLMSafetyValidator()
    result = validator.validate_nudge("Short message without required elements.")
    assert result.is_valid is False
    assert any("Missing required element" in v for v in result.violations)


def test_validate_nudge_detects_prohibited_language() -> None:
    validator = LLMSafetyValidator()
    result = validator.validate_nudge(
        "You must stop. Your behavior is irresponsible. Visit rg.draftkings.com."
    )
    assert result.is_valid is False
    assert any("Prohibited phrase detected" in v for v in result.violations)


def test_validate_nudge_accepts_compliant_message() -> None:
    validator = LLMSafetyValidator()
    nudge = (
        "We want to help you play safely. You can choose tools in the Responsible "
        "Gaming Center at rg.draftkings.com if you'd like support."
    )
    result = validator.validate_nudge(nudge)
    assert result.is_valid is True

"""AI endpoints for semantic audit and nudge validation."""

from fastapi import APIRouter, Request

from ai_services.schemas import (
    NudgeValidationRequest,
    NudgeValidationResult,
    RiskExplanationRequest,
    RiskExplanationResponse,
)

router = APIRouter()


@router.post("/semantic-audit", response_model=RiskExplanationResponse)
async def semantic_audit(
    payload: RiskExplanationRequest, request: Request, reasoning: bool = True
) -> RiskExplanationResponse:
    """
    Generate a semantic risk explanation for a player.

    Args:
        payload: RiskExplanationRequest payload.
        request: FastAPI request (for app state access).
        reasoning: Whether to use reasoning model.

    Returns:
        RiskExplanationResponse.
    """
    auditor = request.app.state.semantic_auditor
    return auditor.generate_risk_explanation(payload, reasoning=reasoning)


@router.post("/validate-nudge", response_model=NudgeValidationResult)
async def validate_nudge(
    payload: NudgeValidationRequest, request: Request
) -> NudgeValidationResult:
    """
    Validate a customer nudge for compliance.

    Args:
        payload: NudgeValidationRequest payload.
        request: FastAPI request (for app state access).

    Returns:
        NudgeValidationResult with violations.
    """
    validator = request.app.state.nudge_validator
    return validator.validate_nudge(payload.nudge_text)

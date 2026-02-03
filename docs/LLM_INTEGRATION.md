# LLM Integration (Week 5)

## Overview
OpenAI-first LLM integration for semantic risk explanations and compliant customer nudges.

## Environment Variables
- `LLM_PROVIDER` (default: `openai`)
- `LLM_MODEL_FAST` (default: `gpt-4o-mini`)
- `LLM_MODEL_REASONING` (default: `gpt-4.1`)
- `LLM_TEMPERATURE` (default: `0.3`)
- `LLM_MAX_TOKENS` (default: `1500`)
- `OPENAI_API_KEY` (required for runtime)

## Model Selection (Defaults)
- **Fast / volume**: `gpt-4o-mini` (cheap, long context, good for high-throughput tasks)
- **Reasoning**: `gpt-4.1` (highest reasoning quality; adjust if cost-sensitive)

**Optional overrides**:
- Use `gpt-4.1-mini` for strong reasoning at lower cost.
- Use `gpt-4.1-nano` for lightweight classification or large-scale batch jobs.

## Endpoints

### POST `/api/ai/semantic-audit`
Generates a structured, audit-ready explanation of a player’s risk profile.

**Request**
```json
{
  "player_id": "PLR_1234_MA",
  "composite_risk_score": 0.82,
  "risk_category": "HIGH",
  "total_bets_7d": 45,
  "total_wagered_7d": 2850.0,
  "loss_chase_score": 0.78,
  "bet_escalation_score": 0.85,
  "market_drift_score": 0.52,
  "temporal_risk_score": 0.41,
  "gamalyze_risk_score": 0.76,
  "state_jurisdiction": "MA"
}
```

**Response**
```json
{
  "risk_verdict": "HIGH",
  "explanation": "Loss-chasing and escalation are elevated...",
  "key_evidence": ["Loss-chase score high", "Escalation ratio high"],
  "recommended_action": "Apply limits",
  "draft_customer_nudge": "You can choose tools at rg.draftkings.com...",
  "regulatory_notes": "MA abnormal-play rule requires documentation."
}
```

### POST `/api/ai/validate-nudge`
Validates a proposed customer nudge for compliance.

**Request**
```json
{
  "nudge_text": "We want to help you play safely. You can choose tools in the Responsible Gaming Center at rg.draftkings.com."
}
```

**Response**
```json
{
  "is_valid": true,
  "violations": []
}
```

## Run Locally
```bash
export OPENAI_API_KEY="sk-..."
uvicorn backend.main:app --reload
```

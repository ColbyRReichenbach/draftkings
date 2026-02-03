---
name: llm-integration
description: Patterns for OpenAI-first LLM integration and LLM safety validation - use when implementing semantic auditing, generating customer nudges, or validating AI outputs for compliance
allowed-tools: Read, Bash
---

# LLM Integration for Semantic Auditing

## When to Use This Skill
- Integrating OpenAI (primary) or Anthropic (fallback) LLM APIs
- Generating behavioral risk explanations
- Creating customer nudges
- Validating AI-generated content for compliance
- Implementing multi-layer safety checks

---

## Project Standard (OpenAI-First)

**Default implementation lives in** `ai_services/` and `backend/`:
- `ai_services/openai_provider.py`
- `ai_services/semantic_auditor.py`
- `ai_services/llm_safety_validator.py`
- `backend/routers/ai.py`

**Defaults**:
- Fast model: `gpt-4o-mini`
- Reasoning model: `gpt-4.1`

**Cost-sensitive override**:
- `LLM_MODEL_REASONING=gpt-4.1-mini`
- Override via `LLM_MODEL_FAST`, `LLM_MODEL_REASONING`

**Docs**: `docs/LLM_INTEGRATION.md`

**Quick example (project standard)**:
```python
from ai_services.config import LLMConfig
from ai_services.openai_provider import OpenAIProvider
from ai_services.semantic_auditor import BehavioralSemanticAuditor

config = LLMConfig()
provider = OpenAIProvider(api_key=os.getenv("OPENAI_API_KEY"))
auditor = BehavioralSemanticAuditor(provider=provider, config=config)
```

---

## Legacy Pattern (Anthropic Reference)
This section is kept for historical reference. Use the OpenAI-first implementation above unless
explicitly switching providers.

**Purpose**: Generate human-readable explanations of WHY a player is flagged for intervention.
```python
from anthropic import Anthropic
import json
import re

class BehavioralSemanticAuditor:
    def __init__(self, api_key: str):
        self.client = Anthropic(api_key=api_key)
        self.model = "claude-sonnet-3-5-20241022"
    
    def generate_risk_explanation(self, player_data: dict) -> dict:
        """
        Generate semantic explanation of player's risk profile.
        
        Args:
            player_data: Dict with keys:
                - player_id (str)
                - composite_risk_score (float)
                - total_bets_7d (int)
                - total_wagered_7d (float)
                - loss_chase_score (float)
                - market_drift_score (float)
                - [other component scores]
        
        Returns:
            Dict with risk verdict, explanation, evidence, recommended action, draft nudge
        
        Raises:
            ValueError: If player_data missing required keys
            JSONDecodeError: If Claude returns invalid JSON
        """
        
        # Input validation
        required_keys = ['player_id', 'composite_risk_score']
        if not all(k in player_data for k in required_keys):
            raise ValueError(f"Missing required keys: {required_keys}")
        
        prompt = f"""Analyze this player's responsible gaming risk profile:

PLAYER ID: {player_data['player_id']}
COMPOSITE RISK SCORE: {player_data['composite_risk_score']:.2f}/1.00

BEHAVIORAL EVIDENCE (Past 7 Days):
- Total Bets: {player_data.get('total_bets_7d', 'N/A')}
- Total Wagered: ${player_data.get('total_wagered_7d', 0):,.2f}
- Loss Chase Score: {player_data.get('loss_chase_score', 'N/A'):.2f}
- Market Drift Score: {player_data.get('market_drift_score', 'N/A'):.2f}
- Temporal Risk Score: {player_data.get('temporal_risk_score', 'N/A'):.2f}

Provide response in JSON format:
{{
    "risk_verdict": "CRITICAL | HIGH | MEDIUM | LOW",
    "explanation": "2-3 sentence explanation of WHY this player is flagged",
    "key_evidence": ["Evidence 1", "Evidence 2", "Evidence 3"],
    "recommended_action": "Specific intervention recommendation",
    "draft_customer_nudge": "Supportive 2-3 sentence message to player",
    "regulatory_notes": "State-specific reporting requirements if applicable"
}}

CRITICAL REQUIREMENTS for draft_customer_nudge:
- Supportive, non-judgmental tone (never "irresponsible", "addicted")
- Include link to Responsible Gaming Center (rg.draftkings.com)
- Emphasize player autonomy ("you can choose" not "you must")
- NO specific dollar amounts
- NO medical/clinical language
"""
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=1500,
            temperature=0.3,  # Low for consistency
            system="You are a responsible gaming analyst assistant at DraftKings. Your analysis helps protect players while preserving their dignity and autonomy.",
            messages=[{"role": "user", "content": prompt}]
        )
        
        # Parse JSON response
        content = response.content[0].text
        
        # Strip markdown code fences if present
        content = re.sub(r'```json\n?', '', content)
        content = re.sub(r'```\n?', '', content)
        content = content.strip()
        
        try:
            result = json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"Claude returned invalid JSON: {e}\n\nResponse: {content}")
        
        # Validate required fields
        required_fields = ['risk_verdict', 'explanation', 'key_evidence', 
                          'recommended_action', 'draft_customer_nudge']
        if not all(field in result for field in required_fields):
            raise ValueError(f"Missing required fields in response: {required_fields}")
        
        return result
```

---

## Safety Validation Pattern

**Purpose**: Multi-layer validation to ensure AI-generated content meets compliance requirements.
```python
class LLMSafetyValidator:
    """
    Validates LLM-generated customer nudges for compliance.
    
    Implements 4-layer validation:
    1. Regex-based prohibited content check (fastest)
    2. Required elements check
    3. LLM-based tone analysis (catches subtle issues)
    4. Factual consistency check
    """
    
    PROHIBITED_PATTERNS = [
        r'\b(irresponsible|reckless|stupid|foolish)\b',  # Judgmental language
        r'\b(addicted|addict|problem gambler)\b',        # Clinical diagnoses
        r'\b(must|required|mandatory)\b',                # Coercive language
        r'\b(report to authorities|notify police)\b',    # Threats
        r'\b(diagnose|treatment|disorder)\b',            # Medical language
        r'\$\d{4,}',                                      # Specific amounts >$999
    ]
    
    REQUIRED_PATTERNS = [
        r'(Responsible Gaming Center|rg\.draftkings\.com)',  # RG link
        r'(you can|option to|available|choose to)',          # Autonomy language
        r'(help|support|ensure|safely)',                     # Supportive tone
    ]
    
    def __init__(self, claude_client: Anthropic):
        self.claude = claude_client
    
    def validate_nudge(self, 
                      nudge_text: str, 
                      player_context: dict) -> tuple[bool, list[str]]:
        """
        Validate customer nudge for compliance.
        
        Args:
            nudge_text: AI-generated message to player
            player_context: Player data used to generate nudge
        
        Returns:
            (is_valid, list_of_violations)
        """
        violations = []
        
        # LAYER 1: Regex prohibited content (fastest)
        for pattern in self.PROHIBITED_PATTERNS:
            if re.search(pattern, nudge_text, re.IGNORECASE):
                violations.append(f"Prohibited phrase detected: {pattern}")
        
        # LAYER 2: Required elements
        for pattern in self.REQUIRED_PATTERNS:
            if not re.search(pattern, nudge_text, re.IGNORECASE):
                violations.append(f"Missing required element: {pattern}")
        
        # LAYER 3: LLM tone analysis (catches subtle issues)
        tone_violations = self._llm_tone_check(nudge_text)
        violations.extend(tone_violations)
        
        # LAYER 4: Factual consistency (prevents hallucinations)
        consistency_violations = self._check_factual_consistency(
            nudge_text, player_context
        )
        violations.extend(consistency_violations)
        
        return len(violations) == 0, violations
    
    def _llm_tone_check(self, nudge_text: str) -> list[str]:
        """Use LLM to detect subtle tone issues."""
        
        prompt = f"""Evaluate this responsible gaming message for tone compliance:

MESSAGE: "{nudge_text}"

REQUIREMENTS:
- Supportive and non-judgmental
- Emphasizes player autonomy
- No shaming or coercive language
- Professional but empathetic

Respond with ONLY:
"PASS" if tone is fully compliant
OR
"FAIL: [specific issue]" if tone violates requirements

Do NOT provide explanations beyond the specific issue.
"""
        
        response = self.claude.messages.create(
            model="claude-sonnet-3-5-20241022",
            max_tokens=100,
            temperature=0.0,  # Deterministic
            messages=[{"role": "user", "content": prompt}]
        )
        
        result = response.content[0].text.strip()
        
        if result.startswith("FAIL"):
            return [result]
        return []
    
    def _check_factual_consistency(self, 
                                   nudge_text: str, 
                                   player_context: dict) -> list[str]:
        """Ensure nudge doesn't hallucinate facts not in player_context."""
        
        violations = []
        
        # Check for dollar amounts (shouldn't appear at all)
        dollar_matches = re.findall(r'\$[\d,]+', nudge_text)
        if dollar_matches:
            violations.append(
                f"Specific dollar amounts mentioned: {dollar_matches}"
            )
        
        # Check for timeframes that don't match context
        if '24 hours' in nudge_text and 'timeout_duration' not in player_context:
            violations.append("Mentions '24 hours' without context data")
        
        return violations
```

---

## Cost Optimization Strategies

### 1. Caching Explanations
```python
from functools import lru_cache
from datetime import datetime, timedelta

class CachedSemanticAuditor(BehavioralSemanticAuditor):
    def __init__(self, api_key: str, cache_ttl_seconds: int = 3600):
        super().__init__(api_key)
        self.cache_ttl = cache_ttl_seconds
        self._cache = {}
    
    def generate_risk_explanation(self, player_data: dict) -> dict:
        # Create cache key from player_id + risk_score (rounded)
        cache_key = (
            player_data['player_id'],
            round(player_data['composite_risk_score'], 2)
        )
        
        # Check cache
        if cache_key in self._cache:
            cached_result, timestamp = self._cache[cache_key]
            if (datetime.now() - timestamp).seconds < self.cache_ttl:
                return cached_result
        
        # Generate fresh result
        result = super().generate_risk_explanation(player_data)
        
        # Cache it
        self._cache[cache_key] = (result, datetime.now())
        
        return result
```

### 2. Batch Processing
```python
def process_intervention_queue_batch(player_ids: list[str]) -> list[dict]:
    """
    Process 100 players at once instead of real-time per player.
    
    Reduces API calls from 100 to 1 by batching explanations.
    """
    
    # Fetch all player data in one query
    players = fetch_player_risk_data(player_ids)  # Single DB query
    
    # Generate explanations for all at once
    auditor = BehavioralSemanticAuditor(api_key=os.getenv('ANTHROPIC_API_KEY'))
    
    results = []
    for player in players:
        explanation = auditor.generate_risk_explanation(player)
        results.append({
            'player_id': player['player_id'],
            'explanation': explanation
        })
    
    return results
```

### 3. Model Selection
```python
# Use Haiku for simple classifications
SIMPLE_CLASSIFICATION_MODEL = "claude-haiku-3-5-20241022"

# Use Sonnet for detailed explanations
DETAILED_EXPLANATION_MODEL = "claude-sonnet-3-5-20241022"

def classify_risk_category(composite_score: float) -> str:
    """Simple classification doesn't need Sonnet."""
    
    client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
    
    response = client.messages.create(
        model=SIMPLE_CLASSIFICATION_MODEL,  # Haiku is cheaper
        max_tokens=50,
        messages=[{
            "role": "user",
            "content": f"Risk score {composite_score}. Respond with only: CRITICAL, HIGH, MEDIUM, or LOW"
        }]
    )
    
    return response.content[0].text.strip()
```

---

## Monitoring & Observability
```sql
-- Create monitoring table
CREATE TABLE PROD.LLM_GENERATION_LOG (
    generation_id VARCHAR(50) PRIMARY KEY,
    player_id VARCHAR(50),
    model VARCHAR(50),
    input_tokens INT,
    output_tokens INT,
    cost_usd DECIMAL(10,6),
    validation_passed BOOLEAN,
    violation_types ARRAY,
    generation_timestamp TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- Daily cost monitoring view
CREATE VIEW ANALYTICS.LLM_DAILY_COSTS AS
SELECT
    DATE_TRUNC('day', generation_timestamp) AS date,
    COUNT(*) AS total_generations,
    SUM(input_tokens * 0.000003 + output_tokens * 0.000015) AS estimated_cost_usd,
    SUM(CASE WHEN validation_passed THEN 0 ELSE 1 END)::FLOAT / COUNT(*) AS violation_rate
FROM PROD.LLM_GENERATION_LOG
GROUP BY 1;

-- Alert if daily costs exceed threshold
CREATE TASK MONITOR_LLM_COSTS
  SCHEDULE = 'USING CRON 0 9 * * * America/New_York'  -- 9 AM daily
AS
  CALL SYSTEM$SEND_ALERT_IF(
    'llm_cost_alert',
    (SELECT estimated_cost_usd FROM ANALYTICS.LLM_DAILY_COSTS 
     WHERE date = CURRENT_DATE()) > 50,
    'LLM costs exceeded $50 for today'
  );
```

---

## Error Handling
```python
from tenacity import retry, stop_after_attempt, wait_exponential

class BehavioralSemanticAuditor:
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def generate_risk_explanation(self, player_data: dict) -> dict:
        """Auto-retry with exponential backoff on API failures."""
        try:
            # [API call implementation]
            pass
        except Exception as e:
            # Log error
            logger.error(f"LLM generation failed for {player_data['player_id']}: {e}")
            
            # Re-raise to trigger retry
            raise
```

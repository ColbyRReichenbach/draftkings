# Skill: LLM Integration

Patterns for Claude API integration in DK Sentinel.

## Core Pattern: Semantic Auditor
```python
from anthropic import Anthropic

class BehavioralSemanticAuditor:
    def __init__(self, api_key: str):
        self.client = Anthropic(api_key=api_key)
    
    def generate_risk_explanation(self, player_data: dict) -> dict:
        prompt = f'''
        Analyze risk profile:
        Player: {player_data['player_id']}
        Risk Score: {player_data['composite_risk_score']:.2f}
        
        Provide JSON:
        {{
            "risk_verdict": "CRITICAL | HIGH | MEDIUM | LOW",
            "explanation": "2-3 sentence WHY",
            "key_evidence": ["E1", "E2", "E3"],
            "recommended_action": "Specific intervention",
            "draft_customer_nudge": "Supportive message"
        }}
        '''
        
        response = self.client.messages.create(
            model="claude-sonnet-3-5-20241022",
            max_tokens=1500,
            temperature=0.3,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return self._parse_json(response.content[0].text)
```

## Safety Validation
```python
class LLMSafetyValidator:
    PROHIBITED = [
        r'\b(irresponsible|addicted)\b',
        r'\b(must|required)\b'
    ]
    
    def validate_nudge(self, text: str) -> tuple[bool, list]:
        violations = []
        
        # Check prohibited phrases
        for pattern in self.PROHIBITED:
            if re.search(pattern, text, re.I):
                violations.append(f"Prohibited: {pattern}")
        
        # Check required elements
        if 'Responsible Gaming' not in text:
            violations.append("Missing RG Center link")
        
        return len(violations) == 0, violations
```

## Cost Optimization
- Cache explanations (1-hour TTL)
- Batch process 100 players at once
- Use Haiku for simple classifications
- Monitor daily costs (<$50 threshold)

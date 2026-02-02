# Skill: Compliance Validation

Regulatory requirements for responsible gaming.

## Customer Nudge Checklist
✅ Supportive, non-judgmental tone
✅ No medical/clinical language
✅ No threats or coercion
✅ Includes RG Center link
✅ Emphasizes player choice
✅ No specific dollar amounts
✅ Resources/support info

## State-Specific Thresholds

**Massachusetts (205 CMR 238.04)**:
- Trigger: Bet >10x rolling avg OR deposit >$5K after >$10K loss
- Action: Internal documentation

**New Jersey**:
- Trigger: 3+ high-risk flags in 30 days
- Action: Mandatory timeout

**Pennsylvania**:
- Trigger: 3+ self-exclusion reversals in 6 months
- Action: Problem Gambling Council referral

## Prohibited Language
```python
PROHIBITED = [
    r'\b(irresponsible|reckless|addicted)\b',
    r'\b(must|required|mandatory)\b',
    r'\$\d{4,}'  # Specific amounts
]
```

## Audit Trail Requirements
Every AI flag must log:
- analyst_id (who reviewed)
- timestamp (when reviewed)
- analyst_action (approved/escalated/dismissed)
- analyst_notes (rationale)
- state_jurisdiction (MA/NJ/PA)

# Business Logic Reference

## Risk Score Calculation

### Composite Formula
```
composite_risk_score = 
    loss_chase_score * 0.30 +
    bet_escalation_score * 0.25 +
    market_drift_score * 0.15 +
    temporal_risk_score * 0.10 +
    gamalyze_risk_score * 0.20
```

### Weight Rationale
- Loss Chasing (0.30): 68% of self-excluded players showed this
- Bet Escalation (0.25): r=0.72 correlation with Gamalyze
- Market Drift (0.15): Moderate predictor
- Temporal (0.10): High variance (shift workers)
- Gamalyze (0.20): External validation

### Risk Categories
- CRITICAL (≥0.75): Immediate intervention
- HIGH (0.50-0.74): Review within 4 hours
- MEDIUM (0.30-0.49): Monitor next 48 hours
- LOW (<0.30): Routine monitoring

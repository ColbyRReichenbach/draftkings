# Data Dictionary

## Raw Tables

### RAW.BET_LOGS
- bet_id (VARCHAR): Unique identifier
- player_id (VARCHAR): Format PLR_####_ST
- bet_timestamp (TIMESTAMP_NTZ): UTC
- bet_amount (DECIMAL): USD
- sport_category (VARCHAR): NFL, NBA, etc.
- outcome (VARCHAR): win, loss, pending, void
- payout_amount (DECIMAL): USD

### RAW.GAMALYZE_SCORES
- assessment_id (VARCHAR): Unique ID
- player_id (VARCHAR): Player identifier
- assessment_date (DATE): When assessed
- sensitivity_to_reward (DECIMAL): 0-100
- sensitivity_to_loss (DECIMAL): 0-100 (PRIMARY)
- risk_tolerance_score (DECIMAL): 0-100
- decision_consistency (DECIMAL): 0-100

## Intermediate Tables

### INT_LOSS_CHASING_INDICATORS
- player_id: Player identifier
- bet_after_loss_ratio: % of bets after losses
- bet_escalation_ratio: Size multiplier after losses

## Marts

### PROD.RG_RISK_SCORES
- player_id: Player identifier
- composite_risk_score: Final score (0-1)
- risk_category: CRITICAL/HIGH/MEDIUM/LOW
- All component scores

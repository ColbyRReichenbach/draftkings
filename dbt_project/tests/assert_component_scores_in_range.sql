-- Ensure component scores are within 0-1 bounds

SELECT
    player_id,
    loss_chase_score,
    bet_escalation_score,
    market_drift_score,
    temporal_risk_score,
    gamalyze_risk_score,
    composite_risk_score
FROM {{ ref('rg_risk_scores') }}
WHERE loss_chase_score < 0 OR loss_chase_score > 1
   OR bet_escalation_score < 0 OR bet_escalation_score > 1
   OR market_drift_score < 0 OR market_drift_score > 1
   OR temporal_risk_score < 0 OR temporal_risk_score > 1
   OR gamalyze_risk_score < 0 OR gamalyze_risk_score > 1
   OR composite_risk_score < 0 OR composite_risk_score > 1

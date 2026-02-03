-- Ensure risk categories align with composite score thresholds

SELECT
    player_id,
    composite_risk_score,
    risk_category
FROM {{ ref('rg_risk_scores') }}
WHERE (
    composite_risk_score >= 0.80 AND risk_category != 'CRITICAL'
) OR (
    composite_risk_score >= 0.60 AND composite_risk_score < 0.80 AND risk_category != 'HIGH'
) OR (
    composite_risk_score >= 0.40 AND composite_risk_score < 0.60 AND risk_category != 'MEDIUM'
) OR (
    composite_risk_score < 0.40 AND risk_category != 'LOW'
)

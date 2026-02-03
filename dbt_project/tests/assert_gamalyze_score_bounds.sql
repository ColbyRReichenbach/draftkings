-- Ensure Gamalyze composite score is within expected bounds

SELECT
    player_id,
    gamalyze_risk_score
FROM {{ ref('int_gamalyze_composite') }}
WHERE gamalyze_risk_score < 0
   OR gamalyze_risk_score > 1

-- Ensure market drift ratios remain within expected bounds

SELECT
    player_id,
    sport_diversity_ratio,
    tier_drop_pct,
    abnormal_hours_pct
FROM {{ ref('int_market_drift_indicators') }}
WHERE sport_diversity_ratio < 0
   OR sport_diversity_ratio > 10
   OR tier_drop_pct < -1
   OR tier_drop_pct > 1
   OR abnormal_hours_pct < 0
   OR abnormal_hours_pct > 1

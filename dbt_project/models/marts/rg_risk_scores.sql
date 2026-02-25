{{
  config(
    materialized='table',
    tags=['rg_scores', 'marts']
  )
}}

/*
  Marts model: composite responsible gaming risk scores.

  Component inputs:
  - int_loss_chasing_indicators
  - int_market_drift_indicators
  - int_gamalyze_composite

  Business Logic:
  - Component normalization thresholds from docs/ANALYST_PLAYBOOK.md
  - Weights (v1.0): loss_chase 0.30, bet_escalation 0.25, market_drift 0.15,
    temporal_risk 0.10, gamalyze 0.20
  - Missing components imputed with population median
  - Exclude players with all components missing
*/

WITH component_scores AS (
    SELECT
        p.player_id,
        lc.bet_after_loss_ratio,
        lc.bet_escalation_ratio,
        md.sport_diversity_ratio,
        md.tier_drop_pct,
        md.abnormal_hours_pct,
        g.gamalyze_risk_score,
        {{ normalize_score('lc.bet_after_loss_ratio', 0.40, 0.75) }} AS loss_chase_score,
        {{ normalize_score('lc.bet_escalation_ratio', 1.2, 2.0) }} AS bet_escalation_score,
        {{ normalize_score('md.sport_diversity_ratio', 1.5, 3.0) }} AS horizontal_drift_score,
        {{ normalize_score('md.tier_drop_pct', 0.30, 0.60) }} AS vertical_drift_score,
        {{ normalize_score('md.abnormal_hours_pct', 0.20, 0.50) }} AS temporal_drift_score
    FROM {{ ref('stg_player_profiles') }} p
    LEFT JOIN {{ ref('int_loss_chasing_indicators') }} lc
        ON p.player_id = lc.player_id
    LEFT JOIN {{ ref('int_market_drift_indicators') }} md
        ON p.player_id = md.player_id
    LEFT JOIN {{ ref('int_gamalyze_composite') }} g
        ON p.player_id = g.player_id
),

market_drift AS (
    SELECT
        *,
        (horizontal_drift_score * 0.33) +
        (vertical_drift_score * 0.33) +
        (temporal_drift_score * 0.33) AS market_drift_score,
        temporal_drift_score AS temporal_risk_score
    FROM component_scores
),

component_medians AS (
    SELECT
        percentile_cont(0.5) WITHIN GROUP (ORDER BY loss_chase_score) AS loss_chase_median,
        percentile_cont(0.5) WITHIN GROUP (ORDER BY bet_escalation_score) AS bet_escalation_median,
        percentile_cont(0.5) WITHIN GROUP (ORDER BY market_drift_score) AS market_drift_median,
        percentile_cont(0.5) WITHIN GROUP (ORDER BY temporal_risk_score) AS temporal_risk_median,
        percentile_cont(0.5) WITHIN GROUP (ORDER BY gamalyze_risk_score) AS gamalyze_median
    FROM market_drift
),

imputed AS (
    SELECT
        m.player_id,
        COALESCE(m.loss_chase_score, cm.loss_chase_median) AS loss_chase_score,
        COALESCE(m.bet_escalation_score, cm.bet_escalation_median) AS bet_escalation_score,
        COALESCE(m.market_drift_score, cm.market_drift_median) AS market_drift_score,
        COALESCE(m.temporal_risk_score, cm.temporal_risk_median) AS temporal_risk_score,
        COALESCE(m.gamalyze_risk_score, cm.gamalyze_median) AS gamalyze_risk_score
    FROM market_drift m
    CROSS JOIN component_medians cm
),

composite AS (
    SELECT
        player_id,
        loss_chase_score,
        bet_escalation_score,
        market_drift_score,
        temporal_risk_score,
        gamalyze_risk_score,
        (
            (loss_chase_score * 0.30) +
            (bet_escalation_score * 0.25) +
            (market_drift_score * 0.15) +
            (temporal_risk_score * 0.10) +
            (gamalyze_risk_score * 0.20)
        ) AS composite_risk_score,
        CURRENT_TIMESTAMP AS calculated_at
    FROM imputed
),

final AS (
    SELECT
        *,
        CASE
            WHEN composite_risk_score >= 0.80 THEN 'CRITICAL'
            WHEN composite_risk_score >= 0.60 THEN 'HIGH'
            WHEN composite_risk_score >= 0.40 THEN 'MEDIUM'
            ELSE 'LOW'
        END AS risk_category
    FROM composite
)

SELECT
    player_id,
    loss_chase_score,
    bet_escalation_score,
    market_drift_score,
    temporal_risk_score,
    gamalyze_risk_score,
    composite_risk_score,
    risk_category,
    calculated_at
FROM final
WHERE NOT (
    loss_chase_score IS NULL AND
    bet_escalation_score IS NULL AND
    market_drift_score IS NULL AND
    temporal_risk_score IS NULL AND
    gamalyze_risk_score IS NULL
)

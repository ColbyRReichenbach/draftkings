{{
  config(
    materialized='table',
    tags=['rg_queue', 'marts']
  )
}}

/*
  Marts model: analyst intervention queue.

  Business Logic:
  - Include HIGH and CRITICAL risk categories
  - Provide key drivers for analyst review
  - Prioritize by risk score (descending) and recency
*/

WITH base AS (
    SELECT
        r.player_id,
        r.composite_risk_score,
        r.risk_category,
        r.loss_chase_score,
        r.bet_escalation_score,
        r.market_drift_score,
        r.temporal_risk_score,
        r.gamalyze_risk_score,
        r.calculated_at
    FROM {{ ref('rg_risk_scores') }} r
    WHERE r.risk_category IN ('HIGH', 'CRITICAL')
),

drivers AS (
    SELECT
        *,
        CASE
            WHEN loss_chase_score >= GREATEST(bet_escalation_score, market_drift_score, temporal_risk_score, gamalyze_risk_score)
                THEN 'LOSS_CHASE'
            WHEN bet_escalation_score >= GREATEST(loss_chase_score, market_drift_score, temporal_risk_score, gamalyze_risk_score)
                THEN 'BET_ESCALATION'
            WHEN market_drift_score >= GREATEST(loss_chase_score, bet_escalation_score, temporal_risk_score, gamalyze_risk_score)
                THEN 'MARKET_DRIFT'
            WHEN temporal_risk_score >= GREATEST(loss_chase_score, bet_escalation_score, market_drift_score, gamalyze_risk_score)
                THEN 'TEMPORAL_RISK'
            ELSE 'GAMALYZE'
        END AS primary_driver
    FROM base
)

SELECT
    player_id,
    composite_risk_score,
    risk_category,
    primary_driver,
    loss_chase_score,
    bet_escalation_score,
    market_drift_score,
    temporal_risk_score,
    gamalyze_risk_score,
    calculated_at
FROM drivers
ORDER BY
    composite_risk_score DESC,
    calculated_at DESC

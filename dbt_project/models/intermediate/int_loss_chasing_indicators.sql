{{
  config(
    materialized='incremental',
    unique_key='player_id',
    on_schema_change='fail',
    tags=['behavioral_analytics', 'loss_chasing'],
    cluster_by=['player_id']
  )
}}

/*
  Intermediate model: loss-chasing behavioral indicators.

  Business Logic:
  - bet_after_loss_ratio = bets_after_loss / total_bets
  - bet_escalation_ratio = avg_bet_after_loss / avg_bet_after_win
  - Exclude players with <2 bets in 7-day window
  - Cap bet_escalation_ratio at 10.0 (outlier handling)

  Window: rolling 7 days by bet_timestamp
  Grain: one row per player
*/

WITH base_bets AS (
    SELECT
        bet_id,
        player_id,
        bet_timestamp,
        bet_amount,
        outcome
    FROM {{ ref('stg_bet_logs') }}
    WHERE bet_timestamp >= {{ dbt.dateadd('day', -7, 'CURRENT_DATE') }}

    {% if is_incremental() %}
      AND bet_timestamp >= (
          SELECT {{ dbt.dateadd('day', -7, 'MAX(last_bet_timestamp)') }}
          FROM {{ this }}
      )
    {% endif %}
),

sequenced AS (
    SELECT
        bet_id,
        player_id,
        bet_timestamp,
        bet_amount,
        outcome,
        LAG(outcome) OVER (
            PARTITION BY player_id
            ORDER BY bet_timestamp, bet_id
        ) AS prev_outcome
    FROM base_bets
),

classified AS (
    SELECT
        bet_id,
        player_id,
        bet_timestamp,
        bet_amount,
        outcome,
        prev_outcome,
        CASE WHEN prev_outcome = 'loss' THEN 1 ELSE 0 END AS is_after_loss,
        CASE WHEN prev_outcome = 'win' THEN 1 ELSE 0 END AS is_after_win
    FROM sequenced
),

player_aggs AS (
    SELECT
        player_id,
        COUNT(*) AS total_bets,
        COUNT(*) FILTER (WHERE is_after_loss = 1) AS bets_after_loss,
        AVG(bet_amount) FILTER (WHERE is_after_loss = 1) AS avg_bet_after_loss,
        AVG(bet_amount) FILTER (WHERE is_after_win = 1) AS avg_bet_after_win,
        MAX(bet_timestamp) AS last_bet_timestamp
    FROM classified
    GROUP BY player_id
),

final AS (
    SELECT
        player_id,
        total_bets,
        bets_after_loss,
        avg_bet_after_loss,
        avg_bet_after_win,
        CASE
            WHEN total_bets = 0 THEN 0.0
            ELSE bets_after_loss::FLOAT / NULLIF(total_bets, 0)
        END AS bet_after_loss_ratio,
        CASE
            WHEN COALESCE(avg_bet_after_win, 0) = 0 THEN 0.0
            ELSE avg_bet_after_loss / NULLIF(avg_bet_after_win, 0)
        END AS bet_escalation_ratio_raw,
        last_bet_timestamp,
        CURRENT_TIMESTAMP AS calculated_at
    FROM player_aggs
)

SELECT
    player_id,
    total_bets,
    bets_after_loss,
    avg_bet_after_loss,
    avg_bet_after_win,
    bet_after_loss_ratio,
    LEAST(bet_escalation_ratio_raw, 10.0) AS bet_escalation_ratio,
    last_bet_timestamp,
    calculated_at
FROM final
WHERE total_bets >= 2

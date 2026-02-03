{{
  config(
    materialized='incremental',
    unique_key='player_id',
    on_schema_change='fail',
    tags=['behavioral_analytics', 'market_drift'],
    cluster_by=['player_id']
  )
}}

/*
  Intermediate model: market drift behavioral indicators.

  Business Logic:
  - Current window: 7 days
  - Baseline window: 90 days
  - sport_diversity_ratio = unique_sports_7d / baseline_unique_sports_90d
  - tier_drop_pct = (baseline_avg_tier_90d - current_avg_tier_7d) / baseline_avg_tier_90d
  - abnormal_hours_pct = bets_2am_to_6am / total_bets_7d

  Grain: one row per player
*/

WITH base_bets AS (
    SELECT
        bet_id,
        player_id,
        bet_timestamp,
        sport_category,
        bet_amount,
        outcome
    FROM {{ ref('stg_bet_logs') }}
    WHERE bet_timestamp >= {{ dbt.dateadd('day', -90, 'CURRENT_DATE') }}

    {% if is_incremental() %}
      AND bet_timestamp >= (
          SELECT {{ dbt.dateadd('day', -90, 'MAX(last_bet_timestamp)') }}
          FROM {{ this }}
      )
    {% endif %}
),

classified AS (
    SELECT
        bet_id,
        player_id,
        bet_timestamp,
        sport_category,
        CASE
            WHEN sport_category IN ('NFL', 'NBA', 'MLB', 'NHL', 'SOCCER_EPL') THEN 1.0
            WHEN sport_category IN ('NCAA_BASKETBALL', 'NCAA_FOOTBALL') THEN 0.7
            WHEN sport_category IN ('MMA', 'BOXING', 'TENNIS') THEN 0.5
            WHEN sport_category IN ('TABLE_TENNIS', 'KOREAN_BASEBALL', 'ESPORTS', 'DARTS') THEN 0.2
            ELSE 0.5
        END AS market_tier,
        EXTRACT('hour' FROM bet_timestamp) AS bet_hour
    FROM base_bets
),

windowed AS (
    SELECT
        *,
        CASE
            WHEN bet_timestamp >= {{ dbt.dateadd('day', -7, 'CURRENT_DATE') }} THEN 1
            ELSE 0
        END AS is_current_7d
    FROM classified
),

player_aggs AS (
    SELECT
        player_id,
        COUNT(*) FILTER (WHERE is_current_7d = 1) AS total_bets_7d,
        COUNT(*) FILTER (
            WHERE is_current_7d = 1
              AND bet_hour >= 2
              AND bet_hour < 6
        ) AS abnormal_hours_bets_7d,
        COUNT(DISTINCT sport_category) FILTER (WHERE is_current_7d = 1) AS unique_sports_7d,
        COUNT(DISTINCT sport_category) AS baseline_unique_sports_90d,
        AVG(market_tier) FILTER (WHERE is_current_7d = 1) AS current_avg_tier_7d,
        AVG(market_tier) AS baseline_avg_tier_90d,
        MAX(bet_timestamp) AS last_bet_timestamp
    FROM windowed
    GROUP BY player_id
),

final AS (
    SELECT
        player_id,
        total_bets_7d,
        abnormal_hours_bets_7d,
        unique_sports_7d,
        baseline_unique_sports_90d,
        current_avg_tier_7d,
        baseline_avg_tier_90d,
        CASE
            WHEN COALESCE(baseline_unique_sports_90d, 0) = 0 THEN 0.0
            ELSE unique_sports_7d::FLOAT / NULLIF(baseline_unique_sports_90d, 0)
        END AS sport_diversity_ratio,
        CASE
            WHEN COALESCE(baseline_avg_tier_90d, 0) = 0 THEN 0.0
            WHEN current_avg_tier_7d IS NULL THEN 0.0
            ELSE (baseline_avg_tier_90d - current_avg_tier_7d) / NULLIF(baseline_avg_tier_90d, 0)
        END AS tier_drop_pct,
        CASE
            WHEN COALESCE(total_bets_7d, 0) = 0 THEN 0.0
            ELSE abnormal_hours_bets_7d::FLOAT / NULLIF(total_bets_7d, 0)
        END AS abnormal_hours_pct,
        last_bet_timestamp,
        CURRENT_TIMESTAMP AS calculated_at
    FROM player_aggs
)

SELECT
    player_id,
    total_bets_7d,
    abnormal_hours_bets_7d,
    unique_sports_7d,
    baseline_unique_sports_90d,
    current_avg_tier_7d,
    baseline_avg_tier_90d,
    sport_diversity_ratio,
    tier_drop_pct,
    abnormal_hours_pct,
    last_bet_timestamp,
    calculated_at
FROM final

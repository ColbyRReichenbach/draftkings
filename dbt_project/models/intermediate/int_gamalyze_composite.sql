{{
  config(
    materialized='incremental',
    unique_key='player_id',
    on_schema_change='fail',
    tags=['behavioral_analytics', 'gamalyze'],
    cluster_by=['player_id']
  )
}}

/*
  Intermediate model: Gamalyze composite risk score.

  Business Logic:
  - Use most recent assessment in last 90 days
  - If no assessment in 90 days, default each component to 50
  - gamalyze_risk_score =
      (sensitivity_to_loss/100)*0.40 +
      (sensitivity_to_reward/100)*0.25 +
      (risk_tolerance/100)*0.25 +
      ((100 - decision_consistency)/100)*0.10

  Grain: one row per player
*/

WITH players AS (
    SELECT player_id
    FROM {{ ref('stg_player_profiles') }}
),

base_assessments AS (
    SELECT
        assessment_id,
        player_id,
        assessment_date,
        sensitivity_to_loss,
        sensitivity_to_reward,
        risk_tolerance,
        decision_consistency,
        gamalyze_version
    FROM {{ ref('stg_gamalyze_scores') }}
    WHERE assessment_date >= {{ dbt.dateadd('day', -90, 'CURRENT_DATE') }}

    {% if is_incremental() %}
      AND assessment_date >= (
          SELECT MAX(last_assessment_date) FROM {{ this }}
      )
    {% endif %}
),

latest_assessment AS (
    SELECT
        assessment_id,
        player_id,
        assessment_date,
        sensitivity_to_loss,
        sensitivity_to_reward,
        risk_tolerance,
        decision_consistency,
        gamalyze_version,
        ROW_NUMBER() OVER (
            PARTITION BY player_id
            ORDER BY assessment_date DESC, assessment_id DESC
        ) AS rn
    FROM base_assessments
),

current_scores AS (
    SELECT
        p.player_id,
        la.assessment_id,
        la.assessment_date AS last_assessment_date,
        COALESCE(la.sensitivity_to_loss, 50) AS sensitivity_to_loss,
        COALESCE(la.sensitivity_to_reward, 50) AS sensitivity_to_reward,
        COALESCE(la.risk_tolerance, 50) AS risk_tolerance,
        COALESCE(la.decision_consistency, 50) AS decision_consistency,
        la.gamalyze_version
    FROM players p
    LEFT JOIN latest_assessment la
      ON p.player_id = la.player_id
     AND la.rn = 1
),

updated_player_ids AS (
    {% if is_incremental() %}
    SELECT DISTINCT player_id
    FROM base_assessments

    UNION

    SELECT player_id
    FROM {{ this }}
    WHERE last_assessment_date < {{ dbt.dateadd('day', -90, 'CURRENT_DATE') }}
    {% else %}
    SELECT player_id FROM players
    {% endif %}
),

final AS (
    {% if is_incremental() %}
    SELECT
        cs.player_id,
        cs.assessment_id,
        cs.last_assessment_date,
        cs.sensitivity_to_loss,
        cs.sensitivity_to_reward,
        cs.risk_tolerance,
        cs.decision_consistency,
        cs.gamalyze_version,
        (
            (cs.sensitivity_to_loss / 100.0) * 0.40 +
            (cs.sensitivity_to_reward / 100.0) * 0.25 +
            (cs.risk_tolerance / 100.0) * 0.25 +
            ((100.0 - cs.decision_consistency) / 100.0) * 0.10
        ) AS gamalyze_risk_score,
        CURRENT_TIMESTAMP AS calculated_at
    FROM current_scores cs
    WHERE cs.player_id IN (SELECT player_id FROM updated_player_ids)

    UNION ALL

    SELECT
        player_id,
        assessment_id,
        last_assessment_date,
        sensitivity_to_loss,
        sensitivity_to_reward,
        risk_tolerance,
        decision_consistency,
        gamalyze_version,
        gamalyze_risk_score,
        calculated_at
    FROM {{ this }}
    WHERE player_id NOT IN (SELECT player_id FROM updated_player_ids)
    {% else %}
    SELECT
        cs.player_id,
        cs.assessment_id,
        cs.last_assessment_date,
        cs.sensitivity_to_loss,
        cs.sensitivity_to_reward,
        cs.risk_tolerance,
        cs.decision_consistency,
        cs.gamalyze_version,
        (
            (cs.sensitivity_to_loss / 100.0) * 0.40 +
            (cs.sensitivity_to_reward / 100.0) * 0.25 +
            (cs.risk_tolerance / 100.0) * 0.25 +
            ((100.0 - cs.decision_consistency) / 100.0) * 0.10
        ) AS gamalyze_risk_score,
        CURRENT_TIMESTAMP AS calculated_at
    FROM current_scores cs
    {% endif %}
)

SELECT
    player_id,
    assessment_id,
    last_assessment_date,
    sensitivity_to_loss,
    sensitivity_to_reward,
    risk_tolerance,
    decision_consistency,
    gamalyze_version,
    gamalyze_risk_score,
    calculated_at
FROM final

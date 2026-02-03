{{
  config(
    materialized='view',
    contract={'enforced': true}
  )
}}

/*
  Staging model for Gamalyze neuro-marker assessments.

  Data Quality Rules:
  - All assessments must have valid assessment_id AND player_id
  - Score columns cast to DECIMAL(5,2) for consistent precision
  - All scores expected to be in 0-100 range

  Source: raw.gamalyze_assessments
*/

WITH source AS (
    SELECT * FROM {{ source('raw', 'gamalyze_assessments') }}
),

cleaned AS (
    SELECT
        assessment_id,
        player_id,
        assessment_date,
        CAST(sensitivity_to_loss AS DECIMAL(5,2)) AS sensitivity_to_loss,
        CAST(sensitivity_to_reward AS DECIMAL(5,2)) AS sensitivity_to_reward,
        CAST(risk_tolerance AS DECIMAL(5,2)) AS risk_tolerance,
        CAST(decision_consistency AS DECIMAL(5,2)) AS decision_consistency,
        gamalyze_version
    FROM source
    WHERE assessment_id IS NOT NULL
      AND player_id IS NOT NULL
)

SELECT * FROM cleaned

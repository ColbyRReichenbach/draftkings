{{
  config(
    materialized='view',
    contract={'enforced': true}
  )
}}

/*
  Staging model for raw player accounts.

  Data Quality Rules:
  - All players must have a valid player_id (player_id IS NOT NULL)
  - State jurisdictions standardized to uppercase and trimmed
  - Risk cohorts standardized to uppercase and trimmed
  - Numeric fields cast for consistent precision

  Source: raw.player_accounts
*/

WITH source AS (
    SELECT * FROM {{ source('raw', 'player_accounts') }}
),

cleaned AS (
    SELECT
        player_id,
        first_name,
        last_name,
        email,
        CAST(age AS INTEGER) AS age,
        UPPER(TRIM(state)) AS state_jurisdiction,
        UPPER(TRIM(risk_cohort)) AS risk_cohort
    FROM source
    WHERE player_id IS NOT NULL
)

SELECT * FROM cleaned

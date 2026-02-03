{{
  config(
    materialized='view',
    contract={'enforced': true}
  )
}}

/*
  Staging model for raw bet transactions.

  Data Quality Rules:
  - All bets must have a valid timestamp (bet_timestamp IS NOT NULL)
  - Bet amounts must be positive (bet_amount > 0)
  - Sport categories standardized to uppercase and trimmed
  - Bet amounts cast to decimal for consistent precision

  Source: raw.bet_transactions
*/

WITH source AS (
    SELECT * FROM {{ source('raw', 'bet_transactions') }}
),

cleaned AS (
    SELECT
        bet_id,
        player_id,
        bet_timestamp,
        UPPER(TRIM(sport_category)) AS sport_category,
        market_type,
        CAST(bet_amount AS DECIMAL(10,2)) AS bet_amount,
        odds_american,
        outcome
    FROM source
    WHERE bet_timestamp IS NOT NULL
      AND bet_amount > 0
)

SELECT * FROM cleaned

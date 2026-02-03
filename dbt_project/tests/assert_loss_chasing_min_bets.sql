-- Ensure model enforces minimum data requirement of 2 bets in window

SELECT
    player_id,
    total_bets
FROM {{ ref('int_loss_chasing_indicators') }}
WHERE total_bets < 2

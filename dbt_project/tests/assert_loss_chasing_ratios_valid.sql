-- Ensure loss-chasing ratios remain within expected bounds

SELECT
    player_id,
    bet_after_loss_ratio,
    bet_escalation_ratio
FROM {{ ref('int_loss_chasing_indicators') }}
WHERE bet_after_loss_ratio < 0
   OR bet_after_loss_ratio > 1
   OR bet_escalation_ratio < 0
   OR bet_escalation_ratio > 10

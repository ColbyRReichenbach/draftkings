-- Ensure composite risk weights sum to 1.0

WITH weight_check AS (
    SELECT
        (0.30 + 0.25 + 0.15 + 0.10 + 0.20) AS weight_sum
)
SELECT *
FROM weight_check
WHERE ROUND(weight_sum, 2) != 1.00

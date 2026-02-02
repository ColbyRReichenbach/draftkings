---
name: dbt-transformations
description: Best practices for dbt models in DK Sentinel - use when creating staging, intermediate, or marts models, or when asked about incremental materialization, data contracts, or Snowflake optimization
allowed-tools: Read, Bash, Grep
---

# dbt Transformations

## When to Use This Skill
- Creating any dbt model (staging, intermediate, marts)
- Implementing incremental processing
- Adding data quality tests
- Optimizing Snowflake queries
- Enforcing data contracts

---

## Core Pattern 1: Staging Model with Data Contract

**Purpose**: Ensure upstream schema changes don't silently break downstream models.
```sql
-- models/staging/stg_bet_logs.sql
{{
  config(
    materialized='view',
    contract={'enforced': true}
  )
}}

WITH source AS (
    SELECT * FROM {{ source('raw', 'bet_logs') }}
),

renamed AS (
    SELECT
        bet_id,
        player_id,
        bet_timestamp,
        bet_amount,
        UPPER(TRIM(sport_category)) AS sport_category,
        LOWER(outcome) AS outcome,
        payout_amount
    FROM source
    WHERE bet_timestamp IS NOT NULL
      AND player_id IS NOT NULL
      AND bet_amount > 0
)

SELECT * FROM renamed
```

**Schema Definition** (schema.yml):
```yaml
version: 2

models:
  - name: stg_bet_logs
    description: |
      Staging layer for raw bet logs with data contract enforcement.
      
      Data Quality Rules:
      - All bets must have timestamp and player_id
      - Bet amounts must be positive
      - Sport categories standardized to uppercase
    
    config:
      contract:
        enforced: true
    
    columns:
      - name: bet_id
        data_type: varchar(50)
        constraints:
          - type: not_null
          - type: unique
        tests:
          - not_null
          - unique
      
      - name: bet_amount
        data_type: decimal(10,2)
        constraints:
          - type: not_null
        tests:
          - not_null
          - dbt_utils.accepted_range:
              min_value: 0.01
              max_value: 10000
```

---

## Core Pattern 2: Incremental Intermediate Model

**Purpose**: Process only new/changed data for performance at scale.
```sql
-- models/intermediate/int_loss_chasing_indicators.sql
{{
  config(
    materialized='incremental',
    unique_key='player_id',
    on_schema_change='fail'
  )
}}

WITH player_bet_sequence AS (
    SELECT
        player_id,
        bet_timestamp,
        bet_amount,
        outcome,
        LAG(outcome) OVER (
            PARTITION BY player_id 
            ORDER BY bet_timestamp
        ) AS prev_outcome,
        LAG(bet_amount) OVER (
            PARTITION BY player_id 
            ORDER BY bet_timestamp
        ) AS prev_bet_amount
    FROM {{ ref('stg_bet_logs') }}
    
    {% if is_incremental() %}
    -- CRITICAL: Time predicate for performance
    WHERE bet_timestamp > (
        SELECT MAX(last_bet_timestamp) FROM {{ this }}
    )
    {% endif %}
)

SELECT
    player_id,
    COUNT(*) FILTER (WHERE prev_outcome = 'loss') AS bets_after_loss,
    COUNT(*) AS total_bets,
    AVG(bet_amount) FILTER (WHERE prev_outcome = 'loss') AS avg_bet_after_loss,
    AVG(bet_amount) FILTER (WHERE prev_outcome = 'win') AS avg_bet_after_win,
    MAX(bet_timestamp) AS last_bet_timestamp
FROM player_bet_sequence
GROUP BY player_id
```

---

## Snowflake Optimization

### Use QUALIFY for Window Functions
```sql
-- ❌ BAD: Requires subquery (two scans)
SELECT *
FROM (
    SELECT *, ROW_NUMBER() OVER (...) AS rn
    FROM {{ ref('stg_gamalyze_scores') }}
)
WHERE rn = 1

-- ✅ GOOD: QUALIFY is Snowflake-specific (one scan)
SELECT *
FROM {{ ref('stg_gamalyze_scores') }}
QUALIFY ROW_NUMBER() OVER (
    PARTITION BY player_id 
    ORDER BY assessment_date DESC
) = 1
```

### Cluster Keys for Large Tables
```sql
{{
  config(
    materialized='incremental',
    cluster_by=['player_id', "DATE_TRUNC('day', bet_timestamp)"]
  )
}}
```

**When to use**: Tables >1M rows frequently filtered/joined on specific columns.

---

## Testing Strategy

### Generic Tests (schema.yml)
```yaml
columns:
  - name: composite_risk_score
    tests:
      - not_null
      - dbt_utils.accepted_range:
          min_value: 0
          max_value: 1
```

### Singular Tests (tests/)
```sql
-- tests/assert_risk_weights_sum_to_one.sql
WITH weight_check AS (
    SELECT ROUND(0.30 + 0.25 + 0.15 + 0.10 + 0.20, 2) AS weight_sum
)
SELECT * FROM weight_check WHERE weight_sum != 1.00
```

---

## Common Mistakes

❌ **Forgetting incremental predicate** → Rescans entire table every run
✅ **Always include**: `WHERE bet_timestamp > (SELECT MAX(...) FROM {{ this }})`

❌ **Using SELECT *** → Scans all columns in columnar storage
✅ **Explicit columns only**: `SELECT player_id, bet_amount, ...`

❌ **Complex subqueries in WHERE** → Poor query optimization
✅ **Use JOINs instead**: `INNER JOIN {{ ref('...') }} ON ...`

---

## Quick Reference
```bash
# Run specific model
dbt run --models int_loss_chasing_indicators

# Run model + all upstream dependencies
dbt run --models +int_loss_chasing_indicators

# Full refresh incremental model
dbt run --models int_loss_chasing_indicators --full-refresh

# Test specific model
dbt test --select int_loss_chasing_indicators
```

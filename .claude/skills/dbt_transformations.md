# Skill: dbt Transformations

Core patterns for dbt models in DK Sentinel:

## Staging with Data Contract
```sql
{{ config(materialized='view', contract={'enforced': true}) }}

WITH source AS (SELECT * FROM {{ source('raw', 'bet_logs') }})
SELECT 
    bet_id,
    player_id,
    bet_timestamp,
    bet_amount
FROM source
```

## Incremental Intermediate
```sql
{{ config(materialized='incremental', unique_key='player_id') }}

SELECT player_id, COUNT(*) as bet_count
FROM {{ ref('stg_bet_logs') }}
{% if is_incremental() %}
WHERE bet_timestamp > (SELECT MAX(last_updated) FROM {{ this }})
{% endif %}
GROUP BY player_id
```

## Key Principles
- Always enforce data contracts on staging
- Use incremental for large intermediate tables
- Include time predicates in incremental blocks
- Test every model (not_null, unique, ranges)
- Document business logic in meta tags

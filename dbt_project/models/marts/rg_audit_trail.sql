{{
  config(
    materialized='incremental',
    unique_key='audit_id',
    on_schema_change='append_new_columns',
    tags=['compliance', 'audit_trail'],
    cluster_by=['player_id']
  )
}}

/*
  Marts model: audit trail foundation for RG compliance.

  Purpose:
  - Capture every risk score evaluation for HITL review
  - Provide required fields for MA/NJ/PA compliance
  - Serve as append-only audit log (7-year retention)

  Note:
  - Analyst fields are nullable until workflow integration is implemented.
*/

WITH base_scores AS (
    SELECT
        player_id,
        composite_risk_score,
        risk_category,
        calculated_at AS score_calculated_at
    FROM {{ ref('rg_risk_scores') }}

    {% if is_incremental() %}
      WHERE calculated_at > (SELECT MAX(score_calculated_at) FROM {{ this }})
    {% endif %}
),

jurisdictions AS (
    SELECT
        player_id,
        state_jurisdiction
    FROM {{ ref('stg_player_profiles') }}
),

final AS (
    SELECT
        CONCAT(bs.player_id, '_', CAST(bs.score_calculated_at AS VARCHAR)) AS audit_id,
        bs.player_id,
        bs.risk_category,
        bs.composite_risk_score,
        bs.score_calculated_at,
        j.state_jurisdiction,
        NULL::VARCHAR AS analyst_id,
        NULL::VARCHAR AS analyst_action,
        NULL::VARCHAR AS analyst_notes,
        NULL::BOOLEAN AS customer_notification_sent,
        NULL::VARCHAR AS intervention_type,
        NULL::INTEGER AS review_duration_seconds,
        CURRENT_TIMESTAMP AS created_at
    FROM base_scores bs
    LEFT JOIN jurisdictions j
      ON bs.player_id = j.player_id
)

SELECT * FROM final

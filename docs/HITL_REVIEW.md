# HITL Review (Completed)

## Purpose
- Demonstrate analyst triage, evidence evaluation, and documented decision-making for RG risk flags.
- Show regulatory awareness by state with explicit trigger checks where data permits.
- Provide an analyst-grade audit trail sample aligned to DraftKings Analyst II responsibilities.

## Review Window
- Date range reviewed: 2026-01-01 to 2026-03-31 (synthetic window)
- Data snapshot (dbt run timestamp): 2026-02-03
- Total queue size: 203
- Sample size: 15
- Risk categories included: CRITICAL, HIGH, MEDIUM

## Data Sources
- `prod.rg_intervention_queue` (queue + primary driver)
- `prod.rg_risk_scores` (composite + component scores)
- `prod.int_loss_chasing_indicators` (loss-chasing metrics)
- `prod.int_market_drift_indicators` (drift metrics)
- `prod.int_gamalyze_composite` (neuro-marker composite)
- `staging.stg_bet_logs` (recent bet timeline)

## Sample Design
- Stratified by risk tier: 5 CRITICAL, 5 HIGH, 5 MEDIUM
- State coverage: MA, NJ, PA
- Driver coverage prioritized where available

## Summary of Actions
| Action Type | Count |
|---|---|
| NO_ACTION | 1 |
| NUDGE | 3 |
| LIMITS | 2 |
| COOLING_OFF | 4 |
| HOLD/REFERRAL | 5 |

## Case Log (15 Total)
| Case ID | player_id | risk_category | primary_driver | state | analyst_action | intervention_type |
|---|---|---|---|---|---|---|
| 1 | PLR_6526_NJ | CRITICAL | LOSS_CHASE | NJ | ESCALATE | HOLD/REFERRAL |
| 2 | PLR_1955_PA | CRITICAL | LOSS_CHASE | PA | ESCALATE | HOLD/REFERRAL |
| 3 | PLR_5789_MA | CRITICAL | BET_ESCALATION | MA | ESCALATE | HOLD/REFERRAL |
| 4 | PLR_4762_PA | CRITICAL | BET_ESCALATION | PA | ESCALATE | HOLD/REFERRAL |
| 5 | PLR_0533_PA | CRITICAL | BET_ESCALATION | PA | ESCALATE | HOLD/REFERRAL |
| 6 | PLR_4560_MA | HIGH | LOSS_CHASE | MA | APPROVE | COOLING_OFF |
| 7 | PLR_9346_NJ | HIGH | LOSS_CHASE | NJ | APPROVE | LIMITS |
| 8 | PLR_9392_PA | HIGH | BET_ESCALATION | PA | APPROVE | COOLING_OFF |
| 9 | PLR_1465_NJ | HIGH | BET_ESCALATION | NJ | ESCALATE | COOLING_OFF |
| 10 | PLR_6779_NJ | HIGH | BET_ESCALATION | NJ | ESCALATE | COOLING_OFF |
| 11 | PLR_4847_MA | MEDIUM | GAMALYZE | MA | APPROVE | NUDGE |
| 12 | PLR_6316_NJ | MEDIUM | TEMPORAL_RISK | NJ | WATCHLIST | NO_ACTION |
| 13 | PLR_6293_PA | MEDIUM | LOSS_CHASE | PA | APPROVE | NUDGE |
| 14 | PLR_0519_NJ | MEDIUM | BET_ESCALATION | NJ | APPROVE | LIMITS |
| 15 | PLR_9523_NJ | MEDIUM | LOSS_CHASE | NJ | APPROVE | NUDGE |

## Case Details
### Case ID: 1
- player_id: PLR_6526_NJ
- state: NJ
- risk_category: CRITICAL
- primary_driver: LOSS_CHASE
- composite_risk_score: 0.883

**Evidence Snapshot**
- bet_after_loss_ratio: 0.809
- bet_escalation_ratio: 4.93
- sport_diversity_ratio: 1.00
- market_tier_drop_pct: 0.4%
- abnormal_hours_pct: 66.7%
- gamalyze_risk_score: 0.918
- recent_bet_timeline_summary (7d/30d): Last bet: 2026-03-31; 7d bets 11 ($5505.95); 30d bets 46 ($25093.30); Late-night 30d 71.7%

**Regulatory Check**
- State-specific triggers: NJ multi-flag (3+ HIGH/CRITICAL in 30d) triggered (flags_30d = 5).
- Notes: Requires analyst sign-off before intervention execution.

**Analyst Decision**
- analyst_action: ESCALATE
- intervention_type: HOLD/REFERRAL
- rationale (1-3 sentences): Loss‑chasing and escalation both exceed CRITICAL thresholds, late‑night concentration is extreme, and Gamalyze score is very high. Multiple independent signals reinforce a high‑risk pattern rather than a single‑metric anomaly.
- follow_up_plan: Apply hold per policy, confirm NJ multi-flag status in audit trail, re‑review in 7 days for post‑intervention behavior.

### Case ID: 2
- player_id: PLR_1955_PA
- state: PA
- risk_category: CRITICAL
- primary_driver: LOSS_CHASE
- composite_risk_score: 0.879

**Evidence Snapshot**
- bet_after_loss_ratio: 0.775
- bet_escalation_ratio: 4.78
- sport_diversity_ratio: 1.00
- market_tier_drop_pct: -0.0%
- abnormal_hours_pct: 77.1%
- gamalyze_risk_score: 0.898
- recent_bet_timeline_summary (7d/30d): Last bet: 2026-03-31; 7d bets 11 ($16425.10); 30d bets 38 ($58216.61); Late-night 30d 84.2%

**Regulatory Check**
- State-specific triggers: PA self-exclusion reversal trigger not evaluable (no exclusion events in current data).
- Notes: Would require account/exclusion event table to validate 3+ reversals in 6 months.

**Analyst Decision**
- analyst_action: ESCALATE
- intervention_type: HOLD/REFERRAL
- rationale (1-3 sentences): Loss‑chasing ratio exceeds CRITICAL threshold, escalation is extreme, and late‑night betting is very high with strong Gamalyze risk. Severity warrants immediate escalation despite missing PA exclusion event data.
- follow_up_plan: Place hold and refer to support, then reassess in 7 days; monitor bet size trend and late‑night activity.

### Case ID: 3
- player_id: PLR_5789_MA
- state: MA
- risk_category: CRITICAL
- primary_driver: BET_ESCALATION
- composite_risk_score: 0.844

**Evidence Snapshot**
- bet_after_loss_ratio: 0.738
- bet_escalation_ratio: 4.72
- sport_diversity_ratio: 1.00
- market_tier_drop_pct: -3.4%
- abnormal_hours_pct: 70.9%
- gamalyze_risk_score: 0.773
- recent_bet_timeline_summary (7d/30d): Last bet: 2026-03-31; 7d bets 10 ($14979.21); 30d bets 40 ($63237.26); Late-night 30d 72.5%

**Regulatory Check**
- State-specific triggers: MA abnormal-play trigger (10x rolling avg bet) not triggered (max multiple 1.44x).
- Notes: Continue monitoring for abnormal-play spikes.

**Analyst Decision**
- analyst_action: ESCALATE
- intervention_type: HOLD/REFERRAL
- rationale (1-3 sentences): Escalation ratio is far above critical, late‑night betting is severe, and loss‑chasing is near critical threshold. Despite no MA 10x trigger, the multi‑signal pattern justifies escalation.
- follow_up_plan: Apply hold and schedule review in 7 days; monitor for abnormal-play spikes and bet size variability.

### Case ID: 4
- player_id: PLR_4762_PA
- state: PA
- risk_category: CRITICAL
- primary_driver: BET_ESCALATION
- composite_risk_score: 0.853

**Evidence Snapshot**
- bet_after_loss_ratio: 0.744
- bet_escalation_ratio: 4.26
- sport_diversity_ratio: 1.00
- market_tier_drop_pct: 0.8%
- abnormal_hours_pct: 53.0%
- gamalyze_risk_score: 0.793
- recent_bet_timeline_summary (7d/30d): Last bet: 2026-03-31; 7d bets 12 ($6196.80); 30d bets 40 ($20680.77); Late-night 30d 52.5%

**Regulatory Check**
- State-specific triggers: PA self-exclusion reversal trigger not evaluable (no exclusion events in current data).
- Notes: Would require account/exclusion event table to validate 3+ reversals in 6 months.

**Analyst Decision**
- analyst_action: ESCALATE
- intervention_type: HOLD/REFERRAL
- rationale (1-3 sentences): Escalation ratio is critical and late‑night betting is elevated, with loss‑chasing near the critical band. The pattern supports immediate escalation.
- follow_up_plan: Place hold and refer to support; re‑evaluate in 7 days and verify if exclusion event data becomes available.

### Case ID: 5
- player_id: PLR_0533_PA
- state: PA
- risk_category: CRITICAL
- primary_driver: BET_ESCALATION
- composite_risk_score: 0.851

**Evidence Snapshot**
- bet_after_loss_ratio: 0.702
- bet_escalation_ratio: 4.76
- sport_diversity_ratio: 1.00
- market_tier_drop_pct: 0.9%
- abnormal_hours_pct: 69.5%
- gamalyze_risk_score: 0.963
- recent_bet_timeline_summary (7d/30d): Last bet: 2026-03-31; 7d bets 10 ($12446.41); 30d bets 47 ($84610.76); Late-night 30d 66.0%

**Regulatory Check**
- State-specific triggers: PA self-exclusion reversal trigger not evaluable (no exclusion events in current data).
- Notes: Would require account/exclusion event table to validate 3+ reversals in 6 months.

**Analyst Decision**
- analyst_action: ESCALATE
- intervention_type: HOLD/REFERRAL
- rationale (1-3 sentences): Escalation ratio and Gamalyze score are extremely high with persistent late‑night activity. Composite severity warrants immediate escalation despite unavailable PA exclusion event data.
- follow_up_plan: Hold and refer; re‑review in 7 days for bet size trend and late‑night frequency.

### Case ID: 6
- player_id: PLR_4560_MA
- state: MA
- risk_category: HIGH
- primary_driver: LOSS_CHASE
- composite_risk_score: 0.800

**Evidence Snapshot**
- bet_after_loss_ratio: 0.795
- bet_escalation_ratio: 4.82
- sport_diversity_ratio: 0.88
- market_tier_drop_pct: 0.3%
- abnormal_hours_pct: 74.2%
- gamalyze_risk_score: 0.500
- recent_bet_timeline_summary (7d/30d): Last bet: 2026-03-31; 7d bets 11 ($11410.06); 30d bets 42 ($57410.87); Late-night 30d 76.2%

**Regulatory Check**
- State-specific triggers: MA abnormal-play trigger (10x rolling avg bet) not triggered (max multiple 1.44x).
- Notes:

**Analyst Decision**
- analyst_action: APPROVE
- intervention_type: COOLING_OFF
- rationale (1-3 sentences): Loss‑chasing and escalation are critical‑level despite a HIGH category, and late‑night activity is extreme. A cooling‑off period is appropriate without a 10x abnormal‑play trigger.
- follow_up_plan: Apply 24–48h cooling‑off; re‑review in 7 days with focus on escalation ratio and late‑night %.

### Case ID: 7
- player_id: PLR_9346_NJ
- state: NJ
- risk_category: HIGH
- primary_driver: LOSS_CHASE
- composite_risk_score: 0.800

**Evidence Snapshot**
- bet_after_loss_ratio: 0.756
- bet_escalation_ratio: 4.55
- sport_diversity_ratio: 0.88
- market_tier_drop_pct: 0.0%
- abnormal_hours_pct: 59.8%
- gamalyze_risk_score: 0.500
- recent_bet_timeline_summary (7d/30d): Last bet: 2026-03-31; 7d bets 12 ($7226.99); 30d bets 45 ($28799.19); Late-night 30d 60.0%

**Regulatory Check**
- State-specific triggers: NJ multi-flag (3+ HIGH/CRITICAL in 30d) not triggered (flags_30d = 2).
- Notes:

**Analyst Decision**
- analyst_action: APPROVE
- intervention_type: LIMITS
- rationale (1-3 sentences): Loss‑chasing and escalation are high, but NJ multi‑flag trigger is not met. Limits are proportional to risk without mandatory timeout.
- follow_up_plan: Apply deposit/wager limits; re‑review in 14 days for trend in loss‑chase ratio and late‑night share.

### Case ID: 8
- player_id: PLR_9392_PA
- state: PA
- risk_category: HIGH
- primary_driver: BET_ESCALATION
- composite_risk_score: 0.795

**Evidence Snapshot**
- bet_after_loss_ratio: 0.700
- bet_escalation_ratio: 4.69
- sport_diversity_ratio: 1.00
- market_tier_drop_pct: -0.1%
- abnormal_hours_pct: 67.7%
- gamalyze_risk_score: 0.693
- recent_bet_timeline_summary (7d/30d): Last bet: 2026-03-31; 7d bets 11 ($7590.57); 30d bets 48 ($40929.26); Late-night 30d 66.7%

**Regulatory Check**
- State-specific triggers: PA self-exclusion reversal trigger not evaluable (no exclusion events in current data).
- Notes: Would require account/exclusion event table to validate 3+ reversals in 6 months.

**Analyst Decision**
- analyst_action: APPROVE
- intervention_type: COOLING_OFF
- rationale (1-3 sentences): Escalation is extreme with sustained late‑night activity. Cooling‑off is appropriate to interrupt the pattern while monitoring for further escalation.
- follow_up_plan: Apply cooling‑off; re‑review in 7–14 days and reassess bet size trend.

### Case ID: 9
- player_id: PLR_1465_NJ
- state: NJ
- risk_category: HIGH
- primary_driver: BET_ESCALATION
- composite_risk_score: 0.798

**Evidence Snapshot**
- bet_after_loss_ratio: 0.649
- bet_escalation_ratio: 4.34
- sport_diversity_ratio: 1.00
- market_tier_drop_pct: 0.6%
- abnormal_hours_pct: 67.8%
- gamalyze_risk_score: 0.928
- recent_bet_timeline_summary (7d/30d): Last bet: 2026-03-31; 7d bets 9 ($8041.62); 30d bets 34 ($31277.01); Late-night 30d 70.6%

**Regulatory Check**
- State-specific triggers: NJ multi-flag (3+ HIGH/CRITICAL in 30d) triggered (flags_30d = 4).
- Notes:

**Analyst Decision**
- analyst_action: ESCALATE
- intervention_type: COOLING_OFF
- rationale (1-3 sentences): NJ multi‑flag trigger is met and escalation is severe with high Gamalyze risk. Cooling‑off is required and escalation documented for compliance.
- follow_up_plan: Apply 24h timeout per NJ; re‑review within 7 days and confirm post‑timeout activity.

### Case ID: 10
- player_id: PLR_6779_NJ
- state: NJ
- risk_category: HIGH
- primary_driver: BET_ESCALATION
- composite_risk_score: 0.798

**Evidence Snapshot**
- bet_after_loss_ratio: 0.688
- bet_escalation_ratio: 4.42
- sport_diversity_ratio: 1.00
- market_tier_drop_pct: -0.6%
- abnormal_hours_pct: 64.3%
- gamalyze_risk_score: 0.760
- recent_bet_timeline_summary (7d/30d): Last bet: 2026-03-31; 7d bets 8 ($1684.26); 30d bets 32 ($6318.23); Late-night 30d 68.8%

**Regulatory Check**
- State-specific triggers: NJ multi-flag (3+ HIGH/CRITICAL in 30d) triggered (flags_30d = 3).
- Notes:

**Analyst Decision**
- analyst_action: ESCALATE
- intervention_type: COOLING_OFF
- rationale (1-3 sentences): Escalation is severe and NJ multi‑flag trigger is met. Cooling‑off is proportional and required under NJ guidelines.
- follow_up_plan: Apply 24h timeout; re‑review in 7 days to reassess escalation and late‑night activity.

### Case ID: 11
- player_id: PLR_4847_MA
- state: MA
- risk_category: MEDIUM
- primary_driver: GAMALYZE
- composite_risk_score: 0.553

**Evidence Snapshot**
- bet_after_loss_ratio: 0.625
- bet_escalation_ratio: 1.81
- sport_diversity_ratio: 0.83
- market_tier_drop_pct: -0.5%
- abnormal_hours_pct: 22.4%
- gamalyze_risk_score: 0.786
- recent_bet_timeline_summary (7d/30d): Last bet: 2026-03-31; 7d bets 6 ($302.48); 30d bets 32 ($2159.17); Late-night 30d 25.0%

**Regulatory Check**
- State-specific triggers: MA abnormal-play trigger (10x rolling avg bet) not triggered (max multiple 3.92x).
- Notes:

**Analyst Decision**
- analyst_action: APPROVE
- intervention_type: NUDGE
- rationale (1-3 sentences): Medium composite with elevated Gamalyze risk and moderate escalation suggests early intervention. Nudge is appropriate given no abnormal‑play trigger.
- follow_up_plan: Send RG reminder; re‑review in 30 days for shifts in escalation or late‑night activity.

### Case ID: 12
- player_id: PLR_6316_NJ
- state: NJ
- risk_category: MEDIUM
- primary_driver: TEMPORAL_RISK
- composite_risk_score: 0.495

**Evidence Snapshot**
- bet_after_loss_ratio: 0.563
- bet_escalation_ratio: 1.70
- sport_diversity_ratio: 1.00
- market_tier_drop_pct: 0.6%
- abnormal_hours_pct: 40.0%
- gamalyze_risk_score: 0.500
- recent_bet_timeline_summary (7d/30d): Last bet: 2026-03-31; 7d bets 6 ($367.39); 30d bets 31 ($1709.94); Late-night 30d 25.8%

**Regulatory Check**
- State-specific triggers: NJ multi-flag (3+ HIGH/CRITICAL in 30d) not triggered (flags_30d < 3).
- Notes:

**Analyst Decision**
- analyst_action: WATCHLIST
- intervention_type: NO_ACTION
- rationale (1-3 sentences): Temporal risk is elevated but other signals are moderate and NJ trigger is not met. Watchlist is appropriate to avoid over‑intervention.
- follow_up_plan: Re‑check in 30 days; monitor for increases in late‑night % or escalation ratio.

### Case ID: 13
- player_id: PLR_6293_PA
- state: PA
- risk_category: MEDIUM
- primary_driver: LOSS_CHASE
- composite_risk_score: 0.548

**Evidence Snapshot**
- bet_after_loss_ratio: 0.656
- bet_escalation_ratio: 1.60
- sport_diversity_ratio: 0.88
- market_tier_drop_pct: -1.7%
- abnormal_hours_pct: 37.5%
- gamalyze_risk_score: 0.579
- recent_bet_timeline_summary (7d/30d): Last bet: 2026-03-31; 7d bets 10 ($839.49); 30d bets 31 ($3119.89); Late-night 30d 35.5%

**Regulatory Check**
- State-specific triggers: PA self-exclusion reversal trigger not evaluable (no exclusion events in current data).
- Notes: Would require account/exclusion event table to validate 3+ reversals in 6 months.

**Analyst Decision**
- analyst_action: APPROVE
- intervention_type: NUDGE
- rationale (1-3 sentences): Loss‑chasing is moderate with elevated late‑night activity, but escalation is below critical. A nudge is proportional for a medium‑risk profile.
- follow_up_plan: Send RG reminder; re‑review in 30 days and watch for escalation increases.

### Case ID: 14
- player_id: PLR_0519_NJ
- state: NJ
- risk_category: MEDIUM
- primary_driver: BET_ESCALATION
- composite_risk_score: 0.598

**Evidence Snapshot**
- bet_after_loss_ratio: 0.515
- bet_escalation_ratio: 3.55
- sport_diversity_ratio: 1.00
- market_tier_drop_pct: 0.4%
- abnormal_hours_pct: 57.5%
- gamalyze_risk_score: 0.500
- recent_bet_timeline_summary (7d/30d): Last bet: 2026-03-31; 7d bets 8 ($4630.58); 30d bets 31 ($17599.64); Late-night 30d 58.1%

**Regulatory Check**
- State-specific triggers: NJ multi-flag (3+ HIGH/CRITICAL in 30d) not triggered (flags_30d < 3).
- Notes:

**Analyst Decision**
- analyst_action: APPROVE
- intervention_type: LIMITS
- rationale (1-3 sentences): Escalation ratio is high with substantial late‑night activity, even though the composite score remains medium. Limits are appropriate to reduce risk without invoking a timeout.
- follow_up_plan: Apply limits; re‑review in 14 days for escalation and late‑night trends.

### Case ID: 15
- player_id: PLR_9523_NJ
- state: NJ
- risk_category: MEDIUM
- primary_driver: LOSS_CHASE
- composite_risk_score: 0.578

**Evidence Snapshot**
- bet_after_loss_ratio: 0.719
- bet_escalation_ratio: 1.47
- sport_diversity_ratio: 1.00
- market_tier_drop_pct: 0.7%
- abnormal_hours_pct: 44.1%
- gamalyze_risk_score: 0.500
- recent_bet_timeline_summary (7d/30d): Last bet: 2026-03-31; 7d bets 9 ($1230.29); 30d bets 32 ($2906.01); Late-night 30d 40.6%

**Regulatory Check**
- State-specific triggers: NJ multi-flag (3+ HIGH/CRITICAL in 30d) not triggered (flags_30d < 3).
- Notes:

**Analyst Decision**
- analyst_action: APPROVE
- intervention_type: NUDGE
- rationale (1-3 sentences): Loss‑chasing is elevated but escalation is moderate and NJ trigger is not met. Nudge is appropriate for medium risk with monitoring.
- follow_up_plan: Send RG reminder; re‑review in 30 days with focus on loss‑chasing ratio.

## Regulatory Trigger Cross-Check
Cases were selected by composite risk score; state triggers were checked where data permits.

- MA abnormal-play 10x trigger: not triggered for any MA cases.
- NJ multi-flag 3+ in 30d: triggered for PLR_6526_NJ (5), PLR_1465_NJ (4), PLR_6779_NJ (3).
- PA self-exclusion reversals: not evaluable in this dataset.

## Queries Used
```sql
-- Select CRITICAL/HIGH candidates for review (queue-based)
SELECT
  q.player_id,
  q.risk_category,
  q.primary_driver,
  q.composite_risk_score,
  p.state_jurisdiction
FROM staging_prod.rg_intervention_queue q
JOIN staging_staging.stg_player_profiles p
  ON q.player_id = p.player_id
WHERE q.risk_category IN ('CRITICAL','HIGH')
ORDER BY q.composite_risk_score DESC, q.calculated_at DESC
LIMIT 20;

-- Select MEDIUM candidates for review (derive primary driver)
WITH scored AS (
  SELECT
    r.player_id,
    r.risk_category,
    CASE
      WHEN r.loss_chase_score >= GREATEST(r.bet_escalation_score, r.market_drift_score, r.temporal_risk_score, r.gamalyze_risk_score)
        THEN 'LOSS_CHASE'
      WHEN r.bet_escalation_score >= GREATEST(r.loss_chase_score, r.market_drift_score, r.temporal_risk_score, r.gamalyze_risk_score)
        THEN 'BET_ESCALATION'
      WHEN r.market_drift_score >= GREATEST(r.loss_chase_score, r.bet_escalation_score, r.temporal_risk_score, r.gamalyze_risk_score)
        THEN 'MARKET_DRIFT'
      WHEN r.temporal_risk_score >= GREATEST(r.loss_chase_score, r.bet_escalation_score, r.market_drift_score, r.gamalyze_risk_score)
        THEN 'TEMPORAL_RISK'
      ELSE 'GAMALYZE'
    END AS primary_driver,
    r.composite_risk_score,
    p.state_jurisdiction
  FROM staging_prod.rg_risk_scores r
  JOIN staging_staging.stg_player_profiles p
    ON r.player_id = p.player_id
  WHERE r.risk_category = 'MEDIUM'
)
SELECT *
FROM scored
ORDER BY composite_risk_score DESC
LIMIT 20;

-- Pull X most recent bets for a single player_id
SELECT
  bet_id,
  bet_timestamp,
  bet_amount,
  outcome,
  sport_category,
  market_type,
  odds_american
FROM staging_staging.stg_bet_logs
WHERE player_id = 'PLR_6526_NJ'
ORDER BY bet_timestamp DESC
LIMIT 25;

-- MA: abnormal play trigger (bet > 10x rolling 90d avg)
WITH player_avg AS (
  SELECT player_id, AVG(bet_amount) AS avg_bet_90d
  FROM staging_staging.stg_bet_logs
  WHERE bet_timestamp >= (
    SELECT MAX(bet_timestamp) - INTERVAL '90 days'
    FROM staging_staging.stg_bet_logs
  )
  GROUP BY 1
)
SELECT
  b.player_id,
  COUNT(*) AS trigger_bets,
  MAX(b.bet_amount / NULLIF(a.avg_bet_90d, 0)) AS max_multiple
FROM staging_staging.stg_bet_logs b
JOIN player_avg a
  ON b.player_id = a.player_id
JOIN staging_staging.stg_player_profiles p
  ON b.player_id = p.player_id
WHERE p.state_jurisdiction = 'MA'
  AND b.player_id IN (
    'PLR_6526_NJ','PLR_1955_PA','PLR_5789_MA','PLR_4762_PA','PLR_0533_PA',
    'PLR_4560_MA','PLR_9346_NJ','PLR_9392_PA','PLR_1465_NJ','PLR_6779_NJ',
    'PLR_4847_MA','PLR_6316_NJ','PLR_6293_PA','PLR_0519_NJ','PLR_9523_NJ'
  )
  AND b.bet_amount > a.avg_bet_90d * 10
GROUP BY 1
ORDER BY trigger_bets DESC;

-- NJ: multi-flag trigger (3+ HIGH/CRITICAL in 30 days)
SELECT
  a.player_id,
  COUNT(*) AS flags_30d
FROM staging_prod.rg_audit_trail a
JOIN staging_staging.stg_player_profiles p
  ON a.player_id = p.player_id
WHERE p.state_jurisdiction = 'NJ'
  AND a.risk_category IN ('HIGH','CRITICAL')
  AND a.score_calculated_at >= (
    SELECT MAX(score_calculated_at) - INTERVAL '30 days'
    FROM staging_prod.rg_audit_trail
  )
  AND a.player_id IN (
    'PLR_6526_NJ','PLR_1955_PA','PLR_5789_MA','PLR_4762_PA','PLR_0533_PA',
    'PLR_4560_MA','PLR_9346_NJ','PLR_9392_PA','PLR_1465_NJ','PLR_6779_NJ',
    'PLR_4847_MA','PLR_6316_NJ','PLR_6293_PA','PLR_0519_NJ','PLR_9523_NJ'
  )
GROUP BY 1
HAVING COUNT(*) >= 3;
```

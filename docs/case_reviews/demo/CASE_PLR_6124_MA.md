# Case Review — PLR_6124_MA (Critical)

## 1) Case Header
- case_id: CASE-PLR_6124_MA
- player_id: PLR_6124_MA
- state_jurisdiction: MA
- risk_category: CRITICAL
- composite_risk_score: 0.877
- primary_driver: LOSS_CHASE
- review_status: SUBMITTED
- score_calculated_at: 2026-02-24 11:41:27.753000-05:00

## 2) Evidence Summary (What Stands Out)
- Composite score is 0.877 with primary driver `LOSS_CHASE`.
- Component profile: loss_chase=1.000, bet_escalation=1.000, market_drift=0.330, temporal=1.000, gamalyze=0.888.
- Recent intensity: 53 bets / $90,407.77 wagered in 7d; 107 bets / $169,423.57 in 90d.

## 3) SQL Evidence (Queries + Outputs)
### A) Risk Snapshot
```sql
SELECT r.player_id,
       p.state_jurisdiction,
       r.risk_category,
       r.composite_risk_score,
       r.loss_chase_score,
       r.bet_escalation_score,
       r.market_drift_score,
       r.temporal_risk_score,
       r.gamalyze_risk_score,
       r.calculated_at,
       q.primary_driver
FROM PROD.RG_RISK_SCORES r
LEFT JOIN PROD.RG_INTERVENTION_QUEUE q ON q.player_id = r.player_id
LEFT JOIN STAGING.STG_PLAYER_PROFILES p ON p.player_id = r.player_id
WHERE r.player_id = '{{player_id}}';
```
- Output summary: 1 row returned for PLR_6124_MA with category `CRITICAL` and composite `0.877`.

### B) 7-Day Activity
```sql
SELECT COUNT(*) AS total_bets_7d, SUM(bet_amount) AS total_wagered_7d,
       AVG(bet_amount) AS avg_bet_7d, MAX(bet_amount) AS max_bet_7d
FROM STAGING.STG_BET_LOGS
WHERE player_id = '{{player_id}}'
  AND bet_timestamp >= DATEADD('day', -7, CURRENT_TIMESTAMP);
```
- Output summary: total_bets_7d=53, total_wagered_7d=$90,407.77, avg_bet_7d=$1,705.81, max_bet_7d=$2,214.05

### C) After-Loss vs After-Win
```sql
WITH ordered AS (
  SELECT bet_timestamp, bet_amount, outcome,
         LAG(outcome) OVER (ORDER BY bet_timestamp) AS prev_outcome
  FROM STAGING.STG_BET_LOGS
  WHERE player_id = '{{player_id}}'
)
SELECT AVG(CASE WHEN prev_outcome = 'loss' THEN bet_amount END) AS avg_after_loss,
       AVG(CASE WHEN prev_outcome = 'win' THEN bet_amount END) AS avg_after_win,
       ROUND(AVG(CASE WHEN prev_outcome = 'loss' THEN bet_amount END) /
             NULLIF(AVG(CASE WHEN prev_outcome = 'win' THEN bet_amount END),0), 2) AS after_loss_ratio
FROM ordered;
```
- Output summary: avg_after_loss=$2,038.64, avg_after_win=$416.61, after_loss_ratio=4.89

### D) Gamalyze Components
```sql
SELECT assessment_date, sensitivity_to_loss, sensitivity_to_reward,
       risk_tolerance, decision_consistency, gamalyze_version
FROM STAGING.STG_GAMALYZE_SCORES
WHERE player_id = '{{player_id}}'
ORDER BY assessment_date DESC
LIMIT 1;
```
- Output summary: assessment_date=2025-10-29, sensitivity_to_loss=95.14, sensitivity_to_reward=68.42, risk_tolerance=100.00, decision_consistency=13.34, version=v3.2.1

## 4) LLM Prompts Used (Assistive Only)
- Prompt 1: "Summarize top risk drivers and draft neutral analyst rationale for this player."
- Prompt 2: "Draft supportive nudge text aligned to Responsible Gaming tone guidelines."
- LLM use: assistive only; final decision retained by analyst.

## 5) False-Positive Checks
- Large payouts check (90d): 0 payouts at >=5x stake.
- Sample-size check: 107 bets in 90d (sufficient for ratio interpretation).
- Model consistency check: driver `LOSS_CHASE` aligns with strongest component direction.

## 6) Decision + Action
- analyst_action: ESCALATE
- intervention_type: HOLD/REFERRAL
- rationale: Composite and component signals are all elevated with reinforcing patterns across intensity, escalation, and temporal behavior.
- follow_up_plan: Re-evaluate within 7 days with emphasis on trend direction and jurisdiction trigger checks.

## 7) Nudge Copy (Supportive, Non-Coercive)
"Hi — we noticed some recent changes in play patterns. If useful, you can set limits or take a short break anytime in the Responsible Gaming Center. We're here to support you in staying in control."

## 8) Audit Log Summary
- SQL query evidence: logged
- LLM prompt log: logged
- Analyst note: logged
- Trigger check: logged for MA
- Case lifecycle status: SUBMITTED

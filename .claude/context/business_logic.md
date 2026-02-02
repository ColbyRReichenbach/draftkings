# Business Logic Reference

**Purpose**: Centralized source of truth for all business rules, thresholds, and calculations in DK Sentinel

**Last Updated**: 2026-02-01

---

## Risk Score Component Weights (v1.0)

**CRITICAL**: These weights are subject to monthly active learning calibration based on analyst feedback.
````python
COMPOSITE_RISK_WEIGHTS = {
    'loss_chase_score': 0.30,       # Bet after loss patterns
    'bet_escalation_score': 0.25,   # Bet size increase after losses
    'market_drift_score': 0.15,     # Sport/tier/time drift
    'temporal_risk_score': 0.10,    # Late-night betting
    'gamalyze_risk_score': 0.20     # External neuro-markers
}

# Total MUST equal 1.00 (enforced via dbt test)
assert sum(COMPOSITE_RISK_WEIGHTS.values()) == 1.00
````

**Rationale for Weights**:
- **loss_chase (0.30)**: Strongest empirical predictor (68% of self-excluded showed ratio >0.75)
- **bet_escalation (0.25)**: r=0.72 correlation with Gamalyze sensitivity to loss
- **market_drift (0.15)**: Moderate predictor; common in normal exploration
- **temporal (0.10)**: Highest variance; confounded by shift workers and time zones
- **gamalyze (0.20)**: External validation baseline; r=0.58 correlation with composite features

---

## Component Score Calculations

### 1. Loss Chase Score

**Formula**:
````python
loss_chase_score = normalize(
    value=bet_after_loss_ratio,
    low_threshold=0.40,
    high_threshold=0.75
)

def normalize(value, low_threshold, high_threshold):
    if value >= high_threshold:
        return 1.0
    elif value >= low_threshold:
        return (value - low_threshold) / (high_threshold - low_threshold)
    else:
        return 0.0
````

**Thresholds**:
- `< 0.40`: Normal (risk = 0.0)
- `0.40 - 0.75`: Moderate to High (linear interpolation)
- `> 0.75`: Critical (risk = 1.0)

**Business Rule**: `bet_after_loss_ratio = bets_after_loss / total_bets`

**Edge Cases**:
- Players with <2 bets: Excluded (insufficient data)
- Players with 100% wins: ratio = 0.0 (no losses to chase)
- Players with 100% losses: ratio = 1.0 (all bets after losses)

---

### 2. Bet Escalation Score

**Formula**:
````python
bet_escalation_score = normalize(
    value=bet_escalation_ratio,
    low_threshold=1.2,
    high_threshold=2.0
)
````

**Business Rule**: `bet_escalation_ratio = avg_bet_after_loss / avg_bet_after_win`

**Thresholds**:
- `< 1.2`: Consistent bet sizing (risk = 0.0)
- `1.2 - 2.0`: Escalating bets (linear interpolation)
- `> 2.0`: Doubling down (risk = 1.0)

**Edge Cases**:
- `avg_bet_after_win = 0`: Set ratio = 0.0 (no wins to compare against)
- Very small bet amounts (<$1): May produce artificially high ratios → cap at 10.0

---

### 3. Market Drift Score

**Components** (weighted equally: 0.33 each):
- Horizontal drift (sport diversity)
- Vertical drift (market tier quality)
- Temporal drift (time-of-day abnormality)

**Composite Formula**:
````python
market_drift_score = (
    horizontal_drift_score * 0.33 +
    vertical_drift_score * 0.33 +
    temporal_drift_score * 0.33
)
````

#### 3a. Horizontal Drift Score

**Formula**:
````python
horizontal_drift_score = normalize(
    value=sport_diversity_ratio,
    low_threshold=1.5,
    high_threshold=3.0
)

sport_diversity_ratio = unique_sports_7d / baseline_sports_90d
````

**Thresholds**:
- `< 1.5x`: Normal exploration
- `1.5x - 3.0x`: Moderate drift
- `> 3.0x`: "Betting on anything available" (desperation signal)

#### 3b. Vertical Drift Score

**Market Tier Classification**:
````python
MARKET_TIERS = {
    1.0: ['NFL', 'NBA', 'MLB', 'NHL', 'SOCCER_EPL'],
    0.7: ['NCAA_BASKETBALL', 'NCAA_FOOTBALL'],
    0.5: ['MMA', 'BOXING', 'TENNIS'],
    0.2: ['TABLE_TENNIS', 'KOREAN_BASEBALL', 'ESPORTS', 'DARTS']
}
````

**Formula**:
````python
vertical_drift_score = normalize(
    value=tier_drop_pct,
    low_threshold=0.30,  # 30% drop
    high_threshold=0.60  # 60% drop
)

tier_drop_pct = (baseline_tier_90d - current_tier_7d) / baseline_tier_90d
````

**Interpretation**:
- Tier 1.0 → Tier 0.7: 30% drop (moderate drift)
- Tier 1.0 → Tier 0.2: 80% drop (critical drift)

#### 3c. Temporal Drift Score

**Formula**:
````python
temporal_drift_score = normalize(
    value=abnormal_hours_pct,
    low_threshold=0.20,  # 20% of bets
    high_threshold=0.50  # 50% of bets
)

abnormal_hours_pct = bets_2am_to_6am / total_bets_7d
````

**Baseline Comparison**:
- If player's baseline is <5% late-night betting
- Current week: 40% late-night
- **Drift**: 40% / 5% = 8x increase → High risk

---

### 4. Temporal Risk Score

**DEPRECATED IN FAVOR OF**: Market Drift → Temporal Drift component

(Keeping for backward compatibility until v2.0 weight rebalancing)

---

### 5. Gamalyze Risk Score

**Source**: Mindway AI Gamalyze neuro-marker assessments (0-100 scale)

**Formula**:
````python
gamalyze_risk_score = (
    (sensitivity_to_loss / 100) * 0.40 +      # Strongest predictor
    (sensitivity_to_reward / 100) * 0.25 +    # Moderate predictor
    (risk_tolerance / 100) * 0.25 +           # Moderate predictor
    ((100 - decision_consistency) / 100) * 0.10  # Inverse scoring
)
````

**Component Weights** (within Gamalyze score):
- **Sensitivity to Loss** (0.40): r=0.72 with bet_escalation_ratio
- **Sensitivity to Reward** (0.25): "Hot hand" fallacy
- **Risk Tolerance** (0.25): Preference for high-variance bets
- **Decision Consistency** (0.10): Lower = more erratic (inverse scoring)

**Thresholds** (for individual components):
- **Sensitivity to Loss**: >75 = risky
- **Sensitivity to Reward**: >70 = risky
- **Risk Tolerance**: >80 = risky
- **Decision Consistency**: <30 = risky (inverse)

---

## Risk Category Classification

**Final Composite Risk Score** (0-1 scale) maps to categories:
````python
def classify_risk(composite_risk_score: float) -> str:
    if composite_risk_score >= 0.80:
        return 'CRITICAL'
    elif composite_risk_score >= 0.60:
        return 'HIGH'
    elif composite_risk_score >= 0.40:
        return 'MEDIUM'
    else:
        return 'LOW'
````

**Thresholds**:
- **CRITICAL** (0.80-1.00): Immediate intervention required
- **HIGH** (0.60-0.79): Elevated monitoring + nudge within 24h
- **MEDIUM** (0.40-0.59): Watchlist + weekly check-in
- **LOW** (0.00-0.39): Standard monitoring

---

## Intervention Action Matrix

| Risk Category | Automatic Action | Analyst Decision Required | Customer Communication |
|---------------|------------------|---------------------------|------------------------|
| **CRITICAL** | Add to priority queue | YES (within 2 hours) | Supportive nudge + timeout offer |
| **HIGH** | Add to standard queue | YES (within 24 hours) | Supportive nudge |
| **MEDIUM** | Add to watchlist | NO (automated nudge) | Optional check-in message |
| **LOW** | Monitor only | NO | None |

**Human-in-the-Loop (HITL) Requirement**:
- CRITICAL and HIGH: Analyst MUST review and sign off before customer communication
- MEDIUM: Automated nudge OK, but logged in audit trail
- LOW: No intervention

---

## State-Specific Regulatory Triggers

### Massachusetts (205 CMR 238.04)

**Trigger 1: Abnormal Single Bet**
````sql
-- Bet amount >10x rolling 90-day average
WHERE bet_amount > (rolling_avg_90d * 10)
````

**Required Action**: Internal documentation in audit trail

**Trigger 2: High Deposit After Loss**
````sql
-- Deposit >$5K within 24h after losses >$10K
WHERE deposit_amount > 5000
  AND losses_24h > 10000
````

**Required Action**: Internal documentation + analyst review

---

### New Jersey

**Trigger: Multi-Venue High-Risk Pattern**
````sql
-- 3+ high-risk flags across ANY operators in 30 days
SELECT player_id, COUNT(*) AS flags
FROM state_gaming_database.all_operators
WHERE risk_category IN ('HIGH', 'CRITICAL')
  AND flag_timestamp >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY player_id
HAVING COUNT(*) >= 3
````

**Required Action**: Mandatory 24-hour timeout + Gaming Commission notification

---

### Pennsylvania

**Trigger: Self-Exclusion Reversal Frequency**
````sql
-- 3+ self-exclusion reversals in 6 months
SELECT player_id, COUNT(*) AS reversals
FROM self_exclusion_history
WHERE action = 'reversed'
  AND reversal_date >= CURRENT_DATE - INTERVAL '6 months'
GROUP BY player_id
HAVING COUNT(*) >= 3
````

**Required Action**: Problem Gambling Council referral + 72-hour cooling period

---

## Active Learning Calibration Process

**Frequency**: Monthly

**Process**:
1. Query analyst feedback from audit trail
2. Calculate approval rate per risk component
3. Analyze correlation with 30-day outcomes (self-exclusion, churn)
4. Adjust weights if:
   - Approval rate <70% (reduce weight)
   - Correlation increases significantly (increase weight)
5. Normalize weights to sum to 1.00
6. Deploy updated model
7. Document changes in CLAUDE.md

**Example Adjustment** (March 2026):
````python
# February results
temporal_risk_approval_rate = 0.62  # Below 0.70 threshold

# Action: Reduce temporal_risk_score weight
OLD: temporal_risk_score = 0.10
NEW: temporal_risk_score = 0.08

# Redistribute to stronger predictors
loss_chase_score: 0.30 → 0.31
bet_escalation_score: 0.25 → 0.26
````

---

## Data Quality Rules

**Minimum Data Requirements**:
- ≥2 bets in 7-day window (for ratios to be meaningful)
- ≥1 Gamalyze assessment in 90 days (or use default 50/100 baseline)

**Null Handling**:
- Missing component score → Impute with population median
- All components missing → Exclude player from risk scoring

**Outlier Handling**:
- Cap bet_escalation_ratio at 10.0 (prevents tiny denominators from skewing)
- Flag sport_diversity_ratio >10.0 for manual review (data quality issue)

---

## Version History

- **v1.0** (2026-01-15): Initial release with 5 components
- **v1.1** (2026-02-01): Updated market drift to 3-dimensional composite
- **v2.0** (TBD): Planned addition of deposit_frequency_score component

---

**For implementation details, see**: `.claude/skills/behavioral-analytics.md`

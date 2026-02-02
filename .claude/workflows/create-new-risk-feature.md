# Workflow: Create New Risk Feature

**When to use**: Adding a new behavioral risk indicator (e.g., "deposit_frequency_score", "parlay_preference_score")

**Estimated time**: 4-6 hours for complete implementation + testing

---

## Prerequisites

- [ ] Business requirement documented (threshold definitions, weights)
- [ ] Source data available in staging layer
- [ ] Statistical validation completed (correlation with problem gambling)
- [ ] Stakeholder sign-off on feature inclusion

---

## Phase 1: Design & Planning (30 min)

### Step 1: Enter Plan Mode
````bash
# Press Shift+Tab twice
claude
# Plan Mode: ON
````

### Step 2: Voice Dictation Prompt (Fn+Fn)
````
"I need to add a new risk feature called [FEATURE_NAME] to the DK Sentinel system.

Business Logic:
- [Describe calculation logic]
- [Define thresholds: low/medium/high/critical]
- [Correlation with problem gambling: r=X.XX]

Integration Points:
- Source data: [table name]
- dbt layer: intermediate
- Final integration: marts/rg_risk_scores.sql

Create a comprehensive plan before writing any code."
````

### Step 3: Review Plan
Claude generates `plan.md` with:
- SQL model design
- Test strategy
- Integration points
- Performance considerations

**Action**: Review plan, press **Ctrl+G** to edit if needed

### Step 4: Approve Plan
Exit Plan Mode → Claude proceeds to implementation

---

## Phase 2: dbt Model Creation (1-2 hours)

### Step 5: Create Intermediate Model
````bash
# Let @dbt-architect handle this
````

**Prompt**:
````
"Use subagents. Have @dbt-architect create int_[feature_name]_indicators.sql with:

1. Incremental materialization
2. Window functions for temporal analysis
3. Player-level aggregation
4. Data contract enforcement
5. Proper column documentation

Follow dbt-transformations skill best practices."
````

### Step 6: Add Feature Calculation to Marts
**File**: `models/marts/rg_risk_scores.sql`

**Prompt**:
````
"Update marts/rg_risk_scores.sql to include [feature_name]:

1. Join to int_[feature_name]_indicators
2. Calculate normalized score (0-1 scale)
3. Add to component_scores object
4. Update composite_risk_score calculation (adjust weights)

CRITICAL: Ensure all component weights still sum to 1.0"
````

---

## Phase 3: Testing (1-2 hours)

### Step 7: Delegate Testing to Subagent
````bash
# Let @data-quality-tester handle comprehensive testing
````

**Prompt**:
````
"Use subagents. Have @data-quality-tester create tests for int_[feature_name]_indicators:

1. Generic tests (schema.yml):
   - not_null on key columns
   - accepted_range (0-1 for normalized scores)
   - relationships (foreign keys)

2. Singular tests (tests/):
   - assert_[feature]_thresholds_valid.sql
   - assert_no_negative_values.sql

3. Business logic validation:
   - Spot check 10 random players
   - Verify calculation against manual calculation
   - Edge cases (zero data, nulls, boundary values)

4. Performance test:
   - Run on 10K players
   - Target: <2 min execution time
   - Alert if >3 min"
````

### Step 8: Run Validation Pipeline
````bash
/validate-pipeline
````

Expected output:
````
✅ dbt tests: 52/52 passed (was 47/47, added 5 for new feature)
✅ Risk weights: Sum = 1.00 (adjusted for new component)
✅ Thresholds: 0 invalid values
✅ Row counts: 500K bets → 10K players → 10K risk scores
✅ Performance: 5m 42s (within 7m threshold)
````

---

## Phase 4: Weight Calibration (30-60 min)

### Step 9: Determine Component Weight
**Options**:

**A) Statistical Approach** (if correlation data available):
````sql
-- Calculate correlation with self-exclusion
SELECT 
    CORR([new_feature_score], self_excluded_flag) AS correlation
FROM ANALYTICS.PLAYER_OUTCOMES
WHERE outcome_date >= '2025-01-01';

-- Weight proportional to correlation strength
-- Example: r=0.65 → weight ≈ 0.15-0.20
````

**B) Expert Judgment** (if no historical data):
- Conservative: Start with 0.10 (10%)
- Adjust after 30-day pilot based on analyst feedback

### Step 10: Update Weight Configuration
**File**: `CLAUDE.md` → Domain Knowledge → Risk Score Weights
````python
# OLD
COMPOSITE_RISK_WEIGHTS = {
    'loss_chase_score': 0.30,
    'bet_escalation_score': 0.25,
    'market_drift_score': 0.15,
    'temporal_risk_score': 0.10,
    'gamalyze_risk_score': 0.20
}

# NEW (example: adding deposit_frequency with 0.12 weight)
COMPOSITE_RISK_WEIGHTS = {
    'loss_chase_score': 0.28,        # Reduced from 0.30
    'bet_escalation_score': 0.23,    # Reduced from 0.25
    'market_drift_score': 0.13,      # Reduced from 0.15
    'temporal_risk_score': 0.09,     # Reduced from 0.10
    'gamalyze_risk_score': 0.18,     # Reduced from 0.20
    'deposit_frequency_score': 0.12  # NEW FEATURE
}
# Total: 1.03 → must normalize to 1.00
````

**Normalization**:
````python
# Divide each weight by sum (1.03) to normalize to 1.00
normalized_weights = {k: v/1.03 for k, v in weights.items()}
````

### Step 11: Update dbt Model with New Weights
**File**: `models/marts/rg_risk_scores.sql`
````sql
-- Update composite score calculation
SELECT
    player_id,
    -- Component scores
    loss_chase_score,
    bet_escalation_score,
    market_drift_score,
    temporal_risk_score,
    gamalyze_risk_score,
    deposit_frequency_score,  -- NEW
    
    -- Composite calculation (updated weights)
    (
        (loss_chase_score * 0.272) +        -- 0.28/1.03
        (bet_escalation_score * 0.223) +     -- 0.23/1.03
        (market_drift_score * 0.126) +       -- 0.13/1.03
        (temporal_risk_score * 0.087) +      -- 0.09/1.03
        (gamalyze_risk_score * 0.175) +      -- 0.18/1.03
        (deposit_frequency_score * 0.117)    -- 0.12/1.03
    ) AS composite_risk_score
FROM component_scores
````

### Step 12: Verify Weights Sum to 1.0
````bash
/validate-pipeline
````

Should pass:
````
✅ Risk weights: Sum = 1.00
````

---

## Phase 5: Documentation & Deployment (30 min)

### Step 13: Update Documentation

**A) CLAUDE.md**:
````markdown
## Domain Knowledge → Risk Score Weights (v2.0)

**CHANGELOG**:
- 2026-02-15: Added deposit_frequency_score (weight: 0.117)
- 2026-02-15: Rebalanced existing weights (all reduced proportionally)

**NEW FEATURE**: deposit_frequency_score
- **What it measures**: Unusual increase in deposit frequency (deposits/day)
- **Threshold**: >3x baseline deposit frequency = high risk
- **Evidence**: r=0.58 correlation with churn-after-loss patterns
- **Weight Rationale**: Moderate predictor; 0.117 weight reflects correlation strength
````

**B) behavioral-analytics.md skill**:
Add section documenting new feature:
````markdown
## Deposit Frequency Detection

### Metric: Deposits Per Day (7-day window)

**Formula**: `total_deposits_7d / 7`

**Baseline**: Player's rolling 90-day average

**Risk Levels**:
- **Normal**: 1.2x baseline
- **Moderate**: 2-3x baseline
- **Risky**: >3x baseline

**Interpretation**: Rapid deposit escalation suggests chasing losses

**Example**:
```sql
-- Player normally deposits 2x/week (0.29/day baseline)
-- This week: 6 deposits in 7 days (0.86/day)
-- Ratio: 0.86 / 0.29 = 2.97x → MODERATE RISK
```
````

### Step 14: Run Full Regression Test
````bash
# Full dbt run + test suite
dbt run --models staging+ intermediate+ marts+
dbt test

# Validate pipeline
/validate-pipeline

# Check for unexpected changes in existing risk scores
dbt run-operation compare_risk_scores --args '{old_table: "rg_risk_scores_v1", new_table: "rg_risk_scores_v2"}'
````

### Step 15: Deploy to Production
````bash
# Tag release
git add .
git commit -m "feat: add deposit_frequency_score component

- Created int_deposit_frequency_indicators.sql
- Integrated into marts/rg_risk_scores.sql
- Rebalanced component weights (v1.0 → v2.0)
- Added comprehensive tests
- Updated documentation

Closes #47"

git tag -a v2.0.0 -m "Release v2.0: Deposit Frequency Risk Component"
git push origin main --tags
````

---

## Phase 6: Monitoring & Calibration (Ongoing)

### Step 16: Set Up Monitoring Dashboard
````sql
-- Create view for feature performance tracking
CREATE VIEW ANALYTICS.DEPOSIT_FREQUENCY_PERFORMANCE AS
SELECT
    DATE_TRUNC('day', score_calculated_at) AS date,
    AVG(deposit_frequency_score) AS avg_score,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY deposit_frequency_score) AS median_score,
    COUNT(*) FILTER (WHERE deposit_frequency_score > 0.75) AS high_risk_count,
    COUNT(*) AS total_players
FROM PROD.RG_RISK_SCORES
WHERE score_calculated_at >= DATEADD(day, -30, CURRENT_DATE())
GROUP BY 1
ORDER BY 1 DESC;
````

### Step 17: 30-Day Pilot Review
**After 30 days, analyze**:

1. **Analyst Feedback**:
````sql
   -- How often do analysts agree with deposit_frequency flags?
   SELECT 
       AVG(CASE WHEN analyst_action = 'approved' THEN 1 ELSE 0 END) AS approval_rate
   FROM PROD.RG_AUDIT_TRAIL
   WHERE feature_flagged = 'deposit_frequency'
     AND score_calculated_at >= DATEADD(day, -30, CURRENT_DATE());
````

2. **Correlation with Outcomes**:
````sql
   -- Does high deposit_frequency predict self-exclusion?
   SELECT
       deposit_frequency_score_bucket,
       COUNT(*) AS total_players,
       SUM(CASE WHEN self_excluded_30d THEN 1 ELSE 0 END) AS self_exclusions,
       (self_exclusions::FLOAT / total_players) AS exclusion_rate
   FROM ANALYTICS.PLAYER_OUTCOMES
   WHERE cohort_start_date >= DATEADD(day, -30, CURRENT_DATE())
   GROUP BY 1
   ORDER BY 1;
````

3. **Weight Adjustment** (if needed):
   - If approval_rate <70%: Consider reducing weight
   - If exclusion_rate correlation strong: Consider increasing weight

### Step 18: Update CLAUDE.md with Learnings
````markdown
## Recent Lessons (Most Recent First)

- 2026-03-15: deposit_frequency_score weight adjusted from 0.117 → 0.095 based on 30-day pilot showing lower-than-expected predictive power (analyst approval rate: 68%)
````

---

## Success Criteria

- [ ] dbt models run without errors
- [ ] All tests pass (generic + singular)
- [ ] Weights sum to exactly 1.0
- [ ] Performance <7 min for 10K players
- [ ] Documentation updated (CLAUDE.md + skills)
- [ ] Deployed to production with semantic versioning
- [ ] 30-day monitoring dashboard configured

---

## Common Pitfalls

❌ **Forgetting to normalize weights**: Always divide by sum to ensure total = 1.0

❌ **Skipping edge case testing**: Test with zero data, nulls, boundary values

❌ **No performance baseline**: Run full-refresh first to establish performance expectations

❌ **Insufficient documentation**: Future-you (or teammates) won't remember the rationale

---

## Rollback Procedure

If feature causes issues in production:
````bash
# Revert to previous version
git revert HEAD
git push origin main

# OR restore previous weights in marts/rg_risk_scores.sql
# Set new feature weight to 0.00, redistribute to other components
# Run dbt and validate
````

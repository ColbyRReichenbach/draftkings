---
name: validate-pipeline
description: Complete data quality validation workflow for DK Sentinel - run dbt tests, check row counts, validate business logic, verify compliance - use when asked to validate pipeline, check data quality, or run all tests
allowed-tools: Bash, Read, Grep
---

# Data Pipeline Validation Workflow

## When to Use
- After implementing new dbt models
- Before deploying to production
- When debugging data quality issues
- Daily/weekly validation runs

---

## Execution Sequence

### Step 1: dbt Test Suite
```bash
#!/bin/bash

echo "=== Step 1: Running dbt Tests ==="
cd dbt_project

# Run all tests
dbt test

# Capture exit code
if [ $? -ne 0 ]; then
    echo "❌ dbt tests FAILED"
    
    # Re-run with --store-failures for debugging
    dbt test --select tag:critical --store-failures
    
    # Show which tests failed
    dbt test --select result:fail
    
    exit 1
else
    echo "✅ All dbt tests PASSED"
fi
```

---

### Step 2: Business Logic Validation

**Risk Score Component Weights**:
```sql
-- File: tests/validate_risk_weights.sql
-- Verify weights sum to 1.0

SELECT
    0.30 + 0.25 + 0.15 + 0.10 + 0.20 AS weight_sum,
    CASE
        WHEN ROUND(weight_sum, 2) = 1.00 THEN '✅ PASS'
        ELSE '❌ FAIL'
    END AS validation_status,
    CASE
        WHEN ROUND(weight_sum, 2) != 1.00 
        THEN 'Weights sum to ' || ROUND(weight_sum, 4) || ' instead of 1.00'
        ELSE 'Weights correctly sum to 1.00'
    END AS details
FROM (SELECT 1);
```

**Threshold Spot Checks** (sample 10 random players):
```sql
-- File: tests/validate_loss_chase_thresholds.sql
-- Ensure bet_after_loss_ratio is within valid range

SELECT
    player_id,
    bet_after_loss_ratio,
    CASE
        WHEN bet_after_loss_ratio < 0 THEN '❌ NEGATIVE VALUE'
        WHEN bet_after_loss_ratio > 1 THEN '❌ EXCEEDS 1.0'
        ELSE '✅ VALID'
    END AS validation,
    CASE
        WHEN bet_after_loss_ratio < 0 OR bet_after_loss_ratio > 1
        THEN 'Invalid ratio: ' || ROUND(bet_after_loss_ratio, 4)
        ELSE NULL
    END AS error_detail
FROM PROD.INT_LOSS_CHASING_INDICATORS
WHERE bet_after_loss_ratio < 0 OR bet_after_loss_ratio > 1
ORDER BY RANDOM()
LIMIT 10;

-- Should return 0 rows if all valid
```

---

### Step 3: Row Count Reconciliation
```sql
-- File: tests/validate_row_counts.sql
-- Ensure data flows correctly through pipeline layers

WITH layer_counts AS (
    SELECT 
        'Staging' AS layer,
        COUNT(*) AS row_count,
        COUNT(DISTINCT player_id) AS unique_players
    FROM STAGING.STG_BET_LOGS
    
    UNION ALL
    
    SELECT 
        'Intermediate',
        COUNT(*),
        COUNT(DISTINCT player_id)
    FROM PROD.INT_LOSS_CHASING_INDICATORS
    
    UNION ALL
    
    SELECT 
        'Marts',
        COUNT(*),
        COUNT(DISTINCT player_id)
    FROM PROD.RG_RISK_SCORES
)

SELECT
    layer,
    row_count,
    unique_players,
    CASE
        WHEN layer = 'Staging' THEN '✅ Baseline'
        WHEN layer = 'Intermediate' AND unique_players = (
            SELECT unique_players FROM layer_counts WHERE layer = 'Staging'
        ) THEN '✅ No players lost'
        WHEN layer = 'Marts' AND unique_players = (
            SELECT unique_players FROM layer_counts WHERE layer = 'Staging'
        ) THEN '✅ Complete pipeline'
        ELSE '❌ Data loss detected'
    END AS validation
FROM layer_counts
ORDER BY 
    CASE layer 
        WHEN 'Staging' THEN 1 
        WHEN 'Intermediate' THEN 2 
        WHEN 'Marts' THEN 3 
    END;
```

---

### Step 4: Compliance Validation

**Audit Trail Completeness**:
```sql
-- File: tests/validate_audit_trail.sql
-- Every HIGH/CRITICAL flag must have analyst sign-off

SELECT
    COUNT(*) AS total_flags,
    COUNT(analyst_id) AS with_analyst_signoff,
    COUNT(*) - COUNT(analyst_id) AS missing_signoff,
    CASE
        WHEN COUNT(*) = COUNT(analyst_id) THEN '✅ 100% HITL Coverage'
        ELSE '❌ Missing analyst sign-off on ' || 
             (COUNT(*) - COUNT(analyst_id)) || ' flags'
    END AS compliance_status
FROM PROD.RG_AUDIT_TRAIL
WHERE risk_category IN ('HIGH', 'CRITICAL')
  AND score_calculated_at >= CURRENT_DATE - INTERVAL '7 days';
```

**Customer Nudge Validation**:
```python
# File: tests/test_llm_safety_validator.py

def test_all_nudges_pass_safety_validation():
    """Ensure all generated customer nudges meet compliance requirements."""
    
    # Fetch recent nudges from audit trail
    nudges = fetch_recent_nudges(days=7)
    
    validator = LLMSafetyValidator(provider=provider, config=config, enable_llm_checks=True)
    
    failures = []
    for nudge in nudges:
        is_valid, violations = validator.validate_nudge(
            nudge_text=nudge['message'],
            player_context=nudge['player_data']
        )
        
        if not is_valid:
            failures.append({
                'nudge_id': nudge['id'],
                'player_id': nudge['player_id'],
                'violations': violations
            })
    
    assert len(failures) == 0, f"Found {len(failures)} nudges with violations: {failures}"
```

---

### Step 5: Performance Validation
```bash
#!/bin/bash

echo "=== Step 5: Performance Check ==="

# Measure execution time for risk scoring
echo "Testing risk score calculation for 10,000 players..."

start_time=$(date +%s)

dbt run --models marts.rg_risk_scores

end_time=$(date +%s)
duration=$((end_time - start_time))

# Target: <5 minutes (300 seconds)
# Alert threshold: >7 minutes (420 seconds)

if [ $duration -lt 300 ]; then
    echo "✅ Performance: ${duration}s (target: <300s)"
elif [ $duration -lt 420 ]; then
    echo "⚠️  Performance: ${duration}s (target: <300s, threshold: <420s)"
    echo "Consider investigating slow models"
else
    echo "❌ Performance: ${duration}s (exceeded 420s threshold)"
    echo "CRITICAL: Investigate performance issues immediately"
    exit 1
fi
```

---

## Output Format

Present results as consolidated checklist:
```bash
#!/bin/bash

echo "╔════════════════════════════════════════════════════════════╗"
echo "║         DK SENTINEL PIPELINE VALIDATION RESULTS           ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Run all validation steps and capture results
dbt_result=$(dbt test 2>&1)
weights_result=$(snowsql -q "$(cat tests/validate_risk_weights.sql)")
# ... [other checks]

# Display summary
echo "✅ dbt tests: 47/47 passed"
echo "✅ Risk weights: Sum = 1.00"
echo "✅ Thresholds: 0 invalid ratios detected"
echo "✅ Row counts: 500K bets → 10K players → 10K risk scores"
echo "✅ Compliance: 100% HITL coverage (2,347/2,347 flags)"
echo "⚠️  Performance: 6m 15s (target: <5m) - investigate int_market_drift"
echo ""
echo "Overall Status: 5 PASS, 1 WARNING, 0 FAIL"
```

---

## Failure Response Protocol

If ANY validation fails:

1. **Report specific failure with context**
```
   ❌ VALIDATION FAILED: Row Count Reconciliation
   
   Details:
   - Staging: 500,000 bets from 10,000 players
   - Intermediate: 9,847 players (153 missing)
   - Marts: 9,847 players
   
   Root Cause: 153 players have insufficient bet history (<2 bets)
              and are filtered out in int_loss_chasing_indicators
```

2. **Suggest root cause**
   - Data issue (missing/corrupt source data)
   - Logic bug (incorrect SQL/Python logic)
   - Performance issue (query timeout, resource contention)
   - Configuration issue (wrong parameters, missing environment variables)

3. **Propose fix (don't implement without approval)**
```
   Proposed Fix:
   
   Option A: Update int_loss_chasing_indicators to include players with >=1 bet
             (risk: may generate unreliable ratios with n=1)
   
   Option B: Document expectation that players with <2 bets are excluded
             (update row count reconciliation test to expect this)
   
   Option C: Create separate mart for "insufficient_data" players
             (allows tracking without generating invalid risk scores)
   
   Recommendation: Option B (document the business rule)
```

4. **Ask for decision**
```
   Should I:
   A) Implement Option B (update documentation + tests)
   B) Investigate further to understand why 153 players have <2 bets
   C) Pause and discuss with you before proceeding
```

---

## Integration with CI/CD
```yaml
# .github/workflows/validate-pipeline.yml

name: DK Sentinel Pipeline Validation

on:
  pull_request:
    paths:
      - 'dbt_project/**'
      - 'ai_services/**'
      - 'backend/**'

jobs:
  validate:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dbt
        run: pip install dbt-snowflake
      
      - name: Run Validation
        run: |
          # This invokes the skill via Claude Code
          claude -p "Run /validate-pipeline and report results"
      
      - name: Upload Results
        if: failure()
        uses: actions/upload-artifact@v3
        with:
          name: validation-failures
          path: validation-report.txt
```

# Workflow: Deploy dbt Model to Production

**When to use**: Promoting dbt models from development to production

**Estimated time**: 30-45 min for complete deployment

---

## Prerequisites

- [ ] Model tested locally (`dbt run --models model_name`)
- [ ] All tests pass (`dbt test --select model_name`)
- [ ] Code reviewed (PR approved)
- [ ] Documentation complete (schema.yml + column descriptions)
- [ ] Performance validated (<5 min for expected row count)

---

## Phase 1: Pre-Deployment Validation (10 min)

### Step 1: Run Full Test Suite Locally
````bash
cd dbt_project

# Run all upstream dependencies + target model
dbt run --models +model_name

# Run all tests
dbt test --select model_name

# Check for compilation errors
dbt compile --select model_name
````

**Expected Output**:
````
Completed successfully
Done. PASS=15 WARN=0 ERROR=0 SKIP=0 TOTAL=15
````

### Step 2: Validate Data Contracts
````bash
# For staging models with contracts
dbt run --models staging.stg_model_name --full-refresh

# Should fail if upstream schema changed unexpectedly
````

### Step 3: Check for Breaking Changes
````sql
-- Compare row counts before/after
SELECT COUNT(*) FROM DEV.MODEL_NAME;  -- Development
SELECT COUNT(*) FROM PROD.MODEL_NAME; -- Production (if exists)

-- Ensure counts are within expected range (±5%)
````

---

## Phase 2: Deployment Strategy (5 min)

### Step 4: Determine Deployment Type

**Type A: New Model** (doesn't exist in production)
- Deploy directly
- No downtime risk

**Type B: Model Update** (already exists in production)
- **Breaking change** (schema change, renamed columns): Blue-Green deployment
- **Non-breaking change** (logic update, new column): Direct deployment

**Type C: Incremental Model Update**
- Test incremental logic first
- Then deploy

### Step 5: Choose Deployment Method

#### **Method 1: Direct Deployment** (for Type A or non-breaking Type B)
````bash
# Switch to production target
dbt run --models model_name --target prod
````

#### **Method 2: Blue-Green Deployment** (for breaking Type B)
````bash
# Step 1: Deploy to new table name
dbt run --models model_name --vars '{table_suffix: "_v2"}' --target prod
# Creates: PROD.MODEL_NAME_V2

# Step 2: Validate new version
dbt test --select model_name --vars '{table_suffix: "_v2"}' --target prod

# Step 3: Swap (atomic operation)
# In Snowflake console:
ALTER TABLE PROD.MODEL_NAME RENAME TO PROD.MODEL_NAME_OLD;
ALTER TABLE PROD.MODEL_NAME_V2 RENAME TO PROD.MODEL_NAME;

# Step 4: Drop old version (after 24h validation period)
DROP TABLE PROD.MODEL_NAME_OLD;
````

#### **Method 3: Incremental Deployment** (for Type C)
````bash
# Step 1: Full-refresh in production to establish baseline
dbt run --models model_name --full-refresh --target prod

# Step 2: Test incremental logic
dbt run --models model_name --target prod

# Step 3: Verify row count increased correctly
````

---

## Phase 3: Post-Deployment Validation (10 min)

### Step 6: Verify Deployment Success
````sql
-- Check row count
SELECT COUNT(*) FROM PROD.MODEL_NAME;

-- Check data freshness
SELECT MAX(last_updated) FROM PROD.MODEL_NAME;
-- Should be within last hour

-- Spot check data quality
SELECT * FROM PROD.MODEL_NAME LIMIT 10;
````

### Step 7: Run Production Test Suite
````bash
dbt test --select model_name --target prod
````

**Expected Output**:
````
✅ All tests passed
````

### Step 8: Validate Downstream Dependencies
````bash
# Check which models depend on this one
dbt list --select model_name+ --target prod

# Run downstream models to ensure no breakage
dbt run --models model_name+ --exclude model_name --target prod
````

---

## Phase 4: Monitoring Setup (10 min)

### Step 9: Configure Snowflake Task (for scheduled runs)
````sql
-- Create task for daily incremental run
CREATE OR REPLACE TASK PROD.REFRESH_MODEL_NAME
  WAREHOUSE = COMPUTE_WH
  SCHEDULE = 'USING CRON 0 2 * * * America/New_York'  -- 2 AM ET daily
AS
  -- This would call dbt Cloud API or run dbt via stored proc
  CALL SYSTEM$DBT_RUN('model_name');

-- Enable task
ALTER TASK PROD.REFRESH_MODEL_NAME RESUME;
````

### Step 10: Set Up Monitoring Alerts
````sql
-- Alert if row count drops >10%
CREATE OR REPLACE ALERT PROD.MODEL_NAME_ROW_COUNT_ALERT
  WAREHOUSE = COMPUTE_WH
  SCHEDULE = 'USING CRON 0 9 * * * America/New_York'  -- 9 AM ET daily
  IF (
    SELECT 
      (current_count::FLOAT - baseline_count) / baseline_count AS pct_change
    FROM (
      SELECT COUNT(*) AS current_count FROM PROD.MODEL_NAME
    ),
    (
      SELECT AVG(row_count) AS baseline_count 
      FROM ANALYTICS.MODEL_ROW_COUNTS 
      WHERE model_name = 'MODEL_NAME' 
        AND date >= DATEADD(day, -7, CURRENT_DATE())
    )
    WHERE pct_change < -0.10  -- Alert if >10% drop
  )
THEN
  CALL SYSTEM$SEND_EMAIL(
    'data-team@draftkings.com',
    'ALERT: MODEL_NAME row count dropped >10%',
    'Check model for data quality issues'
  );

-- Enable alert
ALTER ALERT PROD.MODEL_NAME_ROW_COUNT_ALERT RESUME;
````

### Step 11: Log Deployment Metadata
````sql
-- Insert deployment record
INSERT INTO ANALYTICS.DBT_DEPLOYMENTS (
    model_name,
    deployed_at,
    deployed_by,
    git_commit_sha,
    row_count,
    deployment_method
)
SELECT
    'MODEL_NAME',
    CURRENT_TIMESTAMP(),
    'colby@draftkings.com',
    'abc123def',  -- From git rev-parse HEAD
    (SELECT COUNT(*) FROM PROD.MODEL_NAME),
    'direct'  -- or 'blue-green' or 'incremental'
;
````

---

## Phase 5: Documentation (5 min)

### Step 12: Update CLAUDE.md
````markdown
## Project Status

**Current Phase**: Week 4 - dbt transformations complete

**Recent Deployments**:
- 2026-02-15: Deployed int_loss_chasing_indicators.sql to production
  - Materialization: Incremental
  - Row count: 10,247 players
  - Performance: 1m 42s
  - Git commit: abc123def
````

### Step 13: Update dbt Docs
````bash
# Generate fresh documentation
dbt docs generate --target prod

# Serve documentation (for review)
dbt docs serve --port 8001
````

### Step 14: Notify Stakeholders
````markdown
**Email Template**:

Subject: [DEPLOYED] dbt Model: int_loss_chasing_indicators

Team,

We've deployed the new loss-chasing indicators model to production:

**Model**: int_loss_chasing_indicators
**Deployment Time**: 2026-02-15 14:30 ET
**Method**: Incremental deployment
**Performance**: 1m 42s for 10K players
**Row Count**: 10,247 players

**What This Enables**:
- Real-time loss-chasing detection (hourly refresh)
- Component score for composite risk calculation
- Analyst queue prioritization

**Next Steps**:
- Monitoring for 48 hours
- Integration into marts/rg_risk_scores scheduled for Friday

**Documentation**: https://dbt-docs.draftkings.com/models/int_loss_chasing_indicators

Questions? Reply to this thread or Slack #data-rg-analytics.

— Colby
````

---

## Rollback Procedure

If deployment causes issues:

### **Scenario 1: New Model (Type A)**
````sql
-- Simply drop the table
DROP TABLE PROD.MODEL_NAME;
````

### **Scenario 2: Blue-Green Deployment (Type B)**
````sql
-- Swap back to old version
ALTER TABLE PROD.MODEL_NAME RENAME TO PROD.MODEL_NAME_FAILED;
ALTER TABLE PROD.MODEL_NAME_OLD RENAME TO PROD.MODEL_NAME;
````

### **Scenario 3: Incremental Model (Type C)**
````bash
# Full-refresh from last known good state
dbt run --models model_name --full-refresh --target prod --vars '{restore_from: "2026-02-14"}'
````

---

## Success Criteria

- [ ] Model runs without errors in production
- [ ] All tests pass in production
- [ ] Row count within expected range
- [ ] Downstream models unaffected
- [ ] Monitoring alerts configured
- [ ] Documentation updated
- [ ] Stakeholders notified

---

## Common Pitfalls

❌ **Deploying without full-refresh first** (for incremental models): Always establish baseline

❌ **Not testing downstream dependencies**: Breaking changes cascade

❌ **Forgetting to enable Snowflake tasks**: Model won't refresh automatically

❌ **No rollback plan**: Always keep old version for 24-48 hours

---

## Post-Deployment Checklist (24 hours later)

- [ ] Monitor Snowflake task execution logs
- [ ] Check row count trends (should be stable)
- [ ] Review analyst feedback (if model affects interventions)
- [ ] Verify no downstream breakage
- [ ] Drop old version (if blue-green deployment)
- [ ] Update project status in CLAUDE.md

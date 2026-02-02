# Workflow: Validate Data Pipeline

## Validation Steps

**1. Data Quality Checks**
- Run all dbt tests: `dbt test`
- Check for nulls in critical columns
- Validate row counts vs. expected

**2. Business Logic Validation**
- Spot check 10 random players
- Compare manual calculation vs. model output
- Verify edge cases (zero bets, new players)

**3. Performance Validation**
- Check query execution time (<5 min for 10K players)
- Monitor Snowflake credit usage
- Verify incremental processing works

**4. Compliance Validation**
- Every AI flag has analyst_id
- Audit trail complete
- State-specific logic correct

**5. Integration Testing**
- API returns expected format
- Dashboard renders correctly
- End-to-end test (bet → risk score → dashboard)

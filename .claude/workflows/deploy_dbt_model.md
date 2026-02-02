# Workflow: Deploy dbt Model

## Pre-Deployment Checklist
- [ ] Model runs without errors
- [ ] All tests pass
- [ ] Documentation complete
- [ ] Code review completed

## Deployment Steps
1. Run full refresh in dev: `dbt run --full-refresh --select model_name`
2. Test in dev: `dbt test --select model_name`
3. Generate docs: `dbt docs generate`
4. Create PR with deployment plan
5. Get approval from data quality engineer
6. Merge to main
7. dbt Cloud runs automatically

## Post-Deployment
- Monitor Snowflake query performance
- Check data freshness SLA
- Review analyst feedback (first week)

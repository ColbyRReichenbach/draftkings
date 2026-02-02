# Workflow: Create New Risk Feature

## Steps

**1. Design & Specification** (Human-Led, 1-2 hours)
- Document business logic
- Define thresholds
- Identify data dependencies

**2. dbt Model Creation** (@dbt_architect, 30-60 min)
- Create intermediate model
- Implement incremental materialization
- Add data quality tests

**3. Feature Integration** (@dbt_architect, 30 min)
- Update marts/rg_risk_scores.sql
- Add new feature to composite calculation

**4. Compliance Review** (@compliance_validator, 15 min)
- Review for regulatory compliance
- Check state-specific thresholds

**5. Testing** (@data_quality_engineer, 1 hour)
- Unit tests
- Edge cases
- Integration tests

**6. AI Integration** (@python_backend_dev, 30 min)
- Update semantic_analyzer.py

**7. Dashboard** (@react_ui_developer, 1 hour)
- Add feature to Risk Breakdown component

**8. Documentation** (30 min)
- Generate dbt docs
- Update README

**9. Deployment Checklist** (15 min)
- [ ] Models run
- [ ] Tests pass
- [ ] Compliance approved
- [ ] Docs complete

**10. Post-Deployment Monitoring** (2 weeks)
- Monitor override rates
- Track false positives/negatives

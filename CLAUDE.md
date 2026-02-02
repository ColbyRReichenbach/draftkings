# DK SENTINEL: Responsible Gaming Intelligence System

## Project Overview

**Target Role**: Analyst II, Responsible Gaming Analytics at DraftKings (Job ID: jr13280)

**Purpose**: Portfolio project demonstrating data engineering, behavioral analytics, and AI integration capabilities specifically aligned with DraftKings' 2026 tech stack and responsible gaming mission.

**Core Problem**: 
DraftKings processes millions of daily wagers. Human analysts cannot manually review every high-risk behavioral pattern. This project demonstrates an AI-powered intervention triage system that reduces analyst review queue by 80% while increasing intervention accuracy by 40%.

## Technical Architecture

### Data Stack
- **Warehouse**: Snowflake (DraftKings' primary platform)
- **Transformation**: dbt Core 1.7+ (analytics engineering)
- **Processing**: Python 3.11 (PySpark + Pandas)
- **AI Layer**: Anthropic Claude API (semantic auditing)
- **Frontend**: React 18 + TypeScript + Tailwind CSS
- **Orchestration**: Snowflake Tasks + dbt Cloud

### Data Flow
```
Raw Bets (Snowflake) 
  → dbt Staging (views with data contracts)
  → dbt Intermediate (incremental - behavioral features)
  → dbt Marts (tables - risk scores)
  → Python AI Service (semantic auditing)
  → React Dashboard (analyst interface)
  → Audit Trail (compliance)
```

## Code Standards

### SQL/dbt
- CTEs over subqueries for readability
- Staging: views | Intermediate: incremental | Marts: tables
- Data contracts enforced on ALL staging models
- Every model needs: description, column docs, tests

### Python
- Type hints required on all functions
- Google-style docstrings
- Black formatter (100-char line length)
- Pydantic for request/response validation
- FastAPI for HTTP services

### React/TypeScript
- Functional components + hooks only
- TypeScript strict mode
- Tailwind utility classes
- React Query for data fetching
- DraftKings colors: #53B848, #000000, #F3701B

## Domain Context

### DraftKings 2026 Context
- **Gamalyze Integration** (Jan 2026): Mindway AI neuro-marker assessments
- **Chief RG Officer**: Lori Kalani (appointed April 2024)
- **LTV Strategy**: $1,500-$1,800 per player over 2-3 years

### Risk Score Weights (v1.0)
```python
COMPOSITE_RISK_WEIGHTS = {
    'loss_chase_score': 0.30,      # Strongest predictor
    'bet_escalation_score': 0.25,  # Second strongest
    'market_drift_score': 0.15,    # Moderate signal
    'temporal_risk_score': 0.10,   # High variance
    'gamalyze_risk_score': 0.20    # External validation
}
```

### Compliance Requirements
- **HITL Mandate**: Every AI flag requires analyst sign-off
- **Customer Tone**: Supportive, non-judgmental, emphasize autonomy
- **State Regulations**: MA (205 CMR 238.04), NJ, PA different thresholds
- **Data Retention**: 7-year audit trail

## File Conventions
- dbt: `{layer}_{entity}.sql` (e.g., `stg_bet_logs.sql`)
- Python: `snake_case.py`
- React: `PascalCase.tsx`
- Tests: `test_{module}.py` or `{Component}.test.tsx`

## Common Commands
```bash
# dbt
dbt run --models staging.*
dbt test --select model_name
dbt docs generate && dbt docs serve

# Python
uvicorn backend.main:app --reload
pytest --cov=backend tests/

# React
npm run dev
npm test
```

## Development Philosophy

### Progressive Implementation
1. Human designs (business logic, architecture)
2. Claude Code implements (SQL, Python, React)
3. Human validates (logic accuracy, not syntax)
4. Iterate until correct

### Context Management
- Don't load full spec - use skills for domain knowledge
- Reference context files as needed
- Invoke specific agents for specialized tasks
- Use workflows for multi-step procedures

## Success Metrics
- Code Quality: All tests pass, >80% coverage
- Performance: Risk scores for 10K players in <5 min
- Compliance: 100% audit trail coverage
- Documentation: Every decision has rationale

## Getting Started

**Domain Knowledge**: `.claude/skills/`
- dbt_transformations.md
- behavioral_analytics.md
- llm_integration.md
- compliance_validation.md
- react_dashboard.md

**Procedures**: `.claude/workflows/`
- create_new_risk_feature.md
- deploy_dbt_model.md
- validate_pipeline.md

**Specialized Tasks**: `.claude/agents/`
- @dbt_architect
- @compliance_validator
- @data_quality_engineer
- @python_backend_dev
- @react_ui_developer

---

**This configuration enables systematic AI-augmented development while maintaining clear ownership of analytical decisions.**

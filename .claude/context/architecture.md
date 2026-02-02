# System Architecture

## Data Flow
```
Raw Bets → Staging → Intermediate → Marts → AI Service → Dashboard → Audit
```

## Key Components

**1. Data Layer (Snowflake + dbt)**
- Raw: Source data
- Staging: Data contracts + cleaning
- Intermediate: Feature engineering (incremental)
- Marts: Final outputs (tables)

**2. AI Layer (Python + Claude API)**
- Semantic behavioral auditor
- LLM safety validator
- SAR generation logic

**3. Application Layer (FastAPI)**
- REST API endpoints
- Snowflake connection pooling
- Background job processing

**4. Presentation Layer (React)**
- Intervention queue
- Player detail view
- Audit trail log

## Performance Targets
- Risk scores: 10K players in <5 min
- API response: <500ms p95
- Dashboard load: <2 seconds

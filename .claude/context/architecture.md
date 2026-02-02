# System Architecture

**Purpose**: Technical design, data flow, deployment strategy, and infrastructure decisions

**Last Updated**: 2026-02-01

---

## High-Level Architecture
```
┌─────────────────────────────────────────────────────────────────┐
│                        USER LAYER                                │
│  ┌────────────────┐              ┌─────────────────┐            │
│  │ RG Analyst     │◄────────────►│ React Dashboard │            │
│  │ (Human Review) │              │ (Intervention   │            │
│  └────────────────┘              │  Queue)         │            │
│                                   └────────┬────────┘            │
└──────────────────────────────────────────┼─────────────────────┘
                                            │
                                            │ HTTPS/REST
                                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                     APPLICATION LAYER                            │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              FastAPI Backend (Python 3.11)              │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │   │
│  │  │ Analytics    │  │ Interventions│  │ AI Services  │  │   │
│  │  │ Router       │  │ Router       │  │ (Claude API) │  │   │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │   │
│  └─────────┼──────────────────┼──────────────────┼──────────┘   │
└────────────┼──────────────────┼──────────────────┼──────────────┘
             │                  │                  │
             │                  │                  │ Anthropic API
             │                  │                  ▼
             │                  │         ┌────────────────────┐
             │                  │         │ Claude Sonnet 3.5  │
             │                  │         │ (Semantic Auditor) │
             │                  │         └────────────────────┘
             │                  │
             ▼                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                       DATA LAYER                                 │
│                   Snowflake Data Warehouse                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   STAGING    │  │     PROD     │  │  ANALYTICS   │         │
│  │  (Views)     │  │ (Tables/Inc) │  │   (Views)    │         │
│  ├──────────────┤  ├──────────────┤  ├──────────────┤         │
│  │ stg_bet_logs │  │ int_loss_    │  │ analyst_     │         │
│  │ stg_players  │  │  chasing     │  │  performance │         │
│  │ stg_gamalyze │  │ int_market_  │  │ llm_daily_   │         │
│  │              │  │  drift       │  │  costs       │         │
│  │              │  │ rg_risk_     │  │              │         │
│  │              │  │  scores      │  │              │         │
│  │              │  │ rg_audit_    │  │              │         │
│  │              │  │  trail       │  │              │         │
│  └──────┬───────┘  └──────┬───────┘  └──────────────┘         │
│         │                 │                                     │
│         │  dbt Core       │                                     │
│         └─────────────────┘                                     │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐   │
│  │            Snowflake Tasks (Scheduled Jobs)             │   │
│  │  • Hourly: REFRESH_INT_MODELS (:05)                     │   │
│  │  • Hourly: REFRESH_MARTS (:30)                          │   │
│  │  • Daily: REFRESH_ANALYTICS (2:00 AM ET)                │   │
│  └────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Technology Stack

### Data Layer
| Component | Technology | Justification |
|-----------|-----------|---------------|
| **Data Warehouse** | Snowflake | Industry standard for analytics; columnar storage optimizes dbt models; automatic scaling |
| **Transformation** | dbt Core 1.7+ | SQL-based transformations; version control; testing framework; documentation generation |
| **Orchestration** | Snowflake Tasks | Native scheduling; no external dependencies; cost-effective for hourly jobs |

### Application Layer
| Component | Technology | Justification |
|-----------|-----------|---------------|
| **Backend Framework** | FastAPI 0.109+ | Async support; automatic API docs; Pydantic validation; high performance |
| **Language** | Python 3.11 | Type hints; async/await; rich ecosystem (pandas, pydantic, anthropic SDK) |
| **Database Driver** | snowflake-connector-python | Official Snowflake connector; connection pooling |
| **LLM Integration** | Anthropic Claude API | State-of-the-art language understanding; 200K context window; JSON mode |

### Frontend Layer
| Component | Technology | Justification |
|-----------|-----------|---------------|
| **Framework** | React 18 + Vite | Modern bundling; fast HMR; component-based architecture |
| **Language** | TypeScript 5.0+ | Type safety; better IDE support; catches errors at compile time |
| **Styling** | Tailwind CSS 3.4+ | Utility-first; DraftKings brand colors; responsive by default |
| **State Management** | Zustand 4.5+ | Minimal boilerplate; TypeScript-friendly; devtools support |
| **Server State** | React Query 5.0+ | Caching; background refetch; optimistic updates |
| **Testing** | Vitest + React Testing Library | Fast; React 18 compatible; component testing |

---

## Data Flow

### 1. Ingestion (Upstream → Staging)

**Simulated Sources** (for portfolio):
```python
# scripts/generate_synthetic_data.py
# Generates realistic betting patterns using Faker + statistical distributions

def generate_player_cohorts():
    """
    90% low-risk (normal betting patterns)
    8% medium-risk (occasional loss-chasing)
    1.5% high-risk (consistent escalation)
    0.5% critical (severe problem gambling indicators)
    """
    pass

# Output: CSV files
# - players.csv (10,000 rows)
# - bets.csv (500,000 rows)
# - gamalyze_scores.csv (10,000 rows)
```

**Load to Snowflake**:
```sql
-- Load via Snowflake COPY INTO
COPY INTO RAW.BET_TRANSACTIONS
FROM @my_s3_stage/bets.csv
FILE_FORMAT = (TYPE = 'CSV' SKIP_HEADER = 1);
```

---

### 2. Transformation (dbt Pipeline)

**Staging Layer** (Views):
```sql
-- models/staging/stg_bet_logs.sql
-- Purpose: Clean, standardize, enforce data contracts

SELECT
    bet_id,
    player_id,
    bet_timestamp,
    UPPER(TRIM(sport_category)) AS sport_category,  -- Standardization
    bet_amount,
    outcome
FROM {{ source('raw', 'bet_logs') }}
WHERE bet_timestamp IS NOT NULL  -- Data quality filter
  AND bet_amount > 0
```

**Intermediate Layer** (Incremental Tables):
```sql
-- models/intermediate/int_loss_chasing_indicators.sql
-- Purpose: Behavioral feature engineering

WITH player_bet_sequence AS (
    SELECT
        player_id,
        bet_timestamp,
        outcome,
        LAG(outcome) OVER (
            PARTITION BY player_id 
            ORDER BY bet_timestamp
        ) AS prev_outcome
    FROM {{ ref('stg_bet_logs') }}
    
    {% if is_incremental() %}
    WHERE bet_timestamp > (SELECT MAX(last_bet_timestamp) FROM {{ this }})
    {% endif %}
)

SELECT
    player_id,
    COUNT(*) FILTER (WHERE prev_outcome = 'loss') AS bets_after_loss,
    COUNT(*) AS total_bets,
    bets_after_loss::FLOAT / NULLIF(total_bets, 0) AS bet_after_loss_ratio
FROM player_bet_sequence
GROUP BY player_id
```

**Marts Layer** (Tables):
```sql
-- models/marts/rg_risk_scores.sql
-- Purpose: Final risk scores for consumption

SELECT
    lc.player_id,
    (
        (normalize(lc.bet_after_loss_ratio, 0.40, 0.75) * 0.30) +
        (normalize(lc.bet_escalation_ratio, 1.2, 2.0) * 0.25) +
        (md.market_drift_score * 0.15) +
        (md.temporal_risk_score * 0.10) +
        (g.gamalyze_risk_score * 0.20)
    ) AS composite_risk_score,
    CASE
        WHEN composite_risk_score >= 0.80 THEN 'CRITICAL'
        WHEN composite_risk_score >= 0.60 THEN 'HIGH'
        WHEN composite_risk_score >= 0.40 THEN 'MEDIUM'
        ELSE 'LOW'
    END AS risk_category
FROM {{ ref('int_loss_chasing_indicators') }} lc
LEFT JOIN {{ ref('int_market_drift_detection') }} md USING (player_id)
LEFT JOIN {{ ref('int_gamalyze_composite') }} g USING (player_id)
```

---

### 3. API Layer (Backend → Frontend)

**Endpoint**: `POST /api/analytics/analyze-player`

**Request**:
```json
{
    "player_id": "PLR_1234_MA",
    "include_history": false,
    "generate_nudge": true
}
```

**Backend Processing**:
1. Query Snowflake for latest risk scores
2. If `generate_nudge=true`: Call Claude API for semantic explanation
3. Validate response with `LLMSafetyValidator`
4. Return structured JSON

**Response**:
```json
{
    "player_id": "PLR_1234_MA",
    "composite_risk_score": 0.82,
    "risk_category": "HIGH",
    "component_scores": {
        "loss_chase": 0.78,
        "bet_escalation": 0.85,
        "market_drift": 0.45,
        "temporal_risk": 0.62,
        "gamalyze": 0.75
    },
    "ai_explanation": "Player exhibits severe loss-chasing with 85% of bets placed after losses and 2x bet size escalation. Market drift is moderate (primarily NFL to Table Tennis). Gamalyze assessment shows high sensitivity to loss (82/100).",
    "recommended_action": "24-hour cooling-off period with supportive nudge",
    "generated_at": "2026-01-15T23:30:00Z"
}
```

---

### 4. Frontend Rendering

**React Query Fetch**:
```typescript
// src/api/queries.ts
export const useInterventionQueue = (params: InterventionQueueParams) => {
    return useQuery({
        queryKey: ['intervention-queue', params],
        queryFn: async () => {
            const response = await fetch(`${API_BASE_URL}/api/interventions/queue`);
            return response.json();
        },
        refetchInterval: 30000,  // Auto-refresh every 30s
    });
};
```

**Component Render**:
```typescript
// src/pages/InterventionQueue.tsx
const { data: cases, isLoading } = useInterventionQueue({ riskCategory: 'HIGH' });

return (
    <div className="grid gap-4">
        {cases?.map(case_ => (
            <RiskCaseCard key={case_.player_id} case={case_} onAction={handleAction} />
        ))}
    </div>
);
```

---

## Deployment Strategy

### Development Environment

**Local Setup**:
```bash
# 1. Snowflake (Free Trial Account)
# Database: RG_ANALYTICS_DEV
# Warehouse: COMPUTE_WH_DEV

# 2. dbt
cd dbt_project
dbt run --target dev
dbt test

# 3. Backend
cd backend
uvicorn main:app --reload --port 8000

# 4. Frontend
cd frontend
npm run dev  # Runs on localhost:5173
```

---

### Production Deployment

**Option 1: Cloud-Based (Recommended for Portfolio)**

**Backend**: Railway / Render  
**Frontend**: Vercel  
**Database**: Snowflake (Trial → Production upgrade if needed)

**Cost Estimate**:
- Snowflake: $0-25/month (trial credits)
- Railway: $5/month (hobby tier)
- Vercel: $0 (free tier sufficient)
- Anthropic API: ~$1-5/month (development usage)

**Total**: <$35/month

---

**Option 2: Local Demo (Cost-Free)**

**Setup**:
- Run backend locally (uvicorn)
- Run frontend locally (Vite dev server)
- Record demo video for portfolio
- Screenshots for GitHub README

**Pros**: Zero hosting costs  
**Cons**: No live demo URL for recruiters

---

### CI/CD Pipeline (Future Enhancement)
```yaml
# .github/workflows/test-and-deploy.yml
name: DK Sentinel CI/CD

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test-dbt:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dbt
        run: pip install dbt-snowflake
      
      - name: Run dbt tests
        run: |
          cd dbt_project
          dbt test --target prod
  
  test-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
      
      - name: Install dependencies
        run: pip install -r backend/requirements.txt
      
      - name: Run pytest
        run: pytest backend/tests/ --cov=backend
  
  test-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Node
        uses: actions/setup-node@v3
        with:
          node-version: '20'
      
      - name: Install dependencies
        run: cd frontend && npm install
      
      - name: Run tests
        run: cd frontend && npm test
  
  deploy:
    needs: [test-dbt, test-backend, test-frontend]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - name: Deploy Backend to Railway
        run: railway up
      
      - name: Deploy Frontend to Vercel
        run: vercel --prod
```

---

## Performance Optimization

### Database Optimization

**1. Cluster Keys** (for large tables):
```sql
ALTER TABLE PROD.RG_RISK_SCORES 
CLUSTER BY (player_id, DATE_TRUNC('day', score_calculated_at));
```

**Impact**: 40% query time reduction for filtered queries

---

**2. Incremental Materialization**:
```sql
-- Full refresh: 15 minutes for 10K players
-- Incremental: 2 minutes for daily delta (87% reduction)
```

---

**3. Query Optimization**:
```sql
-- Use QUALIFY instead of subqueries (Snowflake-specific)
SELECT player_id, sensitivity_to_loss
FROM stg_gamalyze_scores
QUALIFY ROW_NUMBER() OVER (PARTITION BY player_id ORDER BY assessment_date DESC) = 1
```

**Impact**: Single table scan vs. double scan

---

### API Optimization

**1. Connection Pooling**:
```python
# backend/database.py
class DatabasePool:
    def __init__(self):
        self.pool = snowflake.connector.connect(
            pool_size=5,  # Reuse connections
            pool_timeout=10
        )
```

---

**2. Response Caching**:
```python
# Cache risk scores for 5 minutes (reduces duplicate queries)
@lru_cache(maxsize=100)
def get_risk_score(player_id: str) -> RiskAssessment:
    pass
```

---

**3. Async Processing**:
```python
# Use async/await for concurrent API calls
async def batch_analyze_players(player_ids: list[str]) -> list[RiskAssessment]:
    tasks = [analyze_player(pid) for pid in player_ids]
    return await asyncio.gather(*tasks)
```

---

### Frontend Optimization

**1. React Query Caching**:
```typescript
// Cache server state for 30 seconds
staleTime: 30000,
cacheTime: 300000,  // Keep in memory for 5 min
```

---

**2. Code Splitting**:
```typescript
// Lazy load detail view
const PlayerDetailView = lazy(() => import('./components/PlayerDetailView'));
```

---

**3. Virtualization** (for large lists):
```typescript
// Use react-window for 100+ cases
import { FixedSizeList } from 'react-window';
```

---

## Monitoring & Observability

### Database Monitoring
```sql
-- Create monitoring table
CREATE TABLE ANALYTICS.MODEL_PERFORMANCE_LOG (
    model_name VARCHAR(100),
    execution_timestamp TIMESTAMP_NTZ,
    row_count INT,
    execution_time_seconds INT,
    status VARCHAR(20)
);

-- Log dbt runs
INSERT INTO ANALYTICS.MODEL_PERFORMANCE_LOG
SELECT 
    'int_loss_chasing_indicators',
    CURRENT_TIMESTAMP(),
    COUNT(*),
    DATEDIFF('second', start_time, end_time),
    'SUCCESS'
FROM model_run_metadata;
```

---

### API Monitoring
```python
# backend/middleware/logging.py
import time
import logging

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    logging.info(f"{request.method} {request.url.path} - {response.status_code} - {duration:.2f}s")
    
    return response
```

---

### Alerts

**Snowflake Alert** (row count drop):
```sql
CREATE ALERT row_count_drop_alert
  WAREHOUSE = COMPUTE_WH
  SCHEDULE = '60 MINUTE'
IF (
    SELECT (current_count - baseline_count)::FLOAT / baseline_count
    FROM (SELECT COUNT(*) AS current_count FROM PROD.RG_RISK_SCORES),
         (SELECT AVG(row_count) AS baseline_count FROM ANALYTICS.MODEL_PERFORMANCE_LOG)
    WHERE pct_change < -0.10
)
THEN CALL SYSTEM$SEND_EMAIL(...);
```

---

## Security Considerations

### API Security
- **CORS**: Restricted to frontend domain only
- **Rate Limiting**: 100 requests/minute per IP (future: API keys)
- **Input Validation**: Pydantic models reject malformed requests
- **SQL Injection**: Parameterized queries only (no string concatenation)

### Data Security
- **PII Handling**: Player IDs are pseudonymized (PLR_####_ST format)
- **Audit Trail**: All analyst actions logged with timestamp + analyst_id
- **Access Control**: Snowflake role-based access (DEV vs PROD schemas)

### LLM Security
- **Prompt Injection Defense**: Multi-layer safety validation
- **Content Filtering**: Regex + LLM checks for prohibited language
- **API Key Management**: Environment variables (never committed to git)

---

## Cost Analysis

### Development Phase (8 weeks)
| Service | Cost/Month | Total (2 months) |
|---------|-----------|------------------|
| Snowflake (Trial) | $0 | $0 |
| Anthropic API | $5 | $10 |
| Hosting (Local) | $0 | $0 |
| **Total** | **$5/month** | **$10** |

### Production (if deployed)
| Service | Cost/Month |
|---------|-----------|
| Snowflake (XS warehouse) | $25 |
| Railway (Backend) | $5 |
| Vercel (Frontend) | $0 |
| Anthropic API | $10-20 |
| **Total** | **$40-50/month** |

**Note**: For portfolio purposes, local development + demo video avoids hosting costs entirely.

---

## Scalability Roadmap

**Current Capacity**: 10K players, 500K bets/month  
**Target Production**: 100K players, 5M bets/month

### Scaling Strategies

**1. Database** (Snowflake auto-scales):
- Increase warehouse size: XS → Small (2x compute)
- Add clustering keys to all large tables
- Partition by date for historical data

**2. API** (Horizontal scaling):
- Deploy multiple backend instances (Railway auto-scaling)
- Add Redis for shared cache across instances
- Implement request queue for async processing

**3. Frontend** (CDN + Edge caching):
- Vercel Edge Functions for API routes
- Static asset caching (images, CSS)
- Service worker for offline support

---

## Future Enhancements

**Phase 2 Features** (Post-Portfolio):
1. **Real-time streaming**: Kafka + Snowpipe for <1min latency
2. **Advanced ML**: Gradient boosting for hybrid scoring
3. **A/B testing framework**: Analyst feedback loop automation
4. **Mobile app**: React Native version of dashboard
5. **Multi-language support**: Spanish/Portuguese nudges

---

**For business logic and calculations, see**: `.claude/context/business_logic.md`  
**For job alignment and success criteria, see**: `.claude/context/stakeholder_requirements.md`

# DK SENTINEL: Responsible Gaming Intelligence System

**Target Role**: Analyst II, Responsible Gaming Analytics at DraftKings (Job ID: jr13280)

**Project Type**: Portfolio project demonstrating data engineering, behavioral analytics, and AI integration

---

## Quick Context

**Problem**: DraftKings processes millions of daily wagers. Analysts can't manually review every high-risk pattern.

**Solution**: AI-powered triage system reducing analyst queue by 80% while increasing intervention accuracy by 40%.

**Tech Stack**: Snowflake + dbt Core + Python (FastAPI) + React + OpenAI API

**LLM Defaults**: `gpt-4o-mini` for high-volume tasks, `gpt-4.1` for reasoning/explanations  
Override via `LLM_MODEL_FAST` and `LLM_MODEL_REASONING` if cost/latency requires.

---

## Code Standards

### SQL/dbt
- **Materialization**: Staging = views | Intermediate = incremental | Marts = tables
- **Data Contracts**: ALWAYS enforce on staging models (`contract: {enforced: true}`)
- **Testing**: Minimum 1 test per model, target 90% column coverage
- **Incremental Strategy**: MUST include time predicate in `{% if is_incremental() %}` block
- **Documentation**: Every model needs description + column docs + business logic in meta tags

### Python
- **Type Hints**: Required on ALL function signatures
- **Docstrings**: Google-style format
- **Formatting**: Black with 100-char line length
- **Validation**: Pydantic models for all API requests/responses
- **Framework**: FastAPI for HTTP services

### React/TypeScript
- **Components**: Functional with hooks only (no class components)
- **Type Safety**: TypeScript strict mode enabled
- **Styling**: Tailwind utility classes (minimize custom CSS)
- **Data Fetching**: React Query for server state
- **State Management**: Zustand for global client state
- **DraftKings Colors**: `#53B848` (green), `#000000` (black), `#F3701B` (orange)

---

## Domain Knowledge

### Risk Score Weights (v1.0 - Subject to Active Learning)
```python
COMPOSITE_RISK_WEIGHTS = {
    'loss_chase_score': 0.30,      # Strongest predictor (68% of self-excluded)
    'bet_escalation_score': 0.25,  # r=0.72 with Gamalyze sensitivity to loss
    'market_drift_score': 0.15,    # Moderate signal
    'temporal_risk_score': 0.10,   # High variance (shift workers confound)
    'gamalyze_risk_score': 0.20    # External validation
}
```

### Critical Thresholds

**Loss-Chasing Detection**:
- Bet After Loss Ratio: <0.40 normal, 0.60-0.75 high, >0.75 critical
- Bet Escalation Ratio: <1.2 normal, 1.5-2.0 high, >2.0 critical

**Market Drift**:
- Horizontal: >3x baseline sport diversity = risky
- Vertical: >50% market tier drop (1.0 → 0.5) = risky  
- Temporal: 2-6 AM betting when normally 7-9 PM = risky

### Compliance Requirements

**Human-in-the-Loop (HITL)**:
- Every AI flag REQUIRES analyst sign-off
- Audit trail MUST capture: analyst_id, timestamp, decision, rationale

**Customer Communication**:
- Tone: Supportive, non-judgmental (never "irresponsible", "addicted")
- Required: Link to RG Center (rg.draftkings.com)
- Required: Autonomy language ("you can choose" not "you must")
- Prohibited: Specific dollar amounts, medical language, threats

**State-Specific**:
- MA (205 CMR 238.04): Flag bets >10x rolling avg
- NJ: Mandatory timeout after 3+ flags in 30 days
- PA: Referral required for 3+ self-exclusion reversals in 6 months

---

## File Naming Conventions

- **dbt**: `{layer}_{entity}.sql` → `stg_bet_logs.sql`, `int_loss_chasing_indicators.sql`
- **Python**: `snake_case.py`
- **React**: `PascalCase.tsx`
- **Tests**: `test_{module}.py`, `{Component}.test.tsx`

---

## Development Workflow

### 1. Start Every Complex Task in Plan Mode
Press **Shift+Tab twice** to enter Plan Mode before implementing:
- New dbt models with complex logic
- AI integration features
- Multi-file refactoring
- Any feature you don't fully understand

**Why**: Prevents "ready, fire, aim". Forces structured thinking. Reduces debugging cycles by 60-80%.

### 2. Use Voice Dictation for Detailed Prompts
Press **Fn+Fn** (Mac) to speak prompts instead of typing:
- 3x faster than typing
- More detailed requirements
- Fewer typos = better responses

### 3. Delegate to Subagents
Use `@agent-name` or "use subagents" to offload:
- Testing → `@data-quality-tester`
- Compliance review → `@compliance-validator`
- Code review → `@dbt-architect`

**Why**: Keeps main context clean and focused.

### 4. Use Skills for Repetitive Workflows
Type `/skill-name` for common tasks:
- `/validate-pipeline` - Full test suite + validation
- `/dbt-docs` - Generate and serve documentation
- `/commit-changes` - Smart git commit with context

---

## Self-Correction Protocol

**CRITICAL**: After EVERY correction from me, you MUST propose a CLAUDE.md update.

**Template**:
> "I've updated my understanding. To prevent this mistake, I should add to CLAUDE.md:
> 
> ```
> [Specific rule based on correction]
> ```
> 
> Should I update CLAUDE.md with this rule?"

**Examples of corrections that trigger updates**:
- "That SQL syntax is wrong for Snowflake" → Add Snowflake-specific pattern
- "Don't use SELECT * in production" → Add to code standards  
- "Customer nudges must include RG link" → Add to compliance checklist
- "Risk weights must sum to 1.0" → Add to business logic validation

This creates a **self-improving feedback loop** where the project gets smarter over time.

---

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

---

## Success Metrics

- **Code Quality**: All tests pass, >80% Python coverage, >90% dbt column coverage
- **Performance**: Risk scores for 10K players in <5 min
- **Compliance**: 100% audit trail coverage, all nudges validated
- **Documentation**: Every decision has documented rationale

---

## Project Status

**Current Phase**: Week 9 extension complete (Ops-grade analytics + SQL execution + queue persistence)
- [x] Week 1-2: Data foundation (synthetic generation + Snowflake setup) — Week 1 complete; Week 2 complete
- [x] Week 3-4: dbt transformations (staging → intermediate → marts) — Week 3 complete; Week 4 complete
- [x] Week 5: AI integration (semantic auditor + safety validator)
- [x] Week 6: Dashboard foundation (React components + mock data + tabs)
- [x] Week 7: HITL-first UI + AI assist (analyst notes + LLM transparency)
- [x] Week 8: Case File (HITL + AI + SQL + lifecycle flow)
- [x] Week 9: Integration, testing & documentation
- [x] Week 9 Extension: Persistent queue batching + SQL execution + trigger caching + manager analytics

**Recent Lessons** (Most Recent First):
- 2026-02-05: SQL drafts must reference live DuckDB schema snapshots and redact/avoid PII before execution.
- 2026-02-03: Always record regulatory trigger checks alongside composite-score selections in HITL reviews.

---

**For detailed workflows, see `claude/skills/`**
**For specialized agents, see `claude/agents/`**
**For step-by-step procedures, see `claude/workflows/`**

# DK Sentinel: Weekly Progress Tracker

## Week 1: Data Foundation ✓ COMPLETE

**Goals**:
- [x] Generate synthetic data (10K players, ~500K bets)
- [x] Create dbt project structure (medallion: staging → intermediate → marts)
- [x] Load data to DuckDB (dev target; Snowflake profile stubbed for Week 5 migration)
- [x] Validate staging layer (51/51 dbt tests passing)

**Delivered**:
- 3 staging views: `stg_bet_logs`, `stg_player_profiles`, `stg_gamalyze_scores`
- Full data contract enforcement via `schema.yml` (unique, not_null, accepted_values, relationships, accepted_range)
- Data generation pipeline: `python -m data_generation` → `python scripts/load_to_duckdb.py`
- SQL compatibility score 100/100 — staging layer is Snowflake-portable as-is
- Pipeline executes in <4s on DuckDB (models 0.7s + tests 2.9s)

**Bug fixed**: `schema.yml` `accepted_values` for `risk_cohort` had `CRITICAL_RISK`; generator emits `critical` → `UPPER()` → `CRITICAL`. Corrected to match.

**Known issues (not blocking)**:
- Bet count was ~216K (below target). **Resolved** by extending the generation window to 90 days; current output ~500K bets.
- Generator validation Tier 3 (distributions) and Tier 4 (correlations) fail. Two of three target correlations are attenuated by the state machine in `bet_generator.py`. Documented in `DATA_GENERATION_METHODOLOGY.md`.
- Edge case injection is stubbed — 10 edge cases defined in `edge_cases.py` but not yet applied to output.

**Next Week Preview**: Intermediate models (loss-chasing indicators, market drift features)

---

## Week 2: Intermediate Models ✓ COMPLETE

**Goals**:
- [x] Build loss-chasing indicators (bet-after-loss + escalation)
- [x] Build market drift indicators (horizontal/vertical/temporal)
- [x] Build Gamalyze composite score (latest 90-day assessment)
- [x] Enforce tests + schema documentation for new models
- [x] Run full dbt test suite

**Delivered**:
- Intermediate models:
  - `int_loss_chasing_indicators`
  - `int_market_drift_indicators`
  - `int_gamalyze_composite`
- Added local `accepted_range` test macro (offline-safe; no dbt_utils dependency)
- Singular tests:
  - `assert_loss_chasing_min_bets`
  - `assert_loss_chasing_ratios_valid`
  - `assert_market_drift_ratios_valid`
  - `assert_gamalyze_score_bounds`
- Validation: `dbt test` 101/101 passing

**Notes**:
- Removed external dbt package dependency to keep offline dev environment stable.

**Next Week Preview**: Marts layer (composite risk scores + categories)

---

## Week 3: Marts Layer ✓ COMPLETE

**Goals**:
- [x] Build composite risk score mart (`rg_risk_scores`)
- [x] Add marts schema tests + singular validations
- [x] Validate full dbt test suite

**Delivered**:
- `rg_risk_scores` marts model with normalization + weight application
- Tests:
  - `assert_component_scores_in_range`
  - `assert_risk_weights_sum_to_one`
  - `assert_risk_category_thresholds`
- Validation: `dbt test` 121/121 passing

**Next Week Preview**: Compliance review + analyst workflow integration

---

## Week 4: Compliance + Analyst Workflow ✓ COMPLETE

**Delivered**:
- Compliance foundation: `rg_audit_trail`
- Analyst queue: `rg_intervention_queue`
- Full dbt validation (152/152 tests)
- Data generator tuning to better surface HIGH/CRITICAL risk categories (documented rationale)
- Completed HITL analyst review with 15 cases in `docs/HITL_REVIEW.md` (including regulatory trigger cross-checks)

---

## Week 5: AI Integration ✓ COMPLETE

**Delivered**:
- OpenAI-first LLM integration (`ai_services/` + `backend/`)
- Semantic auditor + safety validator with provider-agnostic interfaces
- FastAPI endpoints: `/api/ai/semantic-audit` and `/api/ai/validate-nudge`
- Pydantic request/response schemas for LLM I/O
- Integration docs in `docs/LLM_INTEGRATION.md`
- Unit tests for auditor + safety validator (pytest)

**Validation**:
- `pytest` 4/4 passing

---

## Week 6: Dashboard Foundation ✓ COMPLETE

**Delivered**:
- React + TypeScript + Tailwind + Vite scaffold under `frontend/`
- Single-page tab navigation (Queue, Case Detail, Analytics, Audit Trail)
- Mock data layer + typed hooks with React Query
- Zustand state for queue filters + active tab
- UI components for cards, detail panel, charts, and audit table
- AI action buttons wired to OpenAI endpoints (semantic audit + nudge validation)
- Component tests with Vitest + RTL

---

## Week 7: HITL-First UI + AI Assist ✓ COMPLETE

**Delivered**:
- Updated AI button copy to “Draft AI Summary” (assistive framing)
- Analyst notes panel with action selection + submit workflow
- LLM transparency log (prompt + output history)
- DuckDB-backed endpoints for notes and prompt logging
- AI endpoint guardrails (503 if key missing)

**Roadmap Update**:
- Live data integration moved to Week 8 alongside final validation and docs.

---

## Week 8: Case File (HITL + AI + SQL) ✓ COMPLETE

**Delivered**:
- Full-page Case File view inside Audit Trail tab (Medium/High/Critical only)
- Hybrid SQL assistant (LLM draft → analyst edit → log)
- Query log + unified timeline (notes + AI + SQL)
- Client-side PDF export of Case File
- DuckDB table + FastAPI endpoints for SQL draft + query logging
- Case lifecycle flow: Start Case Review → Audit Trail workbench → Submit Decision (status persisted)
- Queue hygiene: active Audit Trail cases are excluded from Queue

**Roadmap Update**:
- Live data integration moved to Week 9 along with full validation + docs polish.

**Notes**:
- `npm audit` flags `jspdf`/`vite` issues that require breaking upgrades. Deferred; dev server locked to `127.0.0.1` for mitigation.

---

## Week 9: Live Integration + Prompt Routing ✓ COMPLETE

**Delivered**:
- Live API integration for Queue, Case Detail, Audit Trail, and Case File (mock data removed for those views)
- Prompt router with routing transparency (SQL Draft vs Regulatory vs External vs General)
- Snowflake-safe SQL enforcement for drafted queries
- Route + tool logging added to LLM transparency log
- Updated UI to show router decisions and Snowflake-only guidance

**Validation**:
- `pytest` (router + snowflake validator)
- `npm test` (UI + routing panel)

**Roadmap Update**:
- Portfolio polish and final packaging remain as optional post-Week 9 enhancements.

---

[Continue through Week 10 if needed]

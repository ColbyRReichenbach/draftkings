# Technical Deep Dive

![Architecture](https://img.shields.io/badge/Architecture-API%20%2B%20Warehouse%20%2B%20UI-0A66C2)
![Data Mode](https://img.shields.io/badge/Data_Mode-Live%20%7C%20Static-444)
![SQL Safety](https://img.shields.io/badge/SQL-Read--Only%20Guardrails-2E7D32)
![AI Design](https://img.shields.io/badge/AI-HITL%20%2B%20Routed-6A1B9A)

## Objective
This system is built to simulate analyst-grade responsible gaming operations with auditable evidence and constrained AI assistance.

## Infrastructure Decision Record
### DuckDB Local Runtime
- **Decision:** Use DuckDB as the local analytical/runtime store.
- **Why:** Fast setup, strong SQL support, deterministic local reproducibility, and easy sharing via a single DB artifact.
- **Tradeoff:** Does not provide enterprise warehouse controls out of the box (for example RBAC layers and managed scaling).

### Snowflake Syntax Enforcement
- **Decision:** Keep SQL drafting/execution Snowflake-oriented with explicit syntax validation.
- **Why:** Align analyst query habits with target warehouse semantics while still executing locally in DuckDB.
- **Tradeoff:** Some dialect differences require rewrite/normalization logic before local execution.

### Prompt Router Taxonomy
- **Decision:** Route prompts into `SQL_DRAFT`, `REGULATORY_CONTEXT`, `EXTERNAL_CONTEXT`, `GENERAL_ANALYSIS`.
- **Why:** Improve transparency, reduce misuse of tools, and keep logs auditable by intent.
- **Tradeoff:** Keyword routing is deterministic but less adaptive than a retrieval/classifier-based router.

### Read-Only SQL Guardrails
- **Decision:** Enforce `SELECT`-only behavior, block prohibited statements, block PII fields, and cap result size.
- **Why:** Preserve analyst safety/governance and avoid accidental data mutation or sensitive-field exposure.
- **Tradeoff:** Analysts may need extra query iterations when blocked by strict controls.

### Static + Live Separation
- **Decision:** Implement `VITE_DATA_MODE` split between API-backed and fixture-backed modes.
- **Why:** Support reliable demos without backend dependency while preserving a realistic live workflow path.
- **Tradeoff:** Static mode can drift from live behavior unless fixture export and parity checks stay disciplined.

## Production-Mirroring Choices
- API-driven workflow mirrors analyst operations through explicit endpoints for queue triage, case workbench actions, and submission.
- Auditability is modeled via persisted logs (`rg_query_log`, `rg_llm_prompt_log`, `rg_trigger_check_log`, status/note/nudge logs).
- Trigger checks run through deterministic SQL logic and cache behavior similar to controlled production checks.
- SQL governance is enforced via read-only execution constraints plus Snowflake-style syntax validation.

## Source-Backed Context
- DraftKings Responsible Gaming commitments and framing:
  - https://www.draftkings.com/responsible-gaming
  - https://www.draftkings.com/draftkings-renews-state-council-funding-program-and-expands-responsible-gaming-initiatives
  - https://www.draftkings.com/lori-kalani-to-join-draftkings-as-first-chief-responsible-gaming-officer
- DraftKings product/technology direction relevant to this portfolio architecture:
  - https://www.draftkings.com/draftkings-reaches-agreement-to-acquire-simplebet-to-further-enhance-live-betting-offering
  - https://www.draftkings.com/draftkings-and-kindbridge-behavioral-health-expand-program
- These sources are used as directional context, not proof of proprietary internal implementation.

## Project Assumptions
> **Assumption (explicit):** The neuro-signal portion of this project is inspired by publicly discussed industry approaches (including Gamalyze-style concepts), and is modeled here as a portfolio design choice.  
> This document does **not** claim confirmed DraftKings proprietary model implementation beyond the cited DraftKings-owned sources.

## Architecture Snapshot
- Frontend: React + TypeScript + Vite.
- API: FastAPI app with dedicated routers (`/api`, `/api/cases`, `/api/ai`, `/api/sql`, `/api/interventions`).
- Storage: DuckDB runtime tables for queue/case/logging + dbt models for transformation layers.
- AI services: OpenAI provider with routing, SQL drafting, semantic audit, and nudge validation flows.

## Backend Composition
The API entrypoint initializes:
- runtime table creation (`ensure_tables()`),
- provider/config wiring (`LLMConfig`, OpenAI provider),
- app-scoped services for semantic audit and nudge validation,
- CORS and router registration.

Router responsibilities:
- `backend/routers/data.py`: queue, case detail, analytics summary, audit trail, case file aggregation.
- `backend/routers/cases.py`: query log reads/writes, timelines, trigger checks, status transitions.
- `backend/routers/ai.py`: semantic audit, SQL draft, router, nudge validation, AI logs.
- `backend/routers/sql.py`: guarded SQL execution and query log persistence.
- `backend/routers/interventions.py`: analyst notes + nudges.

## Data Model (Operational)
Primary runtime tables used in analyst workflows:
- `rg_queue_cases`
- `rg_case_status_log`
- `rg_query_log`
- `rg_llm_prompt_log`
- `rg_trigger_check_log`
- `rg_analyst_notes_log`
- `rg_nudge_log`

These tables allow full reconstruction of analyst actions for a case.

## End-to-End Request Flow
1. Analyst opens queue/case details.
2. Case starts (`/api/cases/start`) and moves into workbench state.
3. Analyst asks AI for route-specific help (`/api/ai/router`) or direct SQL draft (`/api/ai/query-draft`).
4. Generated SQL is validated for Snowflake-compatible syntax.
5. Analyst-approved SQL executes read-only (`/api/sql/execute`) with PII and statement guards.
6. Trigger checks are executed/logged (`/api/cases/trigger-check/{player_id}`).
7. Notes/nudges are saved; case submitted (`/api/cases/submit`).

## SQL Guardrail Design
Implemented controls in `backend/routers/sql.py` and `ai_services/snowflake_sql.py`:
- Reject non-read-only commands (`INSERT`, `UPDATE`, `DELETE`, `DROP`, etc.).
- Enforce `SELECT` / `WITH` query shape.
- Validate Snowflake-oriented SQL function usage.
- Reject PII field selection (`first_name`, `last_name`, `email`).
- Normalize schema aliases and rewrite execution SQL for DuckDB compatibility.
- Hard-limit returned rows by wrapping query with `LIMIT 200`.
- Return actionable binder-error hints for unknown columns.

## Prompt Router Design
`/api/ai/router` classifies prompts into:
- `SQL_DRAFT`
- `REGULATORY_CONTEXT`
- `EXTERNAL_CONTEXT`
- `GENERAL_ANALYSIS`

For `SQL_DRAFT`, the system:
- injects schema context,
- generates JSON-structured SQL drafts,
- validates syntax and prohibited patterns.

For non-SQL routes, it returns concise contextual responses and logs route/tool metadata.

## Trigger Check Logic
`POST /api/cases/trigger-check/{player_id}` supports cached reads and forced recomputation.

State-specific examples:
- MA: max recent bet versus 90-day average multiplier check.
- NJ: count of high/critical flags in recent window.
- PA: PA-specific check path in the same trigger framework.

Each run is logged in both query and trigger log tables with timestamped evidence.

## Static vs Live Data Mode
Frontend data access (`frontend/src/api/httpClient.ts`) uses `VITE_DATA_MODE`:
- `api`: call backend URLs.
- `static`: map API routes to `/demo/*.json` fixtures.

Static behavior:
- Endpoint-path remapping for queue, case detail, case file, timeline, logs, analytics.
- Read-only enforcement for most mutating routes.
- Allows deterministic demo without backend runtime dependency.

## Build and Demo Automation
- `scripts/seed_demo_db.py`: seeds runtime data.
- `scripts/seed_demo_cases.py`: produces deterministic case artifacts.
- `scripts/export_demo_json.py`: exports static fixtures.
- `scripts/build_static_demo.sh`: orchestrates seed + export for static mode.

## Testing Strategy
Current test suite focuses on behavior-critical components:
- Router behavior and LLM-required failures.
- Snowflake SQL validator behavior.
- SQL execution guardrails.
- Case file/trigger-check endpoint behavior.

Representative commands:
```bash
pytest -q
cd frontend && npm test
```

## Design Tradeoffs
- DuckDB provides local speed and reproducibility, but production warehouse concerns are only partially represented.
- Keyword-based routing is deterministic and transparent, but less adaptive than retrieval or classifier-based routing.
- Static mode improves demo reliability but cannot substitute for full backend integration testing.

## Known Gaps vs Production
- Synthetic data does not fully model real player behavioral entropy and can introduce bias.
- No enterprise IAM/RBAC layer is implemented in this local portfolio stack.
- No retrieval-backed legal/policy knowledge system is currently implemented.
- No live event/news/social ingestion pipeline is currently implemented.
- External/regulatory context routes are prompt-driven helper flows, not production legal knowledge infrastructure.

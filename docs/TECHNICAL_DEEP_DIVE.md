# Technical Deep Dive

## Architecture Goals
- Keep analyst decisions evidence-based and reproducible.
- Log every meaningful action (queries, prompts, notes, nudges, status changes).
- Separate live API behavior from static demo behavior.

## System Overview
- Frontend: React + TypeScript (case workflow UI, audit views, PDF export).
- Backend: FastAPI (queue, case, AI, SQL, interventions, analytics routes).
- Data: DuckDB runtime tables and dbt-transformed analytical models.
- AI services: prompt routing, SQL drafting, semantic summaries, nudge validation.

## Analyst Workflow Design
- Queue triage starts from risk category/composite/driver.
- Case file is the active workbench for investigation and action.
- Submission persists analyst action and rationale; no autonomous AI submission path exists.

## AI + SQL Guardrails
- Prompt router classifies prompts into route types.
- SQL draft endpoint validates Snowflake-style syntax patterns.
- SQL execution endpoint enforces read-only behavior and safety checks.
- Generated SQL is schema-aware by injecting current table/column context.

## Trigger Check Implementation
- Endpoint: `POST /api/cases/trigger-check/{player_id}`.
- Deterministic checks run for MA/NJ/PA logic and are logged.
- Static mode replays exported trigger artifacts; live mode uses backend execution/cached responses.

## Data and Logging Objects
- `rg_queue_cases`
- `rg_case_status_log`
- `rg_query_log`
- `rg_llm_prompt_log`
- `rg_trigger_check_log`
- `rg_analyst_notes_log`
- `rg_nudge_log`

## Static/Live Separation
- Live: frontend fetches backend APIs.
- Static: frontend fetches `frontend/public/demo/*` fixtures.
- This separation allows a no-backend demo while preserving a backend-capable implementation.

## Known Constraints
- Synthetic data can create distribution artifacts and analyst bias risk.
- Regulatory/context routes are not backed by a production legal knowledge graph.
- External event enrichment is currently a design direction, not an implemented ingestion pipeline.

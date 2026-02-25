# Production Parity Checklist

## Required Gates
- `dbt run` passes for all models.
- `dbt test` passes for all tests.
- `pytest -q` passes for backend and service logic.
- `cd frontend && npm test` passes.
- `cd frontend && npm run build` passes.

## Pipeline Shape Verification
- Raw ingestion path present (`data/*.csv` -> `raw.*`).
- Staging transformations are dbt-derived (not manually seeded).
- Intermediate and marts are dbt-derived.
- Demo runtime tables are seeded separately from model tables.

## Demo Runtime Verification
- 20 submitted cases + 2 in-progress cases in `rg_case_status_log`.
- Query, LLM prompt, trigger, nudge, and analyst note logs are populated.
- `docs/case_reviews/CASE_MANIFEST.json` exists and resolves to generated case files.

## Static Mode Verification
- `VITE_DATA_MODE=static` renders queue, case detail, audit trail, and analytics.
- Static fixtures exported under `frontend/public/demo`.
- Opening a case replays trigger-check data from demo fixtures without backend writes.

## Live Mode Verification
- `VITE_DATA_MODE=api` loads queue, case, audit, and analytics from backend endpoints.
- Opening a case calls backend trigger-check endpoint and timeline reflects backend logs.

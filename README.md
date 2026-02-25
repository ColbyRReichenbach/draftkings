# DK Sentinel

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-API-009688?logo=fastapi&logoColor=white)
![DuckDB](https://img.shields.io/badge/DuckDB-Analytics-FFF000?logo=duckdb&logoColor=000)
![dbt](https://img.shields.io/badge/dbt-Transformations-FF694B?logo=dbt&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=000)
![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6?logo=typescript&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-LLM_Assist-412991?logo=openai&logoColor=white)
![Tests](https://img.shields.io/badge/Tests-Pytest%20%7C%20Vitest-6E9F18)

I built this project to demonstrate how I operate as a modern Responsible Gaming analyst: SQL-first investigations, auditable AI assistance, and strict human-in-the-loop decision ownership.

## Executive Summary
- End-to-end analyst workflow: queue -> case detail -> case file -> submission.
- AI router for analyst prompts (SQL draft, regulatory context, external context, general analysis).
- Snowflake-oriented SQL guardrails + schema-aware prompting.
- Read-only SQL execution endpoint with safety constraints.
- MA/NJ/PA trigger checks with reproducible logs.
- Dual delivery model: live API mode and static fixture mode.

## Why This Matters For Analyst Work
I use LLMs to reduce mechanical work (query drafting, contextual lookup patterns) so analysis time goes to evidence quality, contradiction checks, and intervention rationale.

This repo is intentionally designed so decisions are inspectable:
- Query history is logged.
- Prompt route + response history is logged.
- Trigger checks are logged.
- Analyst notes and nudges are logged.

## Core Capabilities
### 1) Evidence Workflow
- Draft SQL with `/api/ai/query-draft` or `/api/ai/router`.
- Validate Snowflake-compatible syntax.
- Execute read-only SQL through `/api/sql/execute`.
- Store result previews and summaries in `rg_query_log`.

### 2) AI Governance
- AI never auto-submits case outcomes.
- Analyst remains final approver for notes, nudges, and actions.
- Prompt logs capture route type and selected tool.

### 3) Trigger Checks
- State-specific checks run via `POST /api/cases/trigger-check/{player_id}`.
- Checks are cached unless forced; results are persisted for audit.

### 4) Static vs Live Separation
- `VITE_DATA_MODE=api`: frontend reads backend endpoints.
- `VITE_DATA_MODE=static`: frontend reads `frontend/public/demo/*` fixtures.
- Static mode is read-only (except local replay behavior in browser state).

## Quick Start
### Live Mode
```bash
pip install -r requirements.txt
python scripts/seed_demo_db.py --completed 20 --in-progress 2

# Terminal 1
cd backend && uvicorn main:app --reload --port 8000

# Terminal 2
cd frontend && npm install && npm run dev
```

### Static Mode
```bash
./scripts/build_static_demo.sh
cd frontend && npm install && npm run dev:static
```

## Repo Layout
- `backend/` FastAPI routers and DuckDB-backed services.
- `frontend/` React client with static/live data mode switching.
- `dbt_project/` staging/intermediate/mart transformations.
- `scripts/` seeding, export, and demo build automation.
- `docs/` technical and workflow documentation.

## Limitations (Deliberate and Explicit)
- All player data is synthetic.
- Synthetic distributions can introduce bias and do not fully reproduce real player randomness.
- Regulatory and external context routes are prompt-based helpers, not a production legal/event knowledge platform.
- No live ingestion of news, social, or schedule feeds in current implementation.

## What I Would Build Next
- Retrieval-backed regulatory assistant using internal policy and legal artifacts.
- Event-aware context enrichment (sports schedules, media/news signals).
- Governance handoff flow for legal/compliance approval on high-impact interventions.

## Additional Docs
- `docs/TECHNICAL_DEEP_DIVE.md`
- `docs/LLM_INTEGRATION.md`
- `docs/PROD_PARITY_CHECKLIST.md`
- `docs/case_reviews/README.md`

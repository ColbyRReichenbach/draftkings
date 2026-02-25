<div align="center">
  # DK Sentinel

**Modern analytics full stack project with functional frontend and professional workflow**
Modern analytics stack workflow showcased through a assumption based mock workflow of a Responsible Gaming analyst at DraftKings: SQL-first investigations, auditable AI assistance, and strict human-in-the-loop decision ownership.

  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white" alt="Python" />
    <img src="https://img.shields.io/badge/FastAPI-API-009688?logo=fastapi&logoColor=white" alt="FastAPI" />
    <img src="https://img.shields.io/badge/DuckDB-Analytics-FFF000?logo=duckdb&logoColor=000" alt="DuckDB" />
    <img src="https://img.shields.io/badge/dbt-Transformations-FF694B?logo=dbt&logoColor=white" alt="dbt" />
    <img src="https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=000" alt="React" />
    <img src="https://img.shields.io/badge/TypeScript-5-3178C6?logo=typescript&logoColor=white" alt="TypeScript" />
    <img src="https://img.shields.io/badge/OpenAI-LLM_Assist-412991?logo=openai&logoColor=white" alt="OpenAI" />
    <img src="https://img.shields.io/badge/Tests-Pytest%20%7C%20Vitest-6E9F18" alt="Tests" />

by **Colby Reichenbach**

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-0077B5?style=flat-square&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/colby-reichenbach/)
[![Portfolio](https://img.shields.io/badge/Portfolio%20-%20Check%20Out%20My%20Work?style=flat-square&label=Check%20Out%20My%20Work&color=4B9CD3)](https://colbyrreichenbach.github.io/)
[![GitHub](https://img.shields.io/badge/GitHub-Follow-181717?style=flat-square&logo=github&logoColor=white)](https://github.com/ColbyRReichenbach)

</div>

## Executive Summary
- End-to-end analyst workflow: queue -> case detail -> case file -> submission.
- AI router for analyst prompts (SQL draft, regulatory context, external context, general analysis).
- Snowflake-oriented SQL guardrails + schema-aware prompting.
- Read-only SQL execution endpoint with safety constraints.
- MA/NJ/PA trigger checks with reproducible logs.
- Dual delivery model: live API mode and static fixture mode.

## Why I Chose This Infrastructure
- **DuckDB** for fast local iteration and deterministic, file-based reproducibility during development.
- **Snowflake-style SQL constraints** to mirror production warehouse query expectations while running locally.
- **FastAPI** to expose clear, testable analyst workflow interfaces (queue, case, AI, SQL, interventions).
- **Routed LLM assist** to reduce repetitive SQL drafting and context switching while preserving analyst ownership.
- **Static + live separation** to support reliable demos without losing production-like API workflow behavior.

## Source-Backed Context
- DraftKings publicly positions Responsible Gaming as a core operational priority and ongoing investment area:
  - https://www.draftkings.com/responsible-gaming
  - https://www.draftkings.com/draftkings-renews-state-council-funding-program-and-expands-responsible-gaming-initiatives
  - https://www.draftkings.com/lori-kalani-to-join-draftkings-as-first-chief-responsible-gaming-officer
- DraftKings has also published product/technology direction indicating prioritization of advanced live-betting systems and AI-driven pricing capabilities:
  - https://www.draftkings.com/draftkings-reaches-agreement-to-acquire-simplebet-to-further-enhance-live-betting-offering
  - https://www.draftkings.com/draftkings-and-kindbridge-behavioral-health-expand-program
- These sources inform project direction only. They do not prove DraftKings internal architecture, model stack, or proprietary implementation details.

## Project Assumptions
> **Assumption (explicit):** This project includes a neuro-signal component inspired by public market reporting and industry tooling (for example, Gamalyze-style concepts).  
> This repository does **not** assert DraftKings-official implementation details beyond the cited DraftKings-owned sources.

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
- `docs/case_reviews/README.md`
- `data_generation/DATA.md`

## Built by **Colby Reichenbach**

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-0077B5?style=flat-square&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/colby-reichenbach/)
[![Portfolio](https://img.shields.io/badge/Portfolio%20-%20Check%20Out%20My%20Work?style=flat-square&label=Check%20Out%20My%20Work&color=4B9CD3)](https://colbyrreichenbach.github.io/)
[![GitHub](https://img.shields.io/badge/GitHub-Follow-181717?style=flat-square&logo=github&logoColor=white)](https://github.com/ColbyRReichenbach)

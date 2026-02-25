# DK Sentinel: Responsible Gaming Intelligence System

Portfolio project for Responsible Gaming analytics workflows: queue triage, case audits, SQL evidence logging, AI-assisted analysis, and state-specific trigger checks.

## Quick Start

### Live mode (API-backed)
```bash
pip install -r requirements.txt
python scripts/seed_demo_db.py --completed 20 --in-progress 2

# terminal 1
cd backend && uvicorn main:app --reload --port 8000

# terminal 2
cd frontend && npm install && npm run dev
```

### Static mode (pre-exported fixtures)
```bash
./scripts/build_static_demo.sh
cd frontend && npm install && npm run dev:static
```

## Project Structure
- `dbt_project/` data transformations
- `backend/` FastAPI service layer
- `frontend/` React dashboard
- `scripts/` seed/export/audit automation
- `tests/` backend and integration tests
- `docs/` analyst and technical documentation

## Key Features
- Analyst queue with lifecycle tracking (`NOT_STARTED` -> `IN_PROGRESS` -> `SUBMITTED`)
- Case File workbench with SQL evidence and AI transparency logs
- Read-only SQL drafting/execution safeguards
- MA/NJ/PA trigger checks with deterministic audit records
- Static and live demo modes with explicit data-source separation

## Documentation
- `docs/PORTFOLIO_WRITEUP.md`
- `docs/TECHNICAL_DEEP_DIVE.md`
- `docs/ANALYST_PLAYBOOK.md`
- `docs/LLM_INTEGRATION.md`
- `docs/PROD_PARITY_CHECKLIST.md`
- `docs/case_reviews/README.md`

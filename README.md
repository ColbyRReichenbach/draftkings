# DK SENTINEL: Responsible Gaming Intelligence System

Portfolio project for DraftKings Analyst II, RG Analytics role (Job ID: jr13280).

## Quick Start
```bash
# 1. Review project context
cat CLAUDE.md

# 2. Start Claude Code
claude

# 3. First command
claude "Review CLAUDE.md and list first 3 development tasks"
```

### Demo Data Seed (for hosting)
Generate a demo DuckDB with a majority of Critical/High/Medium cases:
```bash
python scripts/seed_demo_db.py --players 400
```

## Project Structure
```
claude/          # Claude Code configuration
├── skills/       # Domain knowledge (5 files)
├── agents/       # Specialized personas (5 files)
├── workflows/    # Multi-step procedures (3 files)
└── context/      # Reference data (4 files)

dbt_project/      # Data transformation
ai_services/      # LLM integration
backend/          # FastAPI REST API
frontend/         # React dashboard
tests/            # Testing
docs/             # Documentation
```

## Tech Stack
- Snowflake (target) + DuckDB (dev) + dbt + Python + FastAPI + React + OpenAI API

## Recruiter Summary
See `docs/PORTFOLIO_WRITEUP.md` for a concise, recruiter-ready overview of the project.

## Key Features
- Persisted analyst queue with lifecycle tracking (Not Started → In Progress → Submitted)
- Full Case File workbench with HITL notes, SQL evidence, and AI assist transparency
- Read-only SQL execution with logging + Snowflake-safe guardrails
- Regulatory trigger checks (MA/NJ/PA) logged as deterministic SQL evidence
- Manager-grade Analytics dashboard (throughput, rigor, compliance signals)
- DraftKings-authentic tech stack + responsible AI framing

## Documentation
- CLAUDE.md - Project overview
- claude/skills/ - Domain expertise
- claude/agents/ - Specialized tasks
- claude/workflows/ - Step-by-step procedures
- docs/HITL_REVIEW.md - Completed analyst review with SQL queries
- docs/WEEK9_REPORT.md - Live integration + analytics + SQL workflow updates
- docs/PORTFOLIO_WRITEUP.md - Recruiter-ready project summary
- docs/TECHNICAL_DEEP_DIVE.md - Full technical rationale + AI workflow design

## Portfolio Assets
Add your final assets here when ready:
- Live demo link
- Walkthrough video (2–3 min)
- Sample PDF report

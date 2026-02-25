# Portfolio Summary

I built DK Sentinel as a Responsible Gaming analytics portfolio project to demonstrate how I work as a SQL-first, modern-stack analyst.

## What This Project Demonstrates
- Building an end-to-end analyst workflow instead of isolated dashboards.
- Designing evidence-driven case handling with auditable logs.
- Using LLMs as assistive tools with explicit human approval points.
- Constraining generated SQL to Snowflake-compatible syntax and known schema context.

## Implemented Scope
- Queue and case lifecycle endpoints.
- Case file workflow with query logs, AI logs, notes, nudges, and timeline.
- Prompt router for SQL/regulatory/external/general analyst prompts.
- Read-only SQL execution endpoint with safeguards.
- Trigger checks for MA/NJ/PA.
- Static demo export + live API mode.

## Why It Is Relevant For Hiring
This repo is focused on analyst operating quality:
- reproducibility,
- auditability,
- and clear decision ownership.

I intentionally prioritize workflow design and analytical governance over model hype.

## Boundaries
- Data is synthetic and intended for pipeline and workflow validation.
- Results should not be interpreted as real-world prevalence or operational KPI impact.

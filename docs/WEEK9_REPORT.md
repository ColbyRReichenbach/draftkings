# Week 9 Report — Live Integration + Prompt Routing

## Summary
Week 9 transitioned the dashboard from mock data to live backend endpoints, added a prompt router for analyst questions, and enforced Snowflake-compatible SQL drafting. The result is a production-aligned HITL workflow: analysts explicitly request AI assistance, every prompt is routed and logged, and SQL outputs are validated for Snowflake syntax before being stored.

## Key Deliverables
- Live API integration for Queue, Case Detail, Audit Trail, and Case File.
- Prompt router with route transparency (SQL Draft / Regulatory Context / External Context / General Analysis).
- Snowflake-safe SQL enforcement (rejects non-Snowflake syntax).
- Router decisions logged alongside LLM prompt/response history.
- UI badges for route + tool with Snowflake-only guidance.

## Analyst Workflow Alignment
This release reinforces analyst ownership:
- AI is **on-demand only**, never auto-run.
- Routing decisions are visible and logged.
- SQL drafts are validated against Snowflake constraints before logging.
- Audit Trail remains the workbench for in-progress cases.

## Validation
- Backend: `pytest` (router + Snowflake validator)
- Frontend: `npm test` (routing panel + live data wiring)

## Next Roadmap (Optional)
- Portfolio polish (screenshots, README final pass).
- Optional API auth and role-based access controls.
- Replace external-context routing with internal policy knowledge base.

---

# Week 9 Extension — Analyst Ops + SQL Execution

## Summary
Week 9 extended into ops-grade analyst tooling: a persisted queue with refill logic, read-only SQL execution with guardrails, cached regulatory trigger checks, and a manager-ready analytics dashboard. These changes make the workflow feel production-real for a solo analyst while preserving auditability.

## Key Deliverables
- Persisted queue batching in DuckDB with refill thresholds and audit trail exclusions.
- Read-only SQL execution with Snowflake-safe validation + PII guardrails.
- Cached trigger checks (MA/NJ/PA) logged once per case.
- Unified logs for SQL, LLM prompts, and analyst notes in case timelines.
- Manager-grade analytics page (throughput, rigor, compliance signals).
- Draft notes save/load for in-progress work.
- PDF export refinements (summary/appendix separation + layout fixes).

## Analyst Workflow Alignment
- Analysts can save drafts mid-case and resume without losing work.
- SQL evidence is executed read-only and logged for transparency.
- Trigger checks remain deterministic and auditable.
- Manager view surfaces productivity, rigor, and compliance in one place.

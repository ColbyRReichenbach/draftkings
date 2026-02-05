# DK Sentinel — Technical Deep Dive

## Executive Summary
DK Sentinel is a Responsible Gaming analytics platform built to mirror DraftKings analyst workflows: queue triage, case review, evidence gathering via SQL, regulatory trigger checks, audit trails, and compliance-style reporting. The system emphasizes analyst ownership, with AI used only as assistive tooling and fully logged for transparency.

## Why This Architecture
### Analyst-first workflow design
- **Queue → Case File → Audit Trail** mirrors real operational flow and makes accountability explicit.
- Case status (Not Started → In Progress → Submitted) prevents confusion and guarantees traceability.
- Audit Trail is the active workbench; Case Detail is a triage view.

### Evidence before decisions
- SQL evidence is **run, reviewed, and logged**, with output previews tied to each query.
- Analyst summaries are recorded alongside evidence to show reasoning, not just results.

### Compliance-ready reporting
- PDF export produces a professional report with a concise summary section and an appendix for evidence and logs.
- This mirrors how compliance teams expect decisions to be documented and reviewed.

## Data Architecture
### Storage layer
- **DuckDB** for local development (fast, file-based, SQL-first).
- **Snowflake-style SQL guardrails** ensure queries align with target warehouse semantics.

### Core data objects
- `rg_queue_cases`: persisted queue with refills and batching
- `rg_case_status_log`: case lifecycle tracking
- `rg_query_log`: SQL evidence with output preview and analyst summary
- `rg_llm_prompt_log`: AI prompts and responses for transparency
- `rg_trigger_check_log`: deterministic regulatory checks

## AI Engineering Practices
### AI as assistive tooling
- AI outputs never auto-submit decisions.
- Analyst owns final decisions and nudge validation.
- Prompt routing ensures analysts ask the right tool (SQL draft vs regulatory context vs general analysis).

### Transparency and governance
- All AI prompts and responses are logged.
- Audit trail and case timeline preserve the history of reasoning.

### Industry best practices alignment
- The system follows established AI governance and accountability practices, emphasizing traceability, transparency, and risk management throughout the AI lifecycle. citeturn0search0turn0search5turn0search6

## DraftKings Alignment (Responsible Gaming Priorities)
DraftKings has publicly emphasized Responsible Gaming as a core priority and has invested in RG tools that help players understand and manage their behavior (e.g., My Stat Sheet, My Budget Builder, RG Education initiatives). DK Sentinel is aligned with those priorities by focusing on transparency, evidence, and analyst accountability in player-level decisions. citeturn0search1turn0search2turn0search8turn0search9

## Technical Stack (Aligned with Role)
- **Frontend**: React + TypeScript + Tailwind
- **Backend**: FastAPI + DuckDB
- **Analytics**: SQL-first evidence logging and query execution
- **AI**: Prompt routing + transparent logs + assistive summaries
- **Reporting**: PDF export for compliance-style documentation

This mirrors the Analyst II job expectations: analytical frameworks, dashboards, alerting logic, and reusable workflows built on SQL-first systems.

## Router Strategy (Why It Matters)
Analyst questions can span:
- SQL evidence requests (player behavior)
- Regulatory context
- External context (news/events)

A lightweight router ensures the right tool handles the right request, which reduces hallucinations and improves auditability.

## Known Gaps & Next Enhancements
### Data limitations in the current demo
- **No deposits/withdrawals**
- **No bet type (single/parlay) details**
- **Limited player demographics/profile attributes**

### How this would improve with real data
- Add deposit/withdrawal tables to detect financial stress patterns.
- Include bet type breakdown for escalation detection.
- Add external event context (big games, sentiment shifts) for anomaly detection.

### Future improvements
- Internal regulatory knowledge base model for up-to-date state policy logic.
- News/event sentiment integrations to inform volatility-driven behavior.
- ML-based anomaly detection for bet timing and stake spikes.

## Snowflake-Ready Architecture (Portfolio Appendix)
Even though the demo runs locally in DuckDB, the system is designed to map cleanly into Snowflake production environments. This is the exact skill set required for Analyst II roles that operate on Snowflake at scale.

### Snowflake capabilities I would demonstrate in production
- **Warehouse sizing + performance tuning** for high‑volume query workloads.
- **RBAC and data governance** (role‑based access for analysts vs service accounts).
- **Row‑level security / masking policies** to protect sensitive player attributes.
- **Time Travel** for auditability and recovery of historical decisions.
- **Streams + Tasks** to support incremental refresh and automation.
- **Zero‑copy cloning** for safe dev/test environments.

### What would change in this project with Snowflake
- Replace DuckDB with Snowflake as the backing warehouse.
- Move log tables into Snowflake schemas for centralized audit.
- Use Snowflake compute clusters to handle high‑volume SQL evidence queries.
- Implement production‑grade alerting using Tasks and Streams.

## Why This Demonstrates Analyst II Readiness
- Strong SQL evidence workflow and reproducibility
- Clear, explainable decision trails
- Data product design (dashboards, queue, PDF reporting)
- Assistive AI aligned with governance and accountability

---

If you want a shorter recruiter-ready summary, see `docs/PORTFOLIO_WRITEUP.md`.

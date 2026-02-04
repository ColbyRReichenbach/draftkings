# Week 8 Report — Case File (HITL + AI + SQL)

## Summary
Week 8 delivered a full‑page Case File view inside the Audit Trail tab, centered on analyst ownership and transparency. Medium/High/Critical cases now expand into a structured case file with decision rationale, AI drafts, SQL query logs, and a unified timeline. PDF export provides portfolio‑ready reporting.

## Key Deliverables
- Case File view with decision summary, evidence snapshot, analyst notes, AI transparency, SQL assistant, query log, and timeline.
- Hybrid SQL assistant: LLM drafts, analyst edits, and logs final SQL (no execution in‑app).
- New DuckDB table + endpoints for SQL query logging and timeline aggregation.
- Analyst-grade PDF export (structured report layout, multi-section, non-screenshot).
- Case lifecycle flow: **Start Case Review** in Case Detail → Audit Trail workbench → **Submit Decision** (status persisted and surfaced with colored status pills).
- Queue hygiene: cases in Audit Trail are removed from the queue so new triage work isn’t blocked.

## Analyst Workflow Alignment
This release emphasizes HITL accountability:
- AI drafts are explicitly labeled assistive.
- Analysts approve final notes and SQL before logging.
- Case File surfaces rationale, evidence, and audit trail in one place.
- Audit Trail is the single workbench for in‑progress cases; Case Detail remains read‑only triage with a clear **Start Case Review** CTA.

## Next Roadmap
**Week 9**
- Wire live queue + case detail data to backend.
- Run full validation (dbt + pytest + vitest).
- Final documentation polish + portfolio packaging.

## Security Notes
- `npm audit` reports issues in `jspdf` (dompurify) and `vite` (esbuild). Fixes require
  breaking upgrades; deferred to avoid destabilizing Week 8 features.
- Mitigation: dev server locked to `127.0.0.1` in Vite config.

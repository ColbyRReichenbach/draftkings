import { expect, vi } from 'vitest';
import * as matchers from '@testing-library/jest-dom/matchers';

expect.extend(matchers);

const emptyJson = (body: unknown, status = 200) =>
  Promise.resolve(
    new Response(JSON.stringify(body), {
      status,
      headers: { 'Content-Type': 'application/json' }
    })
  );

vi.stubGlobal('fetch', (input: RequestInfo) => {
  const url = typeof input === 'string' ? input : input.url;

  if (url.includes('/api/interventions/notes/')) {
    return Promise.resolve(new Response('', { status: 404 }));
  }

  if (url.includes('/api/ai/logs/')) {
    return emptyJson([]);
  }

  if (url.includes('/api/ai/query-draft')) {
    return emptyJson({ draft_sql: 'SELECT 1', assumptions: ['Sample assumption'] });
  }

  if (url.includes('/api/ai/router')) {
    return emptyJson({
      route: 'SQL_DRAFT',
      tool: 'query-draft',
      reasoning: 'Routed based on prompt intent keywords.',
      model_used: 'gpt-4o-mini',
      response_text: null,
      draft_sql: 'SELECT 1',
      assumptions: ['Sample assumption']
    });
  }

  if (url.includes('/api/cases/query-log/')) {
    return emptyJson([]);
  }

  if (url.includes('/api/cases/query-log')) {
    return emptyJson({
      player_id: 'PLR_0000_MA',
      analyst_id: 'Colby Reichenbach',
      prompt_text: 'Prompt',
      draft_sql: 'SELECT 1',
      final_sql: 'SELECT 1',
      purpose: 'Purpose',
      result_summary: 'Summary',
      created_at: '2026-02-04T00:00:00Z'
    });
  }

  if (url.includes('/api/cases/status')) {
    return emptyJson([
      {
        case_id: 'CASE-1001',
        player_id: 'PLR_1024_MA',
        analyst_id: 'Colby Reichenbach',
        status: 'IN_PROGRESS',
        started_at: '2026-02-04T00:00:00Z',
        submitted_at: null,
        updated_at: '2026-02-04T00:00:00Z'
      }
    ]);
  }

  if (url.includes('/api/cases/start') || url.includes('/api/cases/submit')) {
    return emptyJson({ ok: true });
  }

  if (url.includes('/api/cases/timeline/')) {
    return emptyJson([]);
  }

  if (url.includes('/api/sql/execute')) {
    return emptyJson({
      columns: ['player_id', 'bet_amount'],
      rows: [['PLR_1024_MA', 120]],
      row_count: 1,
      duration_ms: 12,
      result_summary: 'Query returned 1 rows in 12ms. Columns: player_id, bet_amount. Notable patterns: ____.'
    });
  }

  if (url.includes('/api/cases/trigger-check/')) {
    return emptyJson([
      {
        state: 'MA',
        triggered: false,
        reason: 'Max bet $120.00 vs 90d avg $85.00.',
        sql_text: 'SELECT 1',
        row_count: 1,
        created_at: '2026-02-04T00:00:00Z'
      }
    ]);
  }

  if (url.includes('/api/interventions/nudge/')) {
    return emptyJson({
      player_id: 'PLR_1024_MA',
      analyst_id: 'Colby Reichenbach',
      draft_nudge: 'Draft nudge',
      final_nudge: 'Final nudge',
      validation_status: 'VALID',
      validation_violations: [],
      created_at: '2026-02-04T00:00:00Z'
    });
  }

  if (url.includes('/api/interventions/nudge')) {
    return emptyJson({
      player_id: 'PLR_1024_MA',
      analyst_id: 'Colby Reichenbach',
      draft_nudge: 'Draft nudge',
      final_nudge: 'Final nudge',
      validation_status: 'VALID',
      validation_violations: [],
      created_at: '2026-02-04T00:00:00Z'
    });
  }

  if (url.includes('/api/queue')) {
    return emptyJson([
      {
        case_id: 'CASE-PLR_1024_MA',
        player_id: 'PLR_1024_MA',
        risk_category: 'CRITICAL',
        composite_risk_score: 0.92,
        score_calculated_at: '2026-02-03T08:14:00Z',
        state_jurisdiction: 'MA',
        key_evidence: ['Loss chase 0.84', 'Bet escalation 0.88', 'Market drift 0.62']
      }
    ]);
  }

  if (url.includes('/api/case-detail/')) {
    return emptyJson({
      case_id: 'CASE-PLR_1024_MA',
      player_id: 'PLR_1024_MA',
      risk_category: 'CRITICAL',
      composite_risk_score: 0.92,
      score_calculated_at: '2026-02-03T08:14:00Z',
      state_jurisdiction: 'MA',
      evidence_snapshot: {
        total_bets_7d: 84,
        total_wagered_7d: 7420,
        loss_chase_score: 0.84,
        bet_escalation_score: 0.88,
        market_drift_score: 0.62,
        temporal_risk_score: 0.71,
        gamalyze_risk_score: 0.79
      },
      ai_explanation: '',
      draft_nudge: '',
      regulatory_notes: 'MA abnormal-play review pending (10x rolling avg check).',
      analyst_actions: ['Monitor & Document']
    });
  }

  if (url.includes('/api/audit-trail')) {
    return emptyJson([
      {
        audit_id: 'AUD-4001',
        case_id: 'CASE-PLR_1024_MA',
        player_id: 'PLR_1024_MA',
        analyst_id: 'Colby Reichenbach',
        action: 'Review pending',
        risk_category: 'CRITICAL',
        state_jurisdiction: 'MA',
        timestamp: '2026-02-03T09:05:00Z',
        notes: 'No analyst notes yet.'
      }
    ]);
  }

  return emptyJson({});
});

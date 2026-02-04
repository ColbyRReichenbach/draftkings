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

  return emptyJson({});
});

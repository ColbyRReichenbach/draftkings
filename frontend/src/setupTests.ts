import '@testing-library/jest-dom';
import { vi } from 'vitest';

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

  return emptyJson({});
});

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

const DATA_MODE = (import.meta.env.VITE_DATA_MODE ?? 'api').toLowerCase();
const STATIC_BASE = '/demo';

const isStaticMode = DATA_MODE === 'static';

const staticPathFor = (path: string): string | null => {
  const cleanPath = path.split('?')[0];

  const exact: Record<string, string> = {
    '/api/queue': `${STATIC_BASE}/queue.json`,
    '/api/audit-trail': `${STATIC_BASE}/audit-trail.json`,
    '/api/analytics/summary': `${STATIC_BASE}/analytics-summary.json`,
    '/api/cases/status': `${STATIC_BASE}/cases/status.json`
  };
  if (exact[cleanPath]) {
    return exact[cleanPath];
  }

  const caseDetailMatch = cleanPath.match(/^\/api\/case-detail\/(.+)$/);
  if (caseDetailMatch) {
    return `${STATIC_BASE}/case-detail/${caseDetailMatch[1]}.json`;
  }

  const caseFileMatch = cleanPath.match(/^\/api\/case-file\/(.+)$/);
  if (caseFileMatch) {
    return `${STATIC_BASE}/case-file/${caseFileMatch[1]}.json`;
  }

  const timelineMatch = cleanPath.match(/^\/api\/cases\/timeline\/(.+)$/);
  if (timelineMatch) {
    return `${STATIC_BASE}/cases/timeline/${timelineMatch[1]}.json`;
  }

  const queryLogMatch = cleanPath.match(/^\/api\/cases\/query-log\/(.+)$/);
  if (queryLogMatch) {
    return `${STATIC_BASE}/cases/query-log/${queryLogMatch[1]}.json`;
  }

  const triggerMatch = cleanPath.match(/^\/api\/cases\/trigger-check\/(.+)$/);
  if (triggerMatch) {
    return `${STATIC_BASE}/cases/trigger-check/${triggerMatch[1]}.json`;
  }

  const aiLogsMatch = cleanPath.match(/^\/api\/ai\/logs\/(.+)$/);
  if (aiLogsMatch) {
    return `${STATIC_BASE}/ai/logs/${aiLogsMatch[1]}.json`;
  }

  const notesMatch = cleanPath.match(/^\/api\/interventions\/notes\/(.+)$/);
  if (notesMatch) {
    return `${STATIC_BASE}/interventions/notes/${notesMatch[1]}.json`;
  }

  const notesDraftMatch = cleanPath.match(/^\/api\/interventions\/notes-draft\/(.+)$/);
  if (notesDraftMatch) {
    return `${STATIC_BASE}/interventions/notes-draft/${notesDraftMatch[1]}.json`;
  }

  const nudgeMatch = cleanPath.match(/^\/api\/interventions\/nudge\/(.+)$/);
  if (nudgeMatch) {
    return `${STATIC_BASE}/interventions/nudge/${nudgeMatch[1]}.json`;
  }

  return null;
};

const buildUrl = (path: string, method: string): string => {
  if (!isStaticMode) {
    return `${API_BASE_URL}${path}`;
  }

  const staticPath = staticPathFor(path);
  if (!staticPath) {
    throw new Error(`Static mode has no fixture for endpoint: ${path}`);
  }
  if (method.toUpperCase() !== 'GET' && method.toUpperCase() !== 'POST') {
    throw new Error(`Static mode only supports GET/POST fixture reads: ${path}`);
  }

  return staticPath;
};

export const request = async <T>(path: string, options: RequestInit): Promise<T> => {
  const method = options.method ?? 'GET';

  if (isStaticMode && !path.startsWith('/api/cases/trigger-check/') && method.toUpperCase() !== 'GET') {
    throw new Error(`Static mode is read-only. Unsupported method ${method} for ${path}`);
  }

  const response = await fetch(buildUrl(path, method), {
    headers: { 'Content-Type': 'application/json', ...(options.headers ?? {}) },
    ...options
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed with ${response.status}`);
  }

  return (await response.json()) as T;
};

export const requestNullable = async <T>(path: string, options: RequestInit): Promise<T | null> => {
  const method = options.method ?? 'GET';
  const response = await fetch(buildUrl(path, method), {
    headers: { 'Content-Type': 'application/json', ...(options.headers ?? {}) },
    ...options
  });

  if (response.status === 404) {
    return null;
  }
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed with ${response.status}`);
  }

  return (await response.json()) as T;
};

export const dataMode = DATA_MODE;

import {
  CaseTimelineEntry,
  CaseStatusEntry,
  CaseStatusRequest,
  QueryDraftRequest,
  QueryDraftResponse,
  QueryLogEntry,
  QueryLogRequest,
  NudgeLogRequest,
  NudgeLogResponse,
  SqlExecuteRequest,
  SqlExecuteResponse,
  TriggerCheckResult
} from '../types/risk';

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

const request = async <T>(path: string, options: RequestInit): Promise<T> => {
  const response = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(options.headers ?? {}) },
    ...options
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed with ${response.status}`);
  }

  return (await response.json()) as T;
};

export const queryClient = {
  draftSql: (payload: QueryDraftRequest) =>
    request<QueryDraftResponse>('/api/ai/query-draft', {
      method: 'POST',
      body: JSON.stringify(payload)
    }),
  createQueryLog: (payload: QueryLogRequest) =>
    request<QueryLogEntry>('/api/cases/query-log', {
      method: 'POST',
      body: JSON.stringify(payload)
    }),
  getQueryLogs: (playerId: string) =>
    request<QueryLogEntry[]>(`/api/cases/query-log/${playerId}`, {
      method: 'GET'
    }),
  getTimeline: (playerId: string) =>
    request<CaseTimelineEntry[]>(`/api/cases/timeline/${playerId}`, {
      method: 'GET'
    }),
  startCase: (payload: CaseStatusRequest) =>
    request<CaseStatusEntry>('/api/cases/start', {
      method: 'POST',
      body: JSON.stringify(payload)
    }),
  submitCase: (payload: CaseStatusRequest) =>
    request<CaseStatusEntry>('/api/cases/submit', {
      method: 'POST',
      body: JSON.stringify(payload)
    }),
  getCaseStatuses: () =>
    request<CaseStatusEntry[]>('/api/cases/status', {
      method: 'GET'
    }),
  executeSql: (payload: SqlExecuteRequest) =>
    request<SqlExecuteResponse>('/api/sql/execute', {
      method: 'POST',
      body: JSON.stringify(payload)
    }),
  runTriggerChecks: (playerId: string, force = false) =>
    request<TriggerCheckResult[]>(
      `/api/cases/trigger-check/${playerId}${force ? '?force=true' : ''}`,
      {
        method: 'POST'
      }
    ),
  saveNudge: (payload: NudgeLogRequest) =>
    request<NudgeLogResponse>('/api/interventions/nudge', {
      method: 'POST',
      body: JSON.stringify(payload)
    }),
  getNudge: (playerId: string) =>
    request<NudgeLogResponse>(`/api/interventions/nudge/${playerId}`, {
      method: 'GET'
    })
};

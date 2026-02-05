import { AnalyticsSummary, AuditEntry, CaseDetail, RiskCase } from '../types/risk';

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

export const riskClient = {
  getQueue: () =>
    request<RiskCase[]>('/api/queue', {
      method: 'GET'
    }),
  getCaseDetail: (caseId: string) =>
    request<CaseDetail>(`/api/case-detail/${caseId}`, {
      method: 'GET'
    }),
  getAuditTrail: () =>
    request<AuditEntry[]>('/api/audit-trail', {
      method: 'GET'
    }),
  getAnalyticsSummary: () =>
    request<AnalyticsSummary>('/api/analytics/summary', {
      method: 'GET'
    })
};

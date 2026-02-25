import { AnalyticsSummary, AuditEntry, CaseDetail, RiskCase } from '../types/risk';

import { request } from './httpClient';

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

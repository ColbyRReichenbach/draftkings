import {
  mockAnalyticsSummary,
  mockAuditTrail,
  mockCaseDetails,
  mockCases
} from '../data/mockCases';
import { AnalyticsSummary, AuditEntry, CaseDetail, RiskCase } from '../types/risk';

const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

export const mockClient = {
  async getRiskCases(): Promise<RiskCase[]> {
    await delay(150);
    return mockCases;
  },
  async getCaseDetail(caseId: string): Promise<CaseDetail | null> {
    await delay(120);
    return mockCaseDetails.find((detail) => detail.case_id === caseId) ?? null;
  },
  async getAnalyticsSummary(): Promise<AnalyticsSummary> {
    await delay(180);
    return mockAnalyticsSummary;
  },
  async getAuditTrail(): Promise<AuditEntry[]> {
    await delay(140);
    return mockAuditTrail;
  }
};

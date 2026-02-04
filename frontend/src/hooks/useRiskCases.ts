import { useQuery } from '@tanstack/react-query';
import { mockClient } from '../api/mockClient';

export const useRiskCases = () =>
  useQuery({
    queryKey: ['risk-cases'],
    queryFn: () => mockClient.getRiskCases()
  });

export const useCaseDetail = (caseId: string | null) =>
  useQuery({
    queryKey: ['case-detail', caseId],
    queryFn: () => (caseId ? mockClient.getCaseDetail(caseId) : Promise.resolve(null)),
    enabled: Boolean(caseId)
  });

export const useCaseDetailByPlayer = (playerId: string | null) =>
  useQuery({
    queryKey: ['case-detail-player', playerId],
    queryFn: () => (playerId ? mockClient.getCaseDetailByPlayer(playerId) : Promise.resolve(null)),
    enabled: Boolean(playerId)
  });

export const useAnalyticsSummary = () =>
  useQuery({
    queryKey: ['analytics-summary'],
    queryFn: () => mockClient.getAnalyticsSummary()
  });

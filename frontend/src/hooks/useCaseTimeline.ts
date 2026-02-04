import { useMutation, useQuery } from '@tanstack/react-query';
import { queryClient } from '../api/queryClient';
import { CaseStatusRequest } from '../types/risk';

export const useCaseTimeline = (playerId: string | null) =>
  useQuery({
    queryKey: ['case-timeline', playerId],
    queryFn: () => (playerId ? queryClient.getTimeline(playerId) : Promise.resolve([])),
    enabled: Boolean(playerId)
  });

export const useCaseStatuses = () =>
  useQuery({
    queryKey: ['case-statuses'],
    queryFn: () => queryClient.getCaseStatuses()
  });

export const useStartCase = () =>
  useMutation({
    mutationFn: (payload: CaseStatusRequest) => queryClient.startCase(payload)
  });

export const useSubmitCase = () =>
  useMutation({
    mutationFn: (payload: CaseStatusRequest) => queryClient.submitCase(payload)
  });

import { useMutation, useQuery } from '@tanstack/react-query';
import { queryClient } from '../api/queryClient';
import { QueryLogRequest } from '../types/risk';

export const useQueryLog = (playerId: string | null) =>
  useQuery({
    queryKey: ['query-log', playerId],
    queryFn: () => (playerId ? queryClient.getQueryLogs(playerId) : Promise.resolve([])),
    enabled: Boolean(playerId)
  });

export const useCreateQueryLog = () =>
  useMutation({
    mutationFn: (payload: QueryLogRequest) => queryClient.createQueryLog(payload)
  });

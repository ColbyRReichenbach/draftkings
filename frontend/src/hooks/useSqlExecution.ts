import { useMutation, useQuery } from '@tanstack/react-query';
import { queryClient } from '../api/queryClient';
import { SqlExecuteRequest } from '../types/risk';

export const useSqlExecute = () =>
  useMutation({
    mutationFn: (payload: SqlExecuteRequest) => queryClient.executeSql(payload)
  });

export const useTriggerChecks = (playerId: string | null) =>
  useQuery({
    queryKey: ['trigger-checks', playerId],
    queryFn: () => (playerId ? queryClient.runTriggerChecks(playerId) : Promise.resolve([])),
    enabled: Boolean(playerId)
  });

export const useRunTriggerChecks = () =>
  useMutation({
    mutationFn: (playerId: string) => queryClient.runTriggerChecks(playerId, true)
  });

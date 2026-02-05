import { useMutation, useQuery } from '@tanstack/react-query';
import { queryClient } from '../api/queryClient';
import { NudgeLogRequest } from '../types/risk';

export const useNudgeLog = (playerId: string | null) =>
  useQuery({
    queryKey: ['nudge-log', playerId],
    queryFn: () => (playerId ? queryClient.getNudge(playerId) : Promise.resolve(null)),
    enabled: Boolean(playerId)
  });

export const useSaveNudge = () =>
  useMutation({
    mutationFn: (payload: NudgeLogRequest) => queryClient.saveNudge(payload)
  });

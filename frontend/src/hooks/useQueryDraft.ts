import { useMutation } from '@tanstack/react-query';
import { queryClient } from '../api/queryClient';
import { QueryDraftRequest } from '../types/risk';

export const useQueryDraft = () =>
  useMutation({
    mutationFn: (payload: QueryDraftRequest) => queryClient.draftSql(payload)
  });

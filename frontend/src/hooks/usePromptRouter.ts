import { useMutation } from '@tanstack/react-query';
import { aiClient } from '../api/aiClient';
import { PromptRouteRequest } from '../types/risk';

export const usePromptRouter = () =>
  useMutation({
    mutationFn: (payload: PromptRouteRequest) => aiClient.routePrompt(payload)
  });

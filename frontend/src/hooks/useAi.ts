import { useMutation } from '@tanstack/react-query';
import { aiClient } from '../api/aiClient';
import { RiskExplanationRequest } from '../types/risk';

export const useSemanticAudit = () =>
  useMutation({
    mutationFn: (payload: RiskExplanationRequest) => aiClient.semanticAudit(payload)
  });

export const useNudgeValidation = () =>
  useMutation({
    mutationFn: (nudgeText: string) => aiClient.validateNudge(nudgeText)
  });

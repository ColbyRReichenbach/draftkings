import {
  NudgeValidationResult,
  PromptRouteRequest,
  PromptRouteResponse,
  PromptLogEntry,
  RiskExplanationRequest,
  RiskExplanationResponse
} from '../types/risk';

import { request } from './httpClient';

export const aiClient = {
  semanticAudit: (payload: RiskExplanationRequest) =>
    request<RiskExplanationResponse>('/api/ai/semantic-audit', {
      method: 'POST',
      body: JSON.stringify(payload)
    }),
  validateNudge: (nudgeText: string) =>
    request<NudgeValidationResult>('/api/ai/validate-nudge', {
      method: 'POST',
      body: JSON.stringify({ nudge_text: nudgeText })
    }),
  getPromptLogs: (playerId: string) =>
    request<PromptLogEntry[]>(`/api/ai/logs/${playerId}`, {
      method: 'GET'
    }),
  routePrompt: (payload: PromptRouteRequest) =>
    request<PromptRouteResponse>('/api/ai/router', {
      method: 'POST',
      body: JSON.stringify(payload)
    })
};

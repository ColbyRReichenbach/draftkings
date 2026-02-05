import {
  NudgeValidationResult,
  PromptRouteRequest,
  PromptRouteResponse,
  PromptLogEntry,
  RiskExplanationRequest,
  RiskExplanationResponse
} from '../types/risk';

const BASE_URL =
  import.meta.env.VITE_API_BASE_URL ??
  import.meta.env.VITE_API_URL ??
  'http://localhost:8000';

const request = async <T>(path: string, options: RequestInit): Promise<T> => {
  const response = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(options.headers ?? {}) },
    ...options
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed with ${response.status}`);
  }

  return (await response.json()) as T;
};

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

import {
  AnalystNoteDraftRequest,
  AnalystNoteDraftResponse,
  AnalystNoteRequest,
  AnalystNoteResponse
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

export const notesClient = {
  submit: (payload: AnalystNoteRequest) =>
    request<AnalystNoteResponse>('/api/interventions/notes', {
      method: 'POST',
      body: JSON.stringify(payload)
    }),
  saveDraft: (payload: AnalystNoteDraftRequest) =>
    request<AnalystNoteDraftResponse>('/api/interventions/notes-draft', {
      method: 'POST',
      body: JSON.stringify(payload)
    }),
  getLatest: async (playerId: string) => {
    const response = await fetch(`${BASE_URL}/api/interventions/notes/${playerId}`);
    if (response.status === 404) {
      return null;
    }
    if (!response.ok) {
      const message = await response.text();
      throw new Error(message || `Request failed with ${response.status}`);
    }
    return (await response.json()) as AnalystNoteResponse;
  },
  getDraft: async (playerId: string) => {
    const response = await fetch(`${BASE_URL}/api/interventions/notes-draft/${playerId}`);
    if (response.status === 404) {
      return null;
    }
    if (!response.ok) {
      const message = await response.text();
      throw new Error(message || `Request failed with ${response.status}`);
    }
    return (await response.json()) as AnalystNoteDraftResponse;
  }
};

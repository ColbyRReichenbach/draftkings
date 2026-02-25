import {
  AnalystNoteDraftRequest,
  AnalystNoteDraftResponse,
  AnalystNoteRequest,
  AnalystNoteResponse
} from '../types/risk';
import { request, requestNullable } from './httpClient';

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
  getLatest: (playerId: string) =>
    requestNullable<AnalystNoteResponse>(`/api/interventions/notes/${playerId}`, {
      method: 'GET'
    }),
  getDraft: (playerId: string) =>
    requestNullable<AnalystNoteDraftResponse>(`/api/interventions/notes-draft/${playerId}`, {
      method: 'GET'
    })
};

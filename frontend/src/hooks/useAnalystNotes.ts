import { useMutation, useQuery } from '@tanstack/react-query';
import { notesClient } from '../api/notesClient';
import { AnalystNoteDraftRequest, AnalystNoteRequest } from '../types/risk';

export const useAnalystNotes = (playerId: string | null) =>
  useQuery({
    queryKey: ['analyst-notes', playerId],
    queryFn: () => (playerId ? notesClient.getLatest(playerId) : Promise.resolve(null)),
    enabled: Boolean(playerId),
    retry: false
  });

export const useSubmitAnalystNotes = () =>
  useMutation({
    mutationFn: (payload: AnalystNoteRequest) => notesClient.submit(payload)
  });

export const useDraftAnalystNotes = (playerId: string | null) =>
  useQuery({
    queryKey: ['analyst-notes-draft', playerId],
    queryFn: () => (playerId ? notesClient.getDraft(playerId) : Promise.resolve(null)),
    enabled: Boolean(playerId),
    retry: false
  });

export const useSaveDraftAnalystNotes = () =>
  useMutation({
    mutationFn: (payload: AnalystNoteDraftRequest) => notesClient.saveDraft(payload)
  });

import { create } from 'zustand';

export type UiTab = 'queue' | 'case' | 'analytics' | 'audit';

interface UiState {
  activeTab: UiTab;
  activeAuditPlayerId: string | null;
  setActiveTab: (tab: UiTab) => void;
  setActiveAuditPlayerId: (playerId: string | null) => void;
}

export const useUiStore = create<UiState>((set) => ({
  activeTab: 'queue',
  activeAuditPlayerId: null,
  setActiveTab: (tab) => set({ activeTab: tab }),
  setActiveAuditPlayerId: (playerId) => set({ activeAuditPlayerId: playerId })
}));

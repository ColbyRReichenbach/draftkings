import { create } from 'zustand';

export type UiTab = 'queue' | 'case' | 'analytics' | 'audit';

interface UiState {
  activeTab: UiTab;
  setActiveTab: (tab: UiTab) => void;
}

export const useUiStore = create<UiState>((set) => ({
  activeTab: 'queue',
  setActiveTab: (tab) => set({ activeTab: tab })
}));

import { create } from 'zustand';
import { RiskCategory } from '../types/risk';

interface QueueState {
  selectedCaseId: string | null;
  searchTerm: string;
  activeCategories: RiskCategory[];
  setSelectedCaseId: (caseId: string | null) => void;
  setSearchTerm: (term: string) => void;
  toggleCategory: (category: RiskCategory) => void;
  resetFilters: () => void;
}

const DEFAULT_CATEGORIES: RiskCategory[] = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'];

export const useQueueStore = create<QueueState>((set) => ({
  selectedCaseId: null,
  searchTerm: '',
  activeCategories: DEFAULT_CATEGORIES,
  setSelectedCaseId: (caseId) => set({ selectedCaseId: caseId }),
  setSearchTerm: (term) => set({ searchTerm: term }),
  toggleCategory: (category) =>
    set((state) => {
      const isActive = state.activeCategories.includes(category);
      const next = isActive
        ? state.activeCategories.filter((item) => item !== category)
        : [...state.activeCategories, category];
      return { activeCategories: next };
    }),
  resetFilters: () => set({ searchTerm: '', activeCategories: DEFAULT_CATEGORIES })
}));

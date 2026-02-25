import { CaseTimelineEntry } from '../types/risk';

const STORAGE_KEY = 'dk_static_replay_timeline_v1';
const PER_PLAYER_CAP = 20;

type ReplayStore = Record<string, CaseTimelineEntry[]>;

const loadStore = (): ReplayStore => {
  if (typeof window === 'undefined') {
    return {};
  }
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return {};
    }
    const parsed = JSON.parse(raw) as ReplayStore;
    return parsed && typeof parsed === 'object' ? parsed : {};
  } catch {
    return {};
  }
};

const saveStore = (store: ReplayStore): void => {
  if (typeof window === 'undefined') {
    return;
  }
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(store));
};

export const appendReplayTimelineEntry = (playerId: string, entry: CaseTimelineEntry): void => {
  const store = loadStore();
  const current = store[playerId] ?? [];
  const next = [entry, ...current].slice(0, PER_PLAYER_CAP);
  store[playerId] = next;
  saveStore(store);
};

export const getReplayTimelineEntries = (playerId: string): CaseTimelineEntry[] => {
  const store = loadStore();
  return store[playerId] ?? [];
};


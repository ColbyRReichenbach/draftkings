import { RiskCategory } from '../types/risk';
import { useQueueStore } from '../state/useQueueStore';

const CATEGORY_LABELS: RiskCategory[] = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'];

export const QueueFilters = () => {
  const searchTerm = useQueueStore((state) => state.searchTerm);
  const activeCategories = useQueueStore((state) => state.activeCategories);
  const setSearchTerm = useQueueStore((state) => state.setSearchTerm);
  const toggleCategory = useQueueStore((state) => state.toggleCategory);
  const resetFilters = useQueueStore((state) => state.resetFilters);

  return (
    <div className="glass-panel rounded-2xl p-5">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex-1">
          <label className="text-xs font-semibold uppercase tracking-wide text-slate-400">
            Search Player
          </label>
          <input
            value={searchTerm}
            onChange={(event) => setSearchTerm(event.target.value)}
            placeholder="Search by player ID or case"
            className="mt-2 w-full rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm focus:border-[#53B848] focus:outline-none"
          />
        </div>
        <button
          type="button"
          onClick={resetFilters}
          className="rounded-xl border border-slate-200 bg-white px-4 py-2 text-xs font-semibold uppercase tracking-wide text-slate-500 hover:text-slate-800"
        >
          Reset
        </button>
      </div>
      <div className="mt-4 flex flex-wrap gap-2">
        {CATEGORY_LABELS.map((category) => {
          const isActive = activeCategories.includes(category);
          return (
            <button
              key={category}
              type="button"
              onClick={() => toggleCategory(category)}
              className={`rounded-full border px-4 py-1 text-xs font-semibold transition-all ${
                isActive
                  ? 'border-slate-900 bg-slate-900 text-white'
                  : 'border-slate-200 bg-white text-slate-600'
              }`}
            >
              {category}
            </button>
          );
        })}
      </div>
    </div>
  );
};

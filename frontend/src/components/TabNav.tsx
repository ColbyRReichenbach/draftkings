import { UiTab, useUiStore } from '../state/useUiStore';

const TABS: { id: UiTab; label: string; description: string }[] = [
  { id: 'queue', label: 'Queue', description: 'Review risk cases' },
  { id: 'case', label: 'Case Detail', description: 'Evidence + actions' },
  { id: 'analytics', label: 'Analytics', description: 'Program health' },
  { id: 'audit', label: 'Audit Trail', description: 'Analyst history' }
];

export const TabNav = () => {
  const activeTab = useUiStore((state) => state.activeTab);
  const setActiveTab = useUiStore((state) => state.setActiveTab);

  return (
    <div className="flex flex-wrap gap-2">
      {TABS.map((tab) => {
        const isActive = tab.id === activeTab;
        return (
          <button
            key={tab.id}
            type="button"
            onClick={() => setActiveTab(tab.id)}
            className={`hover-lift relative rounded-full border px-4 py-2 text-sm font-semibold transition-all ${
              isActive
                ? 'border-[#53B848] bg-[#53B848] text-black shadow'
                : 'border-slate-700 bg-slate-900/70 text-slate-300 hover:border-slate-500 hover:text-slate-100'
            }`}
            aria-pressed={isActive}
            aria-label={tab.description}
          >
            {tab.label}
            {isActive ? (
              <span className="absolute -bottom-2 left-1/2 h-1.5 w-1.5 -translate-x-1/2 rounded-full bg-[#53B848]" />
            ) : null}
          </button>
        );
      })}
    </div>
  );
};

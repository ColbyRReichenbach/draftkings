import { UiTab, useUiStore } from '../state/useUiStore';

const NAV_ITEMS: { id: UiTab; label: string; icon: string }[] = [
    { id: 'queue', label: 'Queue', icon: 'list' },
    { id: 'case', label: 'Case File', icon: 'folder' },
    { id: 'analytics', label: 'Analytics', icon: 'bar-chart' },
    { id: 'audit', label: 'Audit Trail', icon: 'history' }
];

export const SidebarNav = () => {
    const activeTab = useUiStore((state) => state.activeTab);
    const setActiveTab = useUiStore((state) => state.setActiveTab);

    return (
        <aside className="fixed left-0 top-0 z-40 h-screen w-64 flex-col border-r border-dk-border bg-dk-black hidden md:flex">
            {/* Header / Logo */}
            <div className="flex h-20 items-center gap-3 border-b border-dk-border px-6">
                <div className="flex h-8 w-8 items-center justify-center rounded bg-dk-green font-display font-bold text-black">
                    DK
                </div>
                <div>
                    <span className="block font-display text-lg font-bold tracking-tight text-white uppercase">
                        Sentinel
                    </span>
                    <span className="block text-[10px] font-mono text-slate-400 uppercase tracking-wider">
                        Analyst Console
                    </span>
                </div>
            </div>

            {/* Navigation */}
            <nav className="flex-1 px-4 py-8 space-y-2">
                {NAV_ITEMS.map((item) => {
                    const isActive = activeTab === item.id;
                    return (
                        <button
                            key={item.id}
                            onClick={() => setActiveTab(item.id)}
                            className={`group flex w-full items-center gap-3 rounded-sm border-l-2 px-4 py-3 text-sm font-medium uppercase tracking-wide transition-all ${isActive
                                    ? 'border-dk-green bg-white/5 text-white shadow-[inset_10px_0_20px_-10px_rgba(83,184,72,0.1)]'
                                    : 'border-transparent text-slate-400 hover:bg-white/5 hover:text-slate-200'
                                }`}
                        >
                            {/* Icon Placeholder (or replace with lucide-react icons if available) */}
                            <span className={`block h-1.5 w-1.5 rounded-full ${isActive ? 'bg-dk-green' : 'bg-slate-600 group-hover:bg-slate-400'}`} />

                            {item.label}
                        </button>
                    );
                })}
            </nav>

            {/* User Footer */}
            <div className="border-t border-dk-border p-6">
                <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-full bg-slate-800 text-xs font-bold text-slate-300 ring-1 ring-dk-border">
                        CR
                    </div>
                    <div>
                        <p className="font-display text-sm font-semibold text-slate-200">
                            Colby Reichenbach
                        </p>
                        <p className="text-xs text-dk-green font-mono uppercase">
                            Online
                        </p>
                    </div>
                </div>
            </div>
        </aside>
    );
};

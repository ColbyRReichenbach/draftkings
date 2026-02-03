interface ActionBarProps {
  actions: string[];
}

export const ActionBar = ({ actions }: ActionBarProps) => (
  <div className="flex flex-wrap gap-2">
    {actions.map((action) => (
      <button
        key={action}
        type="button"
        className="rounded-xl border border-slate-200 bg-white px-4 py-2 text-xs font-semibold uppercase tracking-wide text-slate-600 hover:border-[#53B848] hover:text-slate-900"
      >
        {action}
      </button>
    ))}
  </div>
);

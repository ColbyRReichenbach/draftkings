interface KpiCardProps {
  label: string;
  value: string;
  trend?: string;
}

export const KpiCard = ({ label, value, trend }: KpiCardProps) => (
  <div className="glass-panel rounded-2xl p-5">
    <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">{label}</p>
    <p className="mt-2 font-display text-2xl text-slate-900">{value}</p>
    {trend ? <p className="mt-2 text-xs text-emerald-600">{trend}</p> : null}
  </div>
);

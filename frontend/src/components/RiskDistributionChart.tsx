import { AnalyticsSummary } from '../types/risk';

interface RiskDistributionChartProps {
  summary: AnalyticsSummary;
}

export const RiskDistributionChart = ({ summary }: RiskDistributionChartProps) => {
  const total =
    summary.risk_mix.critical +
    summary.risk_mix.high +
    summary.risk_mix.medium +
    summary.risk_mix.low;
  const rows = [
    { label: 'Critical', value: summary.risk_mix.critical, color: 'bg-red-500' },
    { label: 'High', value: summary.risk_mix.high, color: 'bg-[#F3701B]' },
    { label: 'Medium', value: summary.risk_mix.medium, color: 'bg-yellow-400' },
    { label: 'Low', value: summary.risk_mix.low, color: 'bg-[#53B848]' }
  ];

  return (
    <div className="glass-panel panel-sheen rounded-2xl p-6">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">Risk Distribution</p>
      <div className="mt-4 space-y-3">
        {rows.map((row) => (
          <div key={row.label}>
            <div className="flex items-center justify-between text-xs text-slate-400">
              <span>{row.label}</span>
              <span>{total > 0 ? Math.round((row.value / total) * 100) : 0}%</span>
            </div>
            <div className="mt-1 h-2 w-full rounded-full bg-slate-800">
              <div
                className={`h-2 rounded-full ${row.color}`}
                style={{ width: `${total > 0 ? (row.value / total) * 100 : 0}%` }}
              />
            </div>
            <div className="mt-1 text-[11px] text-slate-500">{row.value} cases</div>
          </div>
        ))}
      </div>
    </div>
  );
};

import { AnalyticsSummary } from '../types/risk';

interface RiskDistributionChartProps {
  summary: AnalyticsSummary;
}

export const RiskDistributionChart = ({ summary }: RiskDistributionChartProps) => {
  const rows = [
    { label: 'Critical', value: summary.critical_share, color: 'bg-red-500' },
    { label: 'High', value: summary.high_share, color: 'bg-[#F3701B]' },
    { label: 'Medium', value: summary.medium_share, color: 'bg-yellow-400' },
    { label: 'Low', value: summary.low_share, color: 'bg-[#53B848]' }
  ];

  return (
    <div className="glass-panel panel-sheen rounded-2xl p-6">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">Risk Distribution</p>
      <div className="mt-4 space-y-3">
        {rows.map((row) => (
          <div key={row.label}>
            <div className="flex items-center justify-between text-xs text-slate-400">
              <span>{row.label}</span>
              <span>{Math.round(row.value * 100)}%</span>
            </div>
            <div className="mt-1 h-2 w-full rounded-full bg-slate-800">
              <div className={`h-2 rounded-full ${row.color}`} style={{ width: `${row.value * 100}%` }} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

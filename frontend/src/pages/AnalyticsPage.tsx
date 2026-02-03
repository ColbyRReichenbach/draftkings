import { KpiCard } from '../components/KpiCard';
import { RiskDistributionChart } from '../components/RiskDistributionChart';
import { useAnalyticsSummary } from '../hooks/useRiskCases';

export const AnalyticsPage = () => {
  const { data: summary } = useAnalyticsSummary();

  if (!summary) {
    return (
      <div className="glass-panel rounded-2xl p-6 text-slate-400">
        Loading analytics summary...
      </div>
    );
  }

  return (
    <div className="grid gap-6">
      <div className="grid gap-4 md:grid-cols-3">
        <KpiCard label="Open Cases" value={summary.total_cases.toString()} trend="+6% week-over-week" />
        <KpiCard label="Avg Risk Score" value={summary.avg_risk_score.toFixed(2)} trend="Stable" />
        <KpiCard label="Critical Share" value={`${Math.round(summary.critical_share * 100)}%`} />
      </div>
      <div className="grid gap-6 lg:grid-cols-[1.2fr_1fr]">
        <div className="glass-panel panel-sheen rounded-2xl p-6">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">Weekly Queue Volume</p>
          <div className="mt-4 grid gap-3">
            {summary.weekly_trend.map((row) => (
              <div key={row.week} className="flex items-center gap-3">
                <span className="w-12 text-xs text-slate-400">{row.week}</span>
                <div className="h-2 flex-1 rounded-full bg-slate-800">
                  <div
                    className="h-2 rounded-full bg-[#53B848]"
                    style={{ width: `${(row.cases / summary.total_cases) * 100}%` }}
                  />
                </div>
                <span className="text-xs text-slate-400">{row.cases}</span>
              </div>
            ))}
          </div>
        </div>
        <RiskDistributionChart summary={summary} />
      </div>
    </div>
  );
};

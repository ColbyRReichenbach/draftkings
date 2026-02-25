import { KpiCard } from '../components/KpiCard';
import { RiskDistributionChart } from '../components/RiskDistributionChart';
import { useAnalyticsSummary } from '../hooks/useRiskCases';

export const AnalyticsPage = () => {
  const { data: summary, error } = useAnalyticsSummary();

  if (error) {
    return (
      <div className="glass-panel rounded-2xl border border-rose-800/60 bg-rose-950/20 p-6 text-rose-200">
        Unable to load analytics summary. In live mode this requires backend API access.
      </div>
    );
  }

  if (!summary) {
    return (
      <div className="glass-panel rounded-2xl p-6 text-slate-400">
        Loading analytics summary...
      </div>
    );
  }

  const sqlPerCase =
    summary.total_cases_started > 0
      ? summary.sql_queries_logged / summary.total_cases_started
      : 0;
  const llmPerCase =
    summary.total_cases_started > 0
      ? summary.llm_prompts_logged / summary.total_cases_started
      : 0;
  const casesWithSqlPct = Math.round(summary.cases_with_sql_pct * 100);
  const casesWithLlmPct = Math.round(summary.cases_with_llm_pct * 100);

  return (
    <div className="grid gap-6">
      <div className="grid gap-4 md:grid-cols-3">
        <KpiCard
          label="Total Cases Reviewed"
          value={summary.total_cases_started.toString()}
          trend="Analyst throughput"
        />
        <KpiCard label="In Progress" value={summary.in_progress_count.toString()} trend="Active cases" />
        <KpiCard
          label="Submitted"
          value={summary.total_cases_submitted.toString()}
          trend="Completed decisions"
        />
        <KpiCard
          label="Avg Time to Submit"
          value={`${summary.avg_time_to_submit_hours.toFixed(1)} hrs`}
          trend="Decision velocity"
        />
        <KpiCard label="SQL Queries Logged" value={summary.sql_queries_logged.toString()} />
        <KpiCard label="LLM Prompts Logged" value={summary.llm_prompts_logged.toString()} />
      </div>

      <div className="grid gap-6 lg:grid-cols-[1.1fr_1fr]">
        <div className="glass-panel panel-sheen rounded-2xl p-6">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">Case Funnel</p>
          <div className="mt-4 grid gap-4 sm:grid-cols-3">
            {[
              { label: 'Queued', value: summary.funnel.queued },
              { label: 'Started', value: summary.funnel.started },
              { label: 'Submitted', value: summary.funnel.submitted }
            ].map((row) => (
              <div key={row.label} className="rounded-xl border border-slate-800/70 bg-slate-950/40 p-4">
                <p className="text-xs uppercase tracking-wide text-slate-500">{row.label}</p>
                <p className="mt-2 text-2xl font-semibold text-slate-100">{row.value}</p>
              </div>
            ))}
          </div>
          <div className="mt-5 text-xs text-slate-500">
            Queue refills maintain analyst focus while preserving in-progress work.
          </div>
        </div>
        <RiskDistributionChart summary={summary} />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="glass-panel panel-sheen rounded-2xl p-6">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">Analyst Rigor</p>
          <div className="mt-4 grid gap-4 sm:grid-cols-2">
            <div className="rounded-xl border border-slate-800/70 bg-slate-950/40 p-4">
              <p className="text-xs text-slate-500">Cases with SQL Evidence</p>
              <p className="mt-2 text-xl font-semibold text-slate-100">{casesWithSqlPct}%</p>
              <p className="text-xs text-slate-500">{sqlPerCase.toFixed(2)} queries per case</p>
            </div>
            <div className="rounded-xl border border-slate-800/70 bg-slate-950/40 p-4">
              <p className="text-xs text-slate-500">Cases with LLM Transparency</p>
              <p className="mt-2 text-xl font-semibold text-slate-100">{casesWithLlmPct}%</p>
              <p className="text-xs text-slate-500">{llmPerCase.toFixed(2)} prompts per case</p>
            </div>
          </div>
        </div>

        <div className="glass-panel panel-sheen rounded-2xl p-6">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">Compliance & Quality</p>
          <div className="mt-4 grid gap-4 sm:grid-cols-2">
            <div className="rounded-xl border border-slate-800/70 bg-slate-950/40 p-4">
              <p className="text-xs text-slate-500">Trigger Checks Run</p>
              <p className="mt-2 text-xl font-semibold text-slate-100">{summary.trigger_checks_run}</p>
            </div>
            <div className="rounded-xl border border-slate-800/70 bg-slate-950/40 p-4">
              <p className="text-xs text-slate-500">Nudges Validated</p>
              <p className="mt-2 text-xl font-semibold text-slate-100">{summary.nudges_validated}</p>
            </div>
          </div>
          <div className="mt-4 text-xs text-slate-500">
            AI assistance is logged; analysts retain final decision ownership.
          </div>
        </div>
      </div>
    </div>
  );
};

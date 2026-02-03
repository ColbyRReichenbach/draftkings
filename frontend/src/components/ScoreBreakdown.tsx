import { CaseDetail } from '../types/risk';

interface ScoreBreakdownProps {
  detail: CaseDetail;
}

const formatScore = (value: number) => `${Math.round(value * 100)}%`;

export const ScoreBreakdown = ({ detail }: ScoreBreakdownProps) => {
  const scores = detail.evidence_snapshot;

  return (
    <div className="panel-sheen grid gap-3 rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">Component Scores</p>
      <div className="grid gap-3 sm:grid-cols-2">
        {[
          { label: 'Loss Chase', value: scores.loss_chase_score },
          { label: 'Bet Escalation', value: scores.bet_escalation_score },
          { label: 'Market Drift', value: scores.market_drift_score },
          { label: 'Temporal Risk', value: scores.temporal_risk_score },
          { label: 'Gamalyze', value: scores.gamalyze_risk_score }
        ].map((item) => (
          <div
            key={item.label}
            className="flex items-center justify-between rounded-xl bg-slate-950/60 px-3 py-2"
          >
            <span className="text-sm text-slate-400">{item.label}</span>
            <span className="text-sm font-semibold text-slate-100">{formatScore(item.value)}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

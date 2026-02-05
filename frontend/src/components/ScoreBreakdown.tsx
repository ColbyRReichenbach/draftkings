import { CaseDetail } from '../types/risk';
import { InfoBadge } from './InfoBadge';

interface ScoreBreakdownProps {
  detail: CaseDetail;
}

const formatScore = (value: number) => value.toFixed(2);

const SCORE_TOOLTIP =
  'Normalized 0–1 scale. 0.00–0.39 = Low, 0.40–0.59 = Medium, 0.60–0.79 = High, 0.80–1.00 = Critical.';

const TOOLTIP_MAP: Record<string, string> = {
  'Loss Chase': `${SCORE_TOOLTIP} Higher values indicate loss-chasing behavior (bets after losses).`,
  'Bet Escalation': `${SCORE_TOOLTIP} Higher values indicate increasing bet size after losses.`,
  'Market Drift': `${SCORE_TOOLTIP} Higher values indicate drift into atypical sports/market tiers or hours.`,
  'Temporal Risk': `${SCORE_TOOLTIP} Higher values indicate abnormal late-night activity vs baseline.`,
  'Gamalyze': `${SCORE_TOOLTIP} External neuro-marker composite (Mindway AI).`
};

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
          <InfoBadge
            key={item.label}
            label={TOOLTIP_MAP[item.label] ?? SCORE_TOOLTIP}
            className="rounded-xl bg-slate-950/60 px-3 py-2"
          >
            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-400">{item.label}</span>
              <span className="text-sm font-semibold text-slate-100">
                {formatScore(item.value)}
                <span className="ml-2 text-xs text-slate-500">
                  ({Math.round(item.value * 100)}%)
                </span>
              </span>
            </div>
          </InfoBadge>
        ))}
      </div>
    </div>
  );
};

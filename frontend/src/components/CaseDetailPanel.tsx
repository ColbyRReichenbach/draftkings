import { CaseDetail } from '../types/risk';
import { ScoreBreakdown } from './ScoreBreakdown';
import { NudgePreview } from './NudgePreview';
import { ActionBar } from './ActionBar';
import { useNudgeValidation, useSemanticAudit } from '../hooks/useAi';

interface CaseDetailPanelProps {
  detail: CaseDetail | null;
}

export const CaseDetailPanel = ({ detail }: CaseDetailPanelProps) => {
  const semanticAudit = useSemanticAudit();
  const nudgeValidation = useNudgeValidation();

  if (!detail) {
    return (
      <div className="glass-panel flex h-full items-center justify-center rounded-2xl p-8 text-center text-slate-500">
        Select a case from the queue to view details.
      </div>
    );
  }

  const explanation = semanticAudit.data?.explanation ?? detail.ai_explanation;
  const regulatoryNotes = semanticAudit.data?.regulatory_notes ?? detail.regulatory_notes;
  const nudgeText = semanticAudit.data?.draft_customer_nudge ?? detail.draft_nudge;

  const handleGenerateExplanation = () => {
    semanticAudit.mutate({
      player_id: detail.player_id,
      composite_risk_score: detail.composite_risk_score,
      risk_category: detail.risk_category,
      total_bets_7d: detail.evidence_snapshot.total_bets_7d,
      total_wagered_7d: detail.evidence_snapshot.total_wagered_7d,
      loss_chase_score: detail.evidence_snapshot.loss_chase_score,
      bet_escalation_score: detail.evidence_snapshot.bet_escalation_score,
      market_drift_score: detail.evidence_snapshot.market_drift_score,
      temporal_risk_score: detail.evidence_snapshot.temporal_risk_score,
      gamalyze_risk_score: detail.evidence_snapshot.gamalyze_risk_score,
      state_jurisdiction: detail.state_jurisdiction
    });
  };

  const handleValidateNudge = () => {
    nudgeValidation.mutate(nudgeText);
  };

  return (
    <div className="glass-panel flex flex-col gap-4 rounded-2xl p-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">Case Detail</p>
          <h2 className="font-display text-2xl text-slate-900">{detail.player_id}</h2>
          <p className="text-sm text-slate-500">
            {detail.case_id} • {detail.state_jurisdiction}
          </p>
        </div>
        <div className="rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white">
          Score {(detail.composite_risk_score * 100).toFixed(0)}%
        </div>
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white p-4">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">Evidence Snapshot</p>
        <div className="mt-3 grid gap-3 sm:grid-cols-2">
          <div className="rounded-xl bg-slate-50 p-3">
            <p className="text-xs text-slate-500">Total Bets (7d)</p>
            <p className="text-lg font-semibold text-slate-900">
              {detail.evidence_snapshot.total_bets_7d}
            </p>
          </div>
          <div className="rounded-xl bg-slate-50 p-3">
            <p className="text-xs text-slate-500">Total Wagered (7d)</p>
            <p className="text-lg font-semibold text-slate-900">
              ${detail.evidence_snapshot.total_wagered_7d.toLocaleString()}
            </p>
          </div>
          <div className="rounded-xl bg-slate-50 p-3">
            <p className="text-xs text-slate-500">Regulatory Notes</p>
            <p className="text-sm text-slate-700">{regulatoryNotes}</p>
          </div>
          <div className="rounded-xl bg-slate-50 p-3">
            <p className="text-xs text-slate-500">AI Explanation</p>
            <p className="text-sm text-slate-700">{explanation}</p>
          </div>
        </div>
      </div>

      <ScoreBreakdown detail={detail} />

      <div className="rounded-2xl border border-slate-200 bg-white p-4">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">AI Actions</p>
        <div className="mt-3 flex flex-wrap gap-2">
          <button
            type="button"
            onClick={handleGenerateExplanation}
            className="rounded-xl bg-[#53B848] px-4 py-2 text-xs font-semibold uppercase tracking-wide text-white hover:bg-[#469a3a]"
            disabled={semanticAudit.isPending}
          >
            {semanticAudit.isPending ? 'Generating...' : 'Generate Explanation'}
          </button>
          <button
            type="button"
            onClick={handleValidateNudge}
            className="rounded-xl border border-slate-200 bg-white px-4 py-2 text-xs font-semibold uppercase tracking-wide text-slate-600 hover:border-slate-300"
            disabled={nudgeValidation.isPending}
          >
            {nudgeValidation.isPending ? 'Validating...' : 'Validate Nudge'}
          </button>
          {semanticAudit.isError ? (
            <span className="text-xs text-red-600">AI request failed. Check API.</span>
          ) : null}
        </div>
      </div>

      <NudgePreview
        nudgeText={nudgeText}
        validationResult={nudgeValidation.data ?? null}
        isValidating={nudgeValidation.isPending}
      />

      <div>
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">Recommended Actions</p>
        <div className="mt-2">
          <ActionBar actions={detail.analyst_actions} />
        </div>
      </div>
    </div>
  );
};

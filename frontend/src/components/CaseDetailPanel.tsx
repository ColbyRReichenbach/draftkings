import { CaseDetail, CaseStatusEntry } from '../types/risk';
import { ScoreBreakdown } from './ScoreBreakdown';
import { NudgePreview } from './NudgePreview';
import { ActionBar } from './ActionBar';
import { PromptLogPanel } from './PromptLogPanel';
import { useNudgeValidation, usePromptLogs, useSemanticAudit } from '../hooks/useAi';
import { useStartCase } from '../hooks/useCaseTimeline';
import { useUiStore } from '../state/useUiStore';
import { useQueryClient } from '@tanstack/react-query';

const DEFAULT_ANALYST_ID = 'Colby Reichenbach';

interface CaseDetailPanelProps {
  detail: CaseDetail | null;
}

export const CaseDetailPanel = ({ detail }: CaseDetailPanelProps) => {
  const semanticAudit = useSemanticAudit();
  const nudgeValidation = useNudgeValidation();
  const promptLogs = usePromptLogs(detail?.player_id ?? null);
  const startCase = useStartCase();
  const setActiveTab = useUiStore((state) => state.setActiveTab);
  const setActiveAuditPlayerId = useUiStore((state) => state.setActiveAuditPlayerId);
  const reactQuery = useQueryClient();

  const explanation = semanticAudit.data?.explanation ?? '';
  const regulatoryNotes = semanticAudit.data?.regulatory_notes ?? detail?.regulatory_notes ?? '';
  const nudgeText = semanticAudit.data?.draft_customer_nudge ?? detail?.draft_nudge ?? '';

  const handleGenerateExplanation = () => {
    if (!detail) {
      return;
    }
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

  const handleStartCase = () => {
    if (!detail) {
      return;
    }
    const optimisticStatus = {
      case_id: detail.case_id,
      player_id: detail.player_id,
      analyst_id: DEFAULT_ANALYST_ID,
      status: 'IN_PROGRESS' as const,
      started_at: new Date().toISOString(),
      submitted_at: null,
      updated_at: new Date().toISOString()
    };
    reactQuery.setQueryData(['case-statuses'], (prev: CaseStatusEntry[] | undefined) => {
      const next = prev ? [...prev] : [];
      const existingIndex = next.findIndex((row) => row.case_id === detail.case_id);
      if (existingIndex >= 0) {
        next[existingIndex] = optimisticStatus;
      } else {
        next.push(optimisticStatus);
      }
      return next;
    });
    setActiveAuditPlayerId(detail.player_id);
    setActiveTab('audit');
    startCase.mutate(
      {
        case_id: detail.case_id,
        player_id: detail.player_id,
        analyst_id: DEFAULT_ANALYST_ID
      },
      {
        onSuccess: () => {
          reactQuery.invalidateQueries({ queryKey: ['case-statuses'] });
        }
      }
    );
  };

  if (!detail) {
    return (
      <div className="glass-panel flex h-full items-center justify-center rounded-2xl p-8 text-center text-slate-400">
        Select a case from the queue to view details.
      </div>
    );
  }

  return (
    <div className="glass-panel panel-sheen flex flex-col gap-4 overflow-visible rounded-2xl p-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">Case Detail</p>
          <h2 className="font-display text-2xl text-slate-100">{detail.player_id}</h2>
          <p className="text-sm text-slate-400">
            {detail.case_id} • {detail.state_jurisdiction}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <div className="rounded-full bg-slate-950 px-4 py-2 text-sm font-semibold text-slate-100">
            Score {(detail.composite_risk_score * 100).toFixed(0)}%
          </div>
          <span className="group relative inline-flex items-center">
            <button
              type="button"
              onClick={handleStartCase}
              disabled={startCase.isPending}
              className="hover-lift rounded-xl border border-slate-700 bg-[#F3701B] px-4 py-2 text-xs font-semibold uppercase tracking-wide text-black disabled:cursor-not-allowed disabled:bg-slate-700 disabled:text-slate-400"
            >
              {startCase.isPending ? 'Starting...' : 'Start Case Review'}
            </button>
            <span className="pointer-events-none absolute left-1/2 top-full z-10 mt-2 w-64 -translate-x-1/2 rounded-xl border border-slate-700 bg-slate-950/95 p-2 text-[11px] text-slate-200 opacity-0 shadow-xl transition-opacity duration-150 group-hover:opacity-100">
              Starts an audit trail workbench entry for analyst notes, SQL, and AI logs.
            </span>
          </span>
        </div>
      </div>

      <div className="panel-sheen rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">Evidence Snapshot</p>
        <div className="mt-3 grid gap-3 sm:grid-cols-2">
          <div className="rounded-xl bg-slate-950/60 p-3">
            <p className="text-xs text-slate-400">Total Bets (7d)</p>
            <p className="text-lg font-semibold text-slate-100">
              {detail.evidence_snapshot.total_bets_7d}
            </p>
          </div>
          <div className="rounded-xl bg-slate-950/60 p-3">
            <p className="text-xs text-slate-400">Total Wagered (7d)</p>
            <p className="text-lg font-semibold text-slate-100">
              ${detail.evidence_snapshot.total_wagered_7d.toLocaleString()}
            </p>
          </div>
          <div className="rounded-xl bg-slate-950/60 p-3">
            <p className="text-xs text-slate-400">Regulatory Notes</p>
            <p className="text-sm text-slate-300">{regulatoryNotes}</p>
          </div>
          <div className="rounded-xl bg-slate-950/60 p-3">
            <p className="text-xs text-slate-400">AI Summary</p>
            <p className="text-sm text-slate-300">
              {explanation
                ? explanation
                : 'No AI summary yet. Click “Draft AI Summary” to generate a draft.'}
            </p>
          </div>
        </div>
      </div>

      <ScoreBreakdown detail={detail} />

      <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
          Analyst Guidance (AI Assist)
        </p>
        <p className="mt-2 text-sm text-slate-300">
          Review independent signals before escalating. Use the Case File to document
          rationale, SQL evidence, and final decision.
        </p>
      </div>

      <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">AI Actions</p>
        <div className="mt-3 flex flex-wrap gap-2">
          <button
            type="button"
            onClick={handleGenerateExplanation}
            className="hover-lift rounded-xl bg-[#53B848] px-4 py-2 text-xs font-semibold uppercase tracking-wide text-black hover:bg-[#469a3a]"
            disabled={semanticAudit.isPending}
          >
            {semanticAudit.isPending ? 'Drafting...' : 'Draft AI Summary'}
          </button>
          <button
            type="button"
            onClick={handleValidateNudge}
            className="hover-lift rounded-xl border border-slate-700 bg-slate-900/70 px-4 py-2 text-xs font-semibold uppercase tracking-wide text-slate-300 hover:border-slate-500"
            disabled={nudgeValidation.isPending}
          >
            {nudgeValidation.isPending ? 'Validating...' : 'Validate Nudge'}
          </button>
          {semanticAudit.isError ? (
            <span className="text-xs text-red-300">AI request failed. Check API.</span>
          ) : null}
        </div>
        <p className="mt-2 text-xs text-slate-400">
          AI drafts are assistive only. Analyst approval is required.
        </p>
      </div>

      <NudgePreview
        nudgeText={nudgeText}
        validationResult={nudgeValidation.data ?? null}
        isValidating={nudgeValidation.isPending}
      />

      <PromptLogPanel logs={promptLogs.data ?? []} />

      <div>
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">Recommended Actions</p>
        <div className="mt-2">
          <ActionBar actions={detail.analyst_actions} />
        </div>
      </div>
    </div>
  );
};

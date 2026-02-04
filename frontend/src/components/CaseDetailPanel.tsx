import { useEffect, useMemo, useState } from 'react';
import { CaseDetail } from '../types/risk';
import { ScoreBreakdown } from './ScoreBreakdown';
import { NudgePreview } from './NudgePreview';
import { ActionBar } from './ActionBar';
import { PromptLogPanel } from './PromptLogPanel';
import { useNudgeValidation, usePromptLogs, useSemanticAudit } from '../hooks/useAi';
import { useAnalystNotes, useSubmitAnalystNotes } from '../hooks/useAnalystNotes';

interface CaseDetailPanelProps {
  detail: CaseDetail | null;
}

const ACTION_OPTIONS = [
  'Monitor',
  'Supportive nudge',
  'Outreach call',
  'Temporary limit',
  'Account review',
  'No action'
];

export const CaseDetailPanel = ({ detail }: CaseDetailPanelProps) => {
  const semanticAudit = useSemanticAudit();
  const nudgeValidation = useNudgeValidation();
  const promptLogs = usePromptLogs(detail?.player_id ?? null);
  const notesQuery = useAnalystNotes(detail?.player_id ?? null);
  const submitNotes = useSubmitAnalystNotes();

  const [notes, setNotes] = useState('');
  const [action, setAction] = useState('');

  useEffect(() => {
    if (notesQuery.data) {
      setNotes(notesQuery.data.analyst_notes);
      setAction(notesQuery.data.analyst_action);
    } else {
      setNotes('');
      setAction('');
    }
  }, [notesQuery.data]);

  const canSubmit = notes.trim().length >= 10 && action.length > 0 && detail;

  const explanation = semanticAudit.data?.explanation ?? detail?.ai_explanation ?? '';
  const regulatoryNotes = semanticAudit.data?.regulatory_notes ?? detail?.regulatory_notes ?? '';
  const nudgeText = semanticAudit.data?.draft_customer_nudge ?? detail?.draft_nudge ?? '';

  const lastSaved = useMemo(() => notesQuery.data?.created_at, [notesQuery.data]);

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

  const handleSubmitNotes = () => {
    if (!detail || !canSubmit) {
      return;
    }
    submitNotes.mutate({
      player_id: detail.player_id,
      analyst_id: 'Colby Reichenbach',
      analyst_action: action,
      analyst_notes: notes.trim()
    });
  };

  if (!detail) {
    return (
      <div className="glass-panel flex h-full items-center justify-center rounded-2xl p-8 text-center text-slate-400">
        Select a case from the queue to view details.
      </div>
    );
  }

  return (
    <div className="glass-panel panel-sheen flex flex-col gap-4 rounded-2xl p-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">Case Detail</p>
          <h2 className="font-display text-2xl text-slate-100">{detail.player_id}</h2>
          <p className="text-sm text-slate-400">
            {detail.case_id} • {detail.state_jurisdiction}
          </p>
        </div>
        <div className="rounded-full bg-slate-950 px-4 py-2 text-sm font-semibold text-slate-100">
          Score {(detail.composite_risk_score * 100).toFixed(0)}%
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
            <p className="text-sm text-slate-300">{explanation}</p>
          </div>
        </div>
      </div>

      <ScoreBreakdown detail={detail} />

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

      <div className="panel-sheen rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">Analyst Notes</p>
        <textarea
          value={notes}
          onChange={(event) => setNotes(event.target.value)}
          placeholder="Document rationale, evidence reviewed, and decision context..."
          className="mt-3 h-28 w-full rounded-xl border border-slate-700 bg-slate-950/60 px-3 py-2 text-sm text-slate-100 placeholder:text-slate-500 focus:border-[#53B848] focus:outline-none"
        />
        <div className="mt-3 flex flex-wrap items-center gap-3">
          <select
            value={action}
            onChange={(event) => setAction(event.target.value)}
            className="rounded-xl border border-slate-700 bg-slate-950/60 px-3 py-2 text-sm text-slate-100"
          >
            <option value="" disabled>
              Select action
            </option>
            {ACTION_OPTIONS.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
          <button
            type="button"
            onClick={handleSubmitNotes}
            disabled={!canSubmit || submitNotes.isPending}
            className="hover-lift rounded-xl border border-slate-700 bg-[#53B848] px-4 py-2 text-xs font-semibold uppercase tracking-wide text-black disabled:cursor-not-allowed disabled:bg-slate-700 disabled:text-slate-400"
          >
            {submitNotes.isPending ? 'Saving...' : 'Submit Decision'}
          </button>
          {submitNotes.isSuccess ? (
            <span className="text-xs text-emerald-300">Saved.</span>
          ) : null}
          {submitNotes.isError ? (
            <span className="text-xs text-red-300">Save failed.</span>
          ) : null}
        </div>
        {lastSaved ? (
          <p className="mt-2 text-xs text-slate-400">Last saved: {new Date(lastSaved).toLocaleString()}</p>
        ) : null}
      </div>

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

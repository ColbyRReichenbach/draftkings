import { AuditEntry, CaseDetail, CaseStatusEntry } from '../types/risk';
import { ScoreBreakdown } from './ScoreBreakdown';
import { InfoBadge } from './InfoBadge';
import { ActionBar } from './ActionBar';
import { PromptLogPanel } from './PromptLogPanel';
import { usePromptLogs } from '../hooks/useAi';
import { useStartCase } from '../hooks/useCaseTimeline';
import { useUiStore } from '../state/useUiStore';
import { useQueryClient } from '@tanstack/react-query';

const DEFAULT_ANALYST_ID = 'Colby Reichenbach';

interface CaseDetailPanelProps {
  detail: CaseDetail | null;
}

const SCORE_TOOLTIP =
  'Normalized 0–1 scale. 0.00–0.39 = Low, 0.40–0.59 = Medium, 0.60–0.79 = High, 0.80–1.00 = Critical.';

const KPI_TOOLTIPS: Record<string, string> = {
  'Total Bets (7d)':
    'Total count of bets in the last 7 days. Minimum 2 bets required for ratios to be meaningful.',
  'Total Wagered (7d)':
    'Total wagered amount over the last 7 days. Use with bet count to normalize behavior.',
  'Loss Chase Score': `${SCORE_TOOLTIP} Higher values indicate bets placed after losses.`,
  'Bet Escalation': `${SCORE_TOOLTIP} Higher values indicate larger bets after losses vs wins.`,
  'Market Drift': `${SCORE_TOOLTIP} Higher values indicate drift into atypical sports/market tiers.`,
  'Temporal Risk': `${SCORE_TOOLTIP} Higher values indicate abnormal late-night activity vs baseline.`,
  'Gamalyze': `${SCORE_TOOLTIP} External neuro-marker composite (Mindway AI).`
};

export const CaseDetailPanel = ({ detail }: CaseDetailPanelProps) => {
  const promptLogs = usePromptLogs(detail?.player_id ?? null);
  const startCase = useStartCase();
  const setActiveTab = useUiStore((state) => state.setActiveTab);
  const setActiveAuditPlayerId = useUiStore((state) => state.setActiveAuditPlayerId);
  const reactQuery = useQueryClient();

  const regulatoryNotes = detail?.regulatory_notes ?? '';

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
    startCase.mutate(
      {
        case_id: detail.case_id,
        player_id: detail.player_id,
        analyst_id: DEFAULT_ANALYST_ID
      },
      {
        onSuccess: () => {
          reactQuery.invalidateQueries({ queryKey: ['case-statuses'] });
          reactQuery.invalidateQueries({ queryKey: ['risk-cases'] });
          reactQuery.invalidateQueries({ queryKey: ['audit-trail'] });
          reactQuery.setQueryData(['audit-trail'], (prev: AuditEntry[] | undefined) => {
            const next = prev ? [...prev] : [];
            const already = next.find((row) => row.case_id === detail.case_id);
            if (!already) {
              next.unshift({
                audit_id: detail.case_id,
                case_id: detail.case_id,
                player_id: detail.player_id,
                analyst_id: DEFAULT_ANALYST_ID,
                action: 'Case review started',
                risk_category: detail.risk_category,
                state_jurisdiction: detail.state_jurisdiction,
                timestamp: new Date().toISOString(),
                notes: 'Audit trail entry created after Start Case Review.'
              });
            }
            return next;
          });
          setActiveAuditPlayerId(detail.player_id);
          setActiveTab('audit');
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

      <div className="panel-sheen rounded-2xl border border-slate-800 bg-slate-900/70 p-4 overflow-visible">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">Evidence Snapshot</p>
        <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          <InfoBadge label={KPI_TOOLTIPS['Total Bets (7d)']} className="rounded-xl bg-slate-950/60 p-3">
            <p className="text-xs text-slate-400">Total Bets (7d)</p>
            <p className="text-lg font-semibold text-slate-100">
              {detail.evidence_snapshot.total_bets_7d}
            </p>
          </InfoBadge>
          <InfoBadge label={KPI_TOOLTIPS['Total Wagered (7d)']} className="rounded-xl bg-slate-950/60 p-3">
            <p className="text-xs text-slate-400">Total Wagered (7d)</p>
            <p className="text-lg font-semibold text-slate-100">
              ${detail.evidence_snapshot.total_wagered_7d.toLocaleString()}
            </p>
          </InfoBadge>
          <div className="rounded-xl bg-slate-950/60 p-3">
            <p className="text-xs text-slate-400">Regulatory Notes</p>
            <p className="text-sm text-slate-300">{regulatoryNotes}</p>
          </div>
          <div className="rounded-xl bg-slate-950/60 p-3">
            <p className="text-xs text-slate-400">AI Summary</p>
            <p className="text-sm text-slate-300">
              No AI summary yet. Use the Case File workbench to draft an AI summary.
            </p>
          </div>
          <InfoBadge label={KPI_TOOLTIPS['Loss Chase Score']} className="rounded-xl bg-slate-950/60 p-3">
            <p className="text-xs text-slate-400">Loss Chase Score</p>
            <p className="text-lg font-semibold text-slate-100">
              {detail.evidence_snapshot.loss_chase_score.toFixed(2)}
              <span className="ml-2 text-xs text-slate-500">
                ({Math.round(detail.evidence_snapshot.loss_chase_score * 100)}%)
              </span>
            </p>
          </InfoBadge>
          <InfoBadge label={KPI_TOOLTIPS['Bet Escalation']} className="rounded-xl bg-slate-950/60 p-3">
            <p className="text-xs text-slate-400">Bet Escalation</p>
            <p className="text-lg font-semibold text-slate-100">
              {detail.evidence_snapshot.bet_escalation_score.toFixed(2)}
              <span className="ml-2 text-xs text-slate-500">
                ({Math.round(detail.evidence_snapshot.bet_escalation_score * 100)}%)
              </span>
            </p>
          </InfoBadge>
          <InfoBadge label={KPI_TOOLTIPS['Market Drift']} className="rounded-xl bg-slate-950/60 p-3">
            <p className="text-xs text-slate-400">Market Drift</p>
            <p className="text-lg font-semibold text-slate-100">
              {detail.evidence_snapshot.market_drift_score.toFixed(2)}
              <span className="ml-2 text-xs text-slate-500">
                ({Math.round(detail.evidence_snapshot.market_drift_score * 100)}%)
              </span>
            </p>
          </InfoBadge>
          <InfoBadge label={KPI_TOOLTIPS['Temporal Risk']} className="rounded-xl bg-slate-950/60 p-3">
            <p className="text-xs text-slate-400">Temporal Risk</p>
            <p className="text-lg font-semibold text-slate-100">
              {detail.evidence_snapshot.temporal_risk_score.toFixed(2)}
              <span className="ml-2 text-xs text-slate-500">
                ({Math.round(detail.evidence_snapshot.temporal_risk_score * 100)}%)
              </span>
            </p>
          </InfoBadge>
          <InfoBadge label={KPI_TOOLTIPS['Gamalyze']} className="rounded-xl bg-slate-950/60 p-3">
            <p className="text-xs text-slate-400">Gamalyze</p>
            <p className="text-lg font-semibold text-slate-100">
              {detail.evidence_snapshot.gamalyze_risk_score.toFixed(2)}
              <span className="ml-2 text-xs text-slate-500">
                ({Math.round(detail.evidence_snapshot.gamalyze_risk_score * 100)}%)
              </span>
            </p>
          </InfoBadge>
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

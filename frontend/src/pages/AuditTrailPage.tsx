import { Suspense, lazy, useMemo, useState } from 'react';
import { AuditTrailTable } from '../components/AuditTrailTable';
import { useAuditTrail } from '../hooks/useAuditTrail';
import { useCaseStatuses } from '../hooks/useCaseTimeline';
import { useRiskCases } from '../hooks/useRiskCases';
import { CaseStatus } from '../types/risk';
import { useUiStore } from '../state/useUiStore';
const CaseFilePage = lazy(() =>
  import('./CaseFilePage').then((module) => ({ default: module.CaseFilePage }))
);

export const AuditTrailPage = () => {
  const { data: entries } = useAuditTrail();
  const { data: statuses } = useCaseStatuses();
  const { data: riskCases = [] } = useRiskCases();
  const activeAuditPlayerId = useUiStore((state) => state.activeAuditPlayerId);
  const setActiveAuditPlayerId = useUiStore((state) => state.setActiveAuditPlayerId);
  const [statusFilter, setStatusFilter] = useState<CaseStatus | 'ALL'>('ALL');

  const statusMap = useMemo(() => {
    const map = new Map<string, CaseStatus>();
    (statuses ?? []).forEach((row) => {
      map.set(row.case_id, row.status);
    });
    return map;
  }, [statuses]);

  const caseMap = useMemo(() => {
    const map = new Map<string, (typeof riskCases)[number]>();
    riskCases.forEach((riskCase) => {
      map.set(riskCase.case_id, riskCase);
    });
    return map;
  }, [riskCases]);

  const entriesWithStatus = (entries ?? []).map((entry) => ({
    ...entry,
    case_status: statusMap.get(entry.case_id) ?? 'NOT_STARTED'
  }));

  const statusOnlyEntries = (statuses ?? []).flatMap((statusRow) => {
    if (entriesWithStatus.some((entry) => entry.case_id === statusRow.case_id)) {
      return [];
    }
    const riskCase = caseMap.get(statusRow.case_id);
    if (!riskCase) {
      return [];
    }
    return [
      {
        audit_id: `AUTO-${statusRow.case_id}`,
        case_id: statusRow.case_id,
        player_id: statusRow.player_id,
        analyst_id: statusRow.analyst_id,
        action: 'Case Review Started',
        risk_category: riskCase.risk_category,
        state_jurisdiction: riskCase.state_jurisdiction,
        timestamp: statusRow.updated_at,
        notes: 'Audit trail entry created after Start Case Review.',
        case_status: statusRow.status
      }
    ];
  });

  const mergedEntries = [...entriesWithStatus, ...statusOnlyEntries];

  const filteredEntries =
    statusFilter === 'ALL'
      ? mergedEntries
      : mergedEntries.filter((entry) => entry.case_status === statusFilter);

  const selectedEntry =
    mergedEntries.find((entry) => entry.player_id === activeAuditPlayerId) ?? null;

  if (!entries) {
    return (
      <div className="glass-panel rounded-2xl p-6 text-slate-400">
        Loading audit trail...
      </div>
    );
  }

  if (selectedEntry && selectedEntry.risk_category !== 'LOW') {
    return (
      <Suspense
        fallback={
          <div className="glass-panel rounded-2xl p-6 text-slate-400">
            Loading case file...
          </div>
        }
      >
        <CaseFilePage
          entry={selectedEntry}
          status={selectedEntry.case_status}
          onBack={() => setActiveAuditPlayerId(null)}
        />
      </Suspense>
    );
  }

  return (
    <div className="grid gap-4">
      <div className="flex flex-wrap items-center gap-2">
        {(['ALL', 'NOT_STARTED', 'IN_PROGRESS', 'SUBMITTED'] as const).map((value) => (
          <button
            key={value}
            type="button"
            onClick={() => setStatusFilter(value)}
            className={`rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-wide ${
              statusFilter === value
                ? 'border-[#53B848] bg-[#53B848] text-black'
                : 'border-slate-700 text-slate-300'
            }`}
          >
            {value === 'ALL' ? 'All' : value.replace('_', ' ')}
          </button>
        ))}
      </div>
      <AuditTrailTable
        entries={filteredEntries}
        activePlayerId={activeAuditPlayerId}
        onSelect={(entry) => setActiveAuditPlayerId(entry.player_id)}
      />
    </div>
  );
};

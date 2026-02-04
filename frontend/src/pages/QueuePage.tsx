import { useEffect, useMemo } from 'react';
import { QueueFilters } from '../components/QueueFilters';
import { RiskCaseCard } from '../components/RiskCaseCard';
import { CaseDetailPanel } from '../components/CaseDetailPanel';
import { useCaseDetail, useRiskCases } from '../hooks/useRiskCases';
import { useAuditTrail } from '../hooks/useAuditTrail';
import { useCaseStatuses } from '../hooks/useCaseTimeline';
import { useQueueStore } from '../state/useQueueStore';

export const QueuePage = () => {
  const { data: cases = [] } = useRiskCases();
  const { data: statuses = [] } = useCaseStatuses();
  const { data: auditEntries = [] } = useAuditTrail();
  const selectedCaseId = useQueueStore((state) => state.selectedCaseId);
  const setSelectedCaseId = useQueueStore((state) => state.setSelectedCaseId);
  const searchTerm = useQueueStore((state) => state.searchTerm.toLowerCase());
  const activeCategories = useQueueStore((state) => state.activeCategories);

  const statusMap = useMemo(() => {
    const map = new Map<string, string>();
    statuses.forEach((row) => {
      map.set(row.case_id, row.status);
    });
    return map;
  }, [statuses]);

  const auditCaseIds = useMemo(() => {
    const ids = new Set<string>();
    auditEntries.forEach((entry) => ids.add(entry.case_id));
    return ids;
  }, [auditEntries]);

  const filteredCases = useMemo(
    () =>
      cases.filter((riskCase) => {
        if (statusMap.has(riskCase.case_id)) {
          return false;
        }
        if (auditCaseIds.has(riskCase.case_id)) {
          return false;
        }
        const matchesSearch =
          riskCase.player_id.toLowerCase().includes(searchTerm) ||
          riskCase.case_id.toLowerCase().includes(searchTerm);
        const matchesCategory = activeCategories.includes(riskCase.risk_category);
        return matchesSearch && matchesCategory;
      }),
    [cases, searchTerm, activeCategories, statusMap, auditCaseIds]
  );

  useEffect(() => {
    if (filteredCases.length === 0) {
      if (selectedCaseId) {
        setSelectedCaseId(null);
      }
      return;
    }
    const stillValid = filteredCases.some((riskCase) => riskCase.case_id === selectedCaseId);
    if (!selectedCaseId || !stillValid) {
      setSelectedCaseId(filteredCases[0].case_id);
    }
  }, [filteredCases, selectedCaseId, setSelectedCaseId]);

  const { data: detail } = useCaseDetail(selectedCaseId);

  return (
    <div className="grid gap-6 lg:grid-cols-[1.1fr_1.4fr]">
      <div className="flex flex-col gap-4">
        <QueueFilters />
        <div className="grid gap-3">
          {filteredCases.map((riskCase) => (
            <RiskCaseCard
              key={riskCase.case_id}
              riskCase={riskCase}
              isSelected={riskCase.case_id === selectedCaseId}
              onSelect={setSelectedCaseId}
            />
          ))}
          {filteredCases.length === 0 ? (
            <div className="glass-panel rounded-2xl p-6 text-center text-slate-400">
              No cases match the current filters.
            </div>
          ) : null}
        </div>
      </div>
      <CaseDetailPanel detail={detail ?? null} />
    </div>
  );
};

import { useEffect, useMemo } from 'react';
import { QueueFilters } from '../components/QueueFilters';
import { RiskCaseCard } from '../components/RiskCaseCard';
import { CaseDetailPanel } from '../components/CaseDetailPanel';
import { useCaseDetail, useRiskCases } from '../hooks/useRiskCases';
import { useQueueStore } from '../state/useQueueStore';

export const QueuePage = () => {
  const { data: cases = [] } = useRiskCases();
  const selectedCaseId = useQueueStore((state) => state.selectedCaseId);
  const setSelectedCaseId = useQueueStore((state) => state.setSelectedCaseId);
  const searchTerm = useQueueStore((state) => state.searchTerm.toLowerCase());
  const activeCategories = useQueueStore((state) => state.activeCategories);

  const filteredCases = useMemo(
    () =>
      cases.filter((riskCase) => {
        const matchesSearch =
          riskCase.player_id.toLowerCase().includes(searchTerm) ||
          riskCase.case_id.toLowerCase().includes(searchTerm);
        const matchesCategory = activeCategories.includes(riskCase.risk_category);
        return matchesSearch && matchesCategory;
      }),
    [cases, searchTerm, activeCategories]
  );

  useEffect(() => {
    if (!selectedCaseId && filteredCases.length > 0) {
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
            <div className="glass-panel rounded-2xl p-6 text-center text-slate-500">
              No cases match the current filters.
            </div>
          ) : null}
        </div>
      </div>
      <CaseDetailPanel detail={detail ?? null} />
    </div>
  );
};

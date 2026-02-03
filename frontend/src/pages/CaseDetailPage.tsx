import { CaseDetailPanel } from '../components/CaseDetailPanel';
import { useCaseDetail } from '../hooks/useRiskCases';
import { useQueueStore } from '../state/useQueueStore';

export const CaseDetailPage = () => {
  const selectedCaseId = useQueueStore((state) => state.selectedCaseId);
  const { data: detail } = useCaseDetail(selectedCaseId);

  return (
    <div className="grid gap-6">
      <CaseDetailPanel detail={detail ?? null} />
    </div>
  );
};

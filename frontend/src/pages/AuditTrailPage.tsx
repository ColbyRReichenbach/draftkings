import { AuditTrailTable } from '../components/AuditTrailTable';
import { useAuditTrail } from '../hooks/useAuditTrail';

export const AuditTrailPage = () => {
  const { data: entries } = useAuditTrail();

  if (!entries) {
    return (
      <div className="glass-panel rounded-2xl p-6 text-slate-500">
        Loading audit trail...
      </div>
    );
  }

  return <AuditTrailTable entries={entries} />;
};

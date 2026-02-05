import { AuditEntry, CaseStatus } from '../types/risk';

interface AuditTrailTableProps {
  entries: (AuditEntry & { case_status?: CaseStatus })[];
  activePlayerId?: string | null;
  onSelect?: (entry: AuditEntry) => void;
}

const STATUS_STYLES: Record<CaseStatus, { label: string; className: string; icon: string }> = {
  NOT_STARTED: {
    label: 'Not Started',
    className: 'bg-slate-800 text-slate-300 border-slate-700',
    icon: '○'
  },
  IN_PROGRESS: {
    label: 'In Progress',
    className: 'bg-[#F3701B] text-black border-transparent',
    icon: '●'
  },
  SUBMITTED: {
    label: 'Submitted',
    className: 'bg-[#53B848] text-black border-transparent',
    icon: '✓'
  }
};

export const AuditTrailTable = ({ entries, activePlayerId, onSelect }: AuditTrailTableProps) => (
  <div className="glass-panel panel-sheen rounded-2xl p-6">
    <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">Recent Actions</p>
    <div className="mt-4 overflow-x-auto">
      <table className="w-full text-left text-sm">
        <thead className="text-xs uppercase text-slate-400">
          <tr>
            <th className="py-2">Player</th>
            <th className="py-2">Action</th>
            <th className="py-2">Analyst</th>
            <th className="py-2">State</th>
            <th className="py-2">Time</th>
            <th className="py-2">Status</th>
            <th className="py-2 text-right">Open</th>
          </tr>
        </thead>
        <tbody className="text-slate-300">
          {entries.map((entry) => {
            const status = STATUS_STYLES[entry.case_status ?? 'NOT_STARTED'];
            return (
              <tr
                key={entry.audit_id}
                className={`border-t border-slate-800 ${
                  entry.risk_category === 'LOW'
                    ? 'opacity-60'
                    : 'cursor-pointer transition hover:bg-white/5'
                } ${activePlayerId === entry.player_id ? 'bg-white/5' : ''}`}
                onClick={() => {
                  if (entry.risk_category === 'LOW') {
                    return;
                  }
                  onSelect?.(entry);
                }}
              >
                <td className="py-3 font-semibold text-slate-100">{entry.player_id}</td>
                <td className="py-3">
                  <p className="text-slate-100">{entry.action}</p>
                  <p className="text-xs text-slate-400">{entry.notes}</p>
                  {entry.nudge_status ? (
                    <p className="text-xs text-slate-400">
                      Nudge: {entry.nudge_status}
                      {entry.nudge_excerpt ? ` — ${entry.nudge_excerpt}` : ''}
                    </p>
                  ) : null}
                  <p className="text-xs text-slate-400">Signed by {entry.analyst_id}</p>
                </td>
                <td className="py-3">{entry.analyst_id}</td>
                <td className="py-3">{entry.state_jurisdiction}</td>
                <td className="py-3 text-xs text-slate-400">
                  {new Date(entry.timestamp).toLocaleString()}
                </td>
                <td className="py-3">
                  <span
                    className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-semibold ${status.className}`}
                  >
                    <span aria-hidden="true">{status.icon}</span>
                    {status.label}
                  </span>
                </td>
                <td className="py-3 text-right">
                  {entry.risk_category !== 'LOW' ? (
                    <button
                      type="button"
                      onClick={(event) => {
                        event.stopPropagation();
                        onSelect?.(entry);
                      }}
                      className="hover-lift inline-flex items-center gap-2 rounded-full border border-slate-700 bg-slate-900/70 px-3 py-1 text-xs font-semibold text-slate-200"
                    >
                      View Case File
                      <span aria-hidden="true">→</span>
                    </button>
                  ) : (
                    <span className="text-xs text-slate-500">N/A</span>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  </div>
);

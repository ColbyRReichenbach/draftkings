import { AuditEntry } from '../types/risk';

interface AuditTrailTableProps {
  entries: AuditEntry[];
}

export const AuditTrailTable = ({ entries }: AuditTrailTableProps) => (
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
          </tr>
        </thead>
        <tbody className="text-slate-300">
          {entries.map((entry) => (
            <tr key={entry.audit_id} className="border-t border-slate-800">
              <td className="py-3 font-semibold text-slate-100">{entry.player_id}</td>
              <td className="py-3">
                <p className="text-slate-100">{entry.action}</p>
                <p className="text-xs text-slate-400">{entry.notes}</p>
                <p className="text-xs text-slate-400">Signed by {entry.analyst_id}</p>
              </td>
              <td className="py-3">{entry.analyst_id}</td>
              <td className="py-3">{entry.state_jurisdiction}</td>
              <td className="py-3 text-xs text-slate-400">
                {new Date(entry.timestamp).toLocaleString()}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  </div>
);

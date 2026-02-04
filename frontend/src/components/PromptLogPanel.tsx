import { PromptLogEntry } from '../types/risk';

interface PromptLogPanelProps {
  logs: PromptLogEntry[];
}

export const PromptLogPanel = ({ logs }: PromptLogPanelProps) => (
  <div className="panel-sheen rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
    <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
      LLM Transparency Log
    </p>
    {logs.length === 0 ? (
      <p className="mt-3 text-sm text-slate-400">No AI drafts logged yet.</p>
    ) : (
      <div className="mt-3 space-y-4">
        {logs.map((log, index) => (
          <div key={`${log.created_at}-${index}`} className="rounded-xl bg-slate-950/60 p-3">
            <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-slate-400">
              <span>Analyst: {log.analyst_id}</span>
              <span>{new Date(log.created_at).toLocaleString()}</span>
            </div>
            <details className="mt-2">
              <summary className="cursor-pointer text-xs font-semibold text-slate-300">
                Prompt Used
              </summary>
              <p className="mt-2 whitespace-pre-wrap text-xs text-slate-400">
                {log.prompt_text}
              </p>
            </details>
            <details className="mt-2">
              <summary className="cursor-pointer text-xs font-semibold text-slate-300">
                LLM Output
              </summary>
              <p className="mt-2 whitespace-pre-wrap text-xs text-slate-400">
                {log.response_text}
              </p>
            </details>
          </div>
        ))}
      </div>
    )}
  </div>
);

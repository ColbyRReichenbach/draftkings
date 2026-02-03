import { NudgeValidationResult } from '../types/risk';

interface NudgePreviewProps {
  nudgeText: string;
  validationResult?: NudgeValidationResult | null;
  isValidating: boolean;
}

export const NudgePreview = ({ nudgeText, validationResult, isValidating }: NudgePreviewProps) => (
  <div className="panel-sheen rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
    <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">Draft Nudge</p>
    <p className="mt-2 text-sm text-slate-200">{nudgeText}</p>
    <div className="mt-4 flex flex-wrap items-center gap-2 text-xs">
      {isValidating ? (
        <span className="rounded-full bg-slate-800 px-2 py-1 text-slate-200">Validating...</span>
      ) : validationResult ? (
        validationResult.is_valid ? (
          <span className="rounded-full bg-emerald-400/20 px-2 py-1 text-emerald-200">
            Compliance: Pass
          </span>
        ) : (
          <span className="rounded-full bg-red-500/20 px-2 py-1 text-red-200">Compliance: Review</span>
        )
      ) : (
        <span className="rounded-full bg-amber-400/20 px-2 py-1 text-amber-200">
          Compliance: Pending Review
        </span>
      )}
      <span className="text-slate-400">RG link required</span>
    </div>
    {validationResult && !validationResult.is_valid ? (
      <ul className="mt-3 list-disc space-y-1 pl-5 text-xs text-red-300">
        {validationResult.violations.map((violation) => (
          <li key={violation}>{violation}</li>
        ))}
      </ul>
    ) : null}
  </div>
);

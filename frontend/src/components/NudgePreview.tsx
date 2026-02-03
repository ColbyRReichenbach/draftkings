import { NudgeValidationResult } from '../types/risk';

interface NudgePreviewProps {
  nudgeText: string;
  validationResult?: NudgeValidationResult | null;
  isValidating: boolean;
}

export const NudgePreview = ({ nudgeText, validationResult, isValidating }: NudgePreviewProps) => (
  <div className="rounded-2xl border border-slate-200 bg-white p-4">
    <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">Draft Nudge</p>
    <p className="mt-2 text-sm text-slate-700">{nudgeText}</p>
    <div className="mt-4 flex flex-wrap items-center gap-2 text-xs">
      {isValidating ? (
        <span className="rounded-full bg-slate-100 px-2 py-1 text-slate-600">Validating...</span>
      ) : validationResult ? (
        validationResult.is_valid ? (
          <span className="rounded-full bg-emerald-100 px-2 py-1 text-emerald-700">
            Compliance: Pass
          </span>
        ) : (
          <span className="rounded-full bg-red-100 px-2 py-1 text-red-700">Compliance: Review</span>
        )
      ) : (
        <span className="rounded-full bg-amber-100 px-2 py-1 text-amber-700">
          Compliance: Pending Review
        </span>
      )}
      <span className="text-slate-500">RG link required</span>
    </div>
    {validationResult && !validationResult.is_valid ? (
      <ul className="mt-3 list-disc space-y-1 pl-5 text-xs text-red-600">
        {validationResult.violations.map((violation) => (
          <li key={violation}>{violation}</li>
        ))}
      </ul>
    ) : null}
  </div>
);

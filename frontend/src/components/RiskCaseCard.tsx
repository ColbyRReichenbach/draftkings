import { RiskCase } from '../types/risk';
import { RISK_STYLES } from '../styles/theme';

interface RiskCaseCardProps {
  riskCase: RiskCase;
  isSelected: boolean;
  onSelect: (caseId: string) => void;
}

export const RiskCaseCard = ({ riskCase, isSelected, onSelect }: RiskCaseCardProps) => {
  const style = RISK_STYLES[riskCase.risk_category];

  return (
    <button
      type="button"
      onClick={() => onSelect(riskCase.case_id)}
      className={`w-full rounded-2xl border-l-4 px-5 py-4 text-left transition-all ${style.bg} ${style.border} ${
        isSelected ? 'shadow-lg ring-2 ring-[#53B848]/50' : 'hover:shadow-md'
      }`}
      aria-pressed={isSelected}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className={`text-xs font-semibold uppercase tracking-wide ${style.text}`}>
            {riskCase.risk_category} Risk
          </p>
          <h3 className="mt-1 font-display text-lg text-slate-900">{riskCase.player_id}</h3>
          <p className="text-sm text-slate-500">Case {riskCase.case_id}</p>
        </div>
        <div className={`rounded-full px-3 py-1 text-xs font-semibold ${style.badge}`}>
          {(riskCase.composite_risk_score * 100).toFixed(0)}%
        </div>
      </div>
      <div className="mt-3 flex flex-wrap gap-2">
        {riskCase.key_evidence.map((item) => (
          <span
            key={item}
            className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs text-slate-600"
          >
            {item}
          </span>
        ))}
      </div>
    </button>
  );
};

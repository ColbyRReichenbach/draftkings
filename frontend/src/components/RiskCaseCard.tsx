import { RiskCase } from '../types/risk';
import { RISK_STYLES } from '../styles/theme';

interface RiskCaseCardProps {
  riskCase: RiskCase;
  isSelected: boolean;
  onSelect: (caseId: string) => void;
}

export const RiskCaseCard = ({ riskCase, isSelected, onSelect }: RiskCaseCardProps) => {
  const style = RISK_STYLES[riskCase.risk_category];
  const riskScore = (riskCase.composite_risk_score * 100).toFixed(0);

  return (
    <div
      onClick={() => onSelect(riskCase.case_id)}
      className={`group relative flex w-full cursor-pointer items-center justify-between border-b border-dk-border bg-dk-surface/50 p-4 transition-all hover:bg-dk-surface hover-tech ${isSelected ? 'bg-dk-surface border-l-4 ' + style.border : 'border-l-4 border-l-transparent'
        }`}
    >
      {/* Selection Indicator Overlay */}
      {isSelected && (
        <div className={`absolute inset-y-0 left-0 w-1 ${style.indicator}`} />
      )}

      <div className="flex items-center gap-6">
        {/* Risk Indicator / Category */}
        <div className="w-24 shrink-0">
          <span className={`inline-block rounded px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider ${style.badge}`}>
            {riskCase.risk_category}
          </span>
        </div>

        {/* Player & Case Info */}
        <div className="flex flex-col">
          <h3 className="font-mono text-base font-medium text-slate-200 group-hover:text-white">
            {riskCase.player_id}
          </h3>
          <span className="font-mono text-xs text-slate-500 group-hover:text-slate-400">
            ID: {riskCase.case_id}
          </span>
        </div>

        {/* Evidence Tags - now more technical/minimal */}
        <div className="hidden items-center gap-2 lg:flex">
          {riskCase.key_evidence.slice(0, 3).map((item) => (
            <span
              key={item}
              className="rounded-sm border border-slate-800 bg-black/40 px-1.5 py-0.5 text-[10px] font-medium uppercase text-slate-400"
            >
              {item}
            </span>
          ))}
          {riskCase.key_evidence.length > 3 && (
            <span className="text-[10px] text-slate-600">+{riskCase.key_evidence.length - 3}</span>
          )}
        </div>
      </div>

      {/* Right Side: Risk Score */}
      <div className="flex items-center gap-6">
        <div className="text-right">
          <div className="flex items-baseline justify-end gap-1">
            <span className={`font-display text-2xl font-bold ${style.text}`}>
              {riskScore}
            </span>
            <span className="text-xs font-medium text-slate-500">%</span>
          </div>
          <p className="text-[10px] uppercase tracking-wider text-slate-600">Risk Score</p>
        </div>

        {/* Chevron/Action Icon placeholder */}
        <div className="text-slate-600 group-hover:text-dk-green transition-colors">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="9 18 15 12 9 6" />
          </svg>
        </div>
      </div>
    </div>
  );
};

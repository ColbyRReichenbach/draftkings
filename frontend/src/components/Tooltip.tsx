import { ReactNode } from 'react';

interface TooltipProps {
  label: string;
  children: ReactNode;
  className?: string;
}

export const Tooltip = ({ label, children, className }: TooltipProps) => (
  <div className={`group relative ${className ?? 'inline-flex items-center'}`}>
    {children}
    <span className="pointer-events-none absolute left-1/2 top-full z-[9999] mt-2 w-64 -translate-x-1/2 rounded-xl border border-slate-700 bg-slate-950/95 p-2 text-[11px] leading-relaxed text-slate-200 opacity-0 shadow-xl transition-opacity duration-150 group-hover:opacity-100">
      {label}
    </span>
  </div>
);

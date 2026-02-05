import { ReactNode, useMemo, useRef, useState } from 'react';
import { createPortal } from 'react-dom';

interface InfoBadgeProps {
  label: string;
  className?: string;
  children: ReactNode;
}

type TooltipPlacement = 'top' | 'bottom';

export const InfoBadge = ({ label, className, children }: InfoBadgeProps) => {
  const triggerRef = useRef<HTMLSpanElement | null>(null);
  const [open, setOpen] = useState(false);
  const [coords, setCoords] = useState({ left: 0, top: 0 });

  const tooltip = useMemo(() => {
    if (!open) return null;
    const body = typeof document !== 'undefined' ? document.body : null;
    if (!body) return null;

    return createPortal(
      <span
        className={`pointer-events-none fixed z-[9999] w-64 rounded-xl border border-slate-700 bg-slate-950/95 p-2 text-[11px] leading-relaxed text-slate-200 shadow-xl transition-opacity duration-150 ${
          open ? 'opacity-100' : 'opacity-0'
        }`}
        style={{
          left: coords.left,
          top: coords.top,
        }}
      >
        {label}
      </span>,
      body,
    );
  }, [coords.left, coords.top, label, open]);

  const updatePosition = () => {
    const node = triggerRef.current;
    if (!node) return;
    const rect = node.getBoundingClientRect();
    const preferred: TooltipPlacement = window.innerHeight - rect.bottom < 180 ? 'top' : 'bottom';
    const tooltipWidth = 256;
    const gutter = 12;
    const left = Math.min(
      Math.max(rect.right - tooltipWidth, gutter),
      window.innerWidth - tooltipWidth - gutter,
    );
    const top =
      preferred === 'bottom' ? rect.bottom + 8 : Math.max(rect.top - 8 - 90, gutter);
    setCoords({ left, top });
  };

  return (
    <div className={`relative ${className ?? ''}`}>
      {children}
      <span
        ref={triggerRef}
        className="absolute right-2 top-2 inline-flex h-5 w-5 items-center justify-center rounded-full border border-slate-700 bg-slate-950 text-[11px] font-semibold text-slate-300"
        onMouseEnter={() => {
          updatePosition();
          setOpen(true);
        }}
        onMouseLeave={() => setOpen(false)}
      >
        i
      </span>
      {tooltip}
    </div>
  );
};

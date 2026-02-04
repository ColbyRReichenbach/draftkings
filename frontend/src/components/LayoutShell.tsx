import { ReactNode } from 'react';
import { TabNav } from './TabNav';

interface LayoutShellProps {
  title: string;
  subtitle: string;
  children: ReactNode;
}

export const LayoutShell = ({ title, subtitle, children }: LayoutShellProps) => (
  <div className="relative min-h-screen overflow-x-hidden overflow-y-visible px-6 py-10">
    <div className="pointer-events-none absolute inset-0">
      <div className="absolute -left-24 top-20 h-72 w-72 rounded-full bg-[#53B848]/20 blur-[120px]" />
      <div className="absolute right-0 top-0 h-80 w-80 rounded-full bg-[#F3701B]/15 blur-[140px]" />
      <div className="absolute bottom-0 left-1/3 h-64 w-64 rounded-full bg-slate-500/10 blur-[120px]" />
    </div>
    <div className="relative mx-auto flex w-full max-w-6xl flex-col gap-6">
      <header className="glass-panel panel-sheen animate-fade-in rounded-3xl p-8">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-[#53B848] text-sm font-bold text-black ring-soft">
                DK
              </div>
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">
                  DK Sentinel
                </p>
                <p className="text-sm text-slate-400">Responsible Gaming Command Center</p>
              </div>
            </div>
            <h1 className="mt-4 font-display text-3xl font-semibold text-slate-100 sm:text-4xl">
              {title}
            </h1>
            <p className="mt-2 max-w-xl text-base text-slate-300">{subtitle}</p>
          </div>
          <div className="flex items-center gap-3 rounded-2xl border border-slate-800 bg-slate-900/70 px-4 py-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[#53B848] text-black">
              RG
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                Analyst
              </p>
              <p className="text-sm font-medium text-slate-100">Colby Reichenbach</p>
            </div>
          </div>
        </div>
        <div className="mt-6 border-t border-slate-800 pt-4">
          <TabNav />
        </div>
      </header>

      <main className="grid gap-6 animate-fade-up">{children}</main>
    </div>
  </div>
);

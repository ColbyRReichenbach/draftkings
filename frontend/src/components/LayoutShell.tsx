import { ReactNode } from 'react';
import { TabNav } from './TabNav';

interface LayoutShellProps {
  title: string;
  subtitle: string;
  children: ReactNode;
}

export const LayoutShell = ({ title, subtitle, children }: LayoutShellProps) => (
  <div className="min-h-screen px-6 py-10">
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-6">
      <header className="glass-panel rounded-3xl p-8">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-slate-400">
              DraftKings RG Analytics
            </p>
            <h1 className="font-display text-3xl font-semibold text-slate-900 sm:text-4xl">
              {title}
            </h1>
            <p className="mt-2 max-w-xl text-base text-slate-600">{subtitle}</p>
          </div>
          <div className="flex items-center gap-3 rounded-2xl border border-slate-100 bg-white px-4 py-3 shadow-sm">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[#53B848] text-white">
              RG
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                Analyst
              </p>
              <p className="text-sm font-medium text-slate-800">Colby Reichenbach</p>
            </div>
          </div>
        </div>
        <div className="mt-6 border-t border-slate-100 pt-4">
          <TabNav />
        </div>
      </header>

      <main className="grid gap-6">{children}</main>
    </div>
  </div>
);

import { ReactNode } from 'react';
import { SidebarNav } from './SidebarNav';

interface LayoutShellProps {
  title: string;
  subtitle: string;
  children: ReactNode;
}

export const LayoutShell = ({ title, subtitle, children }: LayoutShellProps) => (
  <div className="flex min-h-screen w-full bg-dk-black text-slate-200 font-body">
    {/* Sidebar Navigation */}
    <SidebarNav />

    {/* Main Content Area */}
    <main className="relative flex-1 flex flex-col min-w-0 ml-0 md:ml-64 transition-all duration-300">
      {/* Background Grid Pattern */}
      <div className="absolute inset-0 bg-grid-pattern opacity-[0.03] pointer-events-none z-0" />

      {/* Top Header / Context Bar */}
      <header className="relative z-10 flex h-20 items-center justify-between border-b border-dk-border bg-dk-black/50 px-8 backdrop-blur-sm">
        <div>
          <h1 className="font-display text-2xl font-bold uppercase tracking-tight text-white">
            {title}
          </h1>
          <p className="hidden text-sm text-slate-400 sm:block">
            {subtitle}
          </p>
        </div>

        {/* Right side actions or status indicators could go here */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 rounded bg-dk-surface px-3 py-1.5 border border-dk-border">
            <div className="h-2 w-2 rounded-full bg-dk-green animate-pulse" />
            <span className="text-xs font-mono font-medium text-slate-300">SYSTEM NORMAL</span>
          </div>
        </div>
      </header>

      {/* Content Scroll Area */}
      <div className="relative z-10 flex-1 overflow-y-auto p-8">
        <div className="animate-fade-in max-w-7xl mx-auto">
          {children}
        </div>
      </div>
    </main>
  </div>
);

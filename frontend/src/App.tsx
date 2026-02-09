import { useCallback, useEffect, useMemo, useState } from 'react';
import { LayoutShell } from './components/LayoutShell';
import { AuditTrailPage } from './pages/AuditTrailPage';
import { AnalyticsPage } from './pages/AnalyticsPage';
import { CaseDetailPage } from './pages/CaseDetailPage';
import { QueuePage } from './pages/QueuePage';
import { useUiStore } from './state/useUiStore';

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ??
  import.meta.env.VITE_API_URL ??
  'http://localhost:8000';

type BackendStatus = 'checking' | 'warming' | 'ready';

const BackendWarmupOverlay = ({
  status,
  retryIn,
  onRetry,
  showManualWake
}: {
  status: BackendStatus;
  retryIn: number;
  onRetry: () => void;
  showManualWake: boolean;
}) => {
  if (status === 'ready') {
    return null;
  }

  const handleManualWake = () => {
    window.open(API_BASE_URL, '_blank', 'noopener,noreferrer');
    onRetry();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 px-6">
      <div className="glass-panel panel-sheen w-full max-w-lg rounded-3xl border border-slate-800 bg-slate-950/80 p-8 text-center shadow-2xl">
        <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-[#53B848] text-lg font-semibold text-black ring-soft">
          DK
        </div>
        <h2 className="font-display text-2xl font-semibold text-slate-100">
          Warming backend service
        </h2>
        <p className="mt-3 text-sm text-slate-300">
          This demo runs on a free Render tier, so the API can sleep when idle.
          We&apos;ll auto‑retry every few seconds until it&apos;s ready.
        </p>
        <div className="mt-6 flex flex-col items-center gap-2 text-sm text-slate-400">
          <span className="inline-flex items-center gap-2">
            <span className="h-2 w-2 animate-pulse rounded-full bg-[#53B848]" />
            Next retry in {retryIn}s
          </span>
          <button
            type="button"
            onClick={onRetry}
            className="mt-4 inline-flex items-center justify-center rounded-full bg-[#53B848] px-5 py-2 text-sm font-semibold text-black transition hover:brightness-110"
          >
            Retry now
          </button>
          {showManualWake ? (
            <button
              type="button"
              onClick={handleManualWake}
              className="text-xs text-slate-300 underline decoration-slate-600 transition hover:text-slate-100"
            >
              Wake backend in new tab
            </button>
          ) : null}
        </div>
      </div>
    </div>
  );
};

const App = () => {
  const activeTab = useUiStore((state) => state.activeTab);
  const [backendStatus, setBackendStatus] = useState<BackendStatus>('checking');
  const [retryIn, setRetryIn] = useState(0);
  const [retryCount, setRetryCount] = useState(0);

  const checkBackend = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/health`, {
        cache: 'no-store'
      });
      if (response.ok) {
        setBackendStatus('ready');
        setRetryIn(0);
        setRetryCount(0);
        return true;
      }
    } catch {
      // ignore network errors; we retry below
    }
    setBackendStatus('warming');
    setRetryIn(8);
    setRetryCount((count) => count + 1);
    return false;
  }, []);

  useEffect(() => {
    let retryTimeout: number | undefined;
    let countdownInterval: number | undefined;

    const scheduleRetry = async () => {
      const isReady = await checkBackend();
      if (isReady) {
        return;
      }

      let remaining = 8;
      countdownInterval = window.setInterval(() => {
        remaining = Math.max(0, remaining - 1);
        setRetryIn(remaining);
      }, 1000);

      retryTimeout = window.setTimeout(async () => {
        if (countdownInterval) {
          window.clearInterval(countdownInterval);
        }
        await scheduleRetry();
      }, 8000);
    };

    scheduleRetry();

    return () => {
      if (retryTimeout) {
        window.clearTimeout(retryTimeout);
      }
      if (countdownInterval) {
        window.clearInterval(countdownInterval);
      }
    };
  }, [checkBackend]);

  const renderTab = () => {
    switch (activeTab) {
      case 'queue':
        return <QueuePage />;
      case 'case':
        return <CaseDetailPage />;
      case 'analytics':
        return <AnalyticsPage />;
      case 'audit':
        return <AuditTrailPage />;
      default:
        return <QueuePage />;
    }
  };

  const isBackendReady = backendStatus === 'ready';
  const renderedTab = useMemo(() => {
    if (!isBackendReady) {
      return (
        <div className="glass-panel rounded-3xl border border-slate-800 bg-slate-950/60 p-6 text-sm text-slate-300">
          Waiting for the backend to finish waking up…
        </div>
      );
    }
    return renderTab();
  }, [isBackendReady, activeTab]);

  return (
    <LayoutShell
      title="Responsible Gaming Command Center"
      subtitle="Prioritize high-risk cases, review evidence, and document interventions in one unified workflow."
    >
      {renderedTab}
      <BackendWarmupOverlay
        status={backendStatus}
        retryIn={retryIn}
        onRetry={checkBackend}
        showManualWake={retryCount >= 1}
      />
    </LayoutShell>
  );
};

export default App;

import { LayoutShell } from './components/LayoutShell';
import { AuditTrailPage } from './pages/AuditTrailPage';
import { AnalyticsPage } from './pages/AnalyticsPage';
import { CaseDetailPage } from './pages/CaseDetailPage';
import { QueuePage } from './pages/QueuePage';
import { useUiStore } from './state/useUiStore';

const App = () => {
  const activeTab = useUiStore((state) => state.activeTab);

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

  return (
    <LayoutShell
      title="Responsible Gaming Command Center"
      subtitle="Prioritize high-risk cases, review evidence, and document interventions in one unified workflow."
    >
      {renderTab()}
    </LayoutShell>
  );
};

export default App;

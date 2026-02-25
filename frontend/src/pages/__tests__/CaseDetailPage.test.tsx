import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { CaseDetailPage } from '../CaseDetailPage';
import { useQueueStore } from '../../state/useQueueStore';
import { useUiStore } from '../../state/useUiStore';

const renderWithClient = (ui: React.ReactElement) => {
  const client = new QueryClient();
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
};

describe('CaseDetailPage', () => {
  beforeEach(() => {
    useQueueStore.setState({ selectedCaseId: null });
    useUiStore.setState({ activeTab: 'queue', activeAuditPlayerId: null });
  });

  it('renders selected case detail', async () => {
    useQueueStore.setState({ selectedCaseId: 'CASE-1001' });
    renderWithClient(<CaseDetailPage />);
    expect(await screen.findByText('Case Detail')).toBeInTheDocument();
    expect(await screen.findByText('PLR_1024_MA')).toBeInTheDocument();
  });

  it('renders placeholder when no case is selected', () => {
    renderWithClient(<CaseDetailPage />);
    expect(screen.getByText('Select a case from the queue to view details.')).toBeInTheDocument();
  });

  it('moves analyst to audit tab when Start Case Review is clicked', async () => {
    useQueueStore.setState({ selectedCaseId: 'CASE-1001' });
    renderWithClient(<CaseDetailPage />);

    const button = await screen.findByRole('button', { name: 'Start Case Review' });
    fireEvent.click(button);

    await waitFor(() => {
      expect(useUiStore.getState().activeTab).toBe('audit');
      expect(useUiStore.getState().activeAuditPlayerId).toBe('PLR_1024_MA');
    });
  });
});

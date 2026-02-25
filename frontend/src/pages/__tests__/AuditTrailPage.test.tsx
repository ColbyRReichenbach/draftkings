import { fireEvent, render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuditTrailPage } from '../AuditTrailPage';
import { useUiStore } from '../../state/useUiStore';

const renderWithClient = (ui: React.ReactElement) => {
  const client = new QueryClient();
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
};

describe('AuditTrailPage', () => {
  beforeEach(() => {
    useUiStore.setState({ activeAuditPlayerId: null });
  });

  it('renders audit trail heading', async () => {
    renderWithClient(<AuditTrailPage />);
    expect(await screen.findByText('Recent Actions')).toBeInTheDocument();
  });

  it('opens case file on row click', async () => {
    renderWithClient(<AuditTrailPage />);
    const row = await screen.findByText('PLR_1024_MA');
    fireEvent.click(row);
    expect(await screen.findByText('Case File')).toBeInTheDocument();
    expect(screen.getByText('Export Analyst Report (PDF)')).toBeInTheDocument();
    expect(screen.getByText('Log Result')).toBeDisabled();
  });

  it('shows explicit view case button', async () => {
    renderWithClient(<AuditTrailPage />);
    const buttons = await screen.findAllByText('View Case File');
    expect(buttons.length).toBeGreaterThan(0);
  });
});

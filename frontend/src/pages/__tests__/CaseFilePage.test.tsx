import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { CaseFilePage } from '../CaseFilePage';
import { AuditEntry, CaseStatus } from '../../types/risk';

const renderWithClient = (ui: React.ReactElement) => {
  const client = new QueryClient();
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
};

describe('CaseFilePage', () => {
  it('renders SQL preview and output sections', async () => {
    const entry: AuditEntry = {
      audit_id: 'AUD-1',
      case_id: 'CASE-PLR_1024_MA',
      player_id: 'PLR_1024_MA',
      analyst_id: 'Colby Reichenbach',
      action: 'Review pending',
      risk_category: 'CRITICAL',
      state_jurisdiction: 'MA',
      timestamp: '2026-02-04T00:00:00Z',
      notes: 'No analyst notes yet.'
    };

    renderWithClient(
      <CaseFilePage entry={entry} status={'IN_PROGRESS' as CaseStatus} onBack={() => {}} />
    );

    expect(await screen.findByText('SQL Output (Read-only)')).toBeInTheDocument();
    expect(await screen.findByRole('button', { name: 'Run Query' })).toBeInTheDocument();
  });
});

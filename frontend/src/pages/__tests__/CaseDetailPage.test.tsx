import React from 'react';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { CaseDetailPage } from '../CaseDetailPage';
import { useQueueStore } from '../../state/useQueueStore';

const renderWithClient = (ui: React.ReactElement) => {
  const client = new QueryClient();
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
};

describe('CaseDetailPage', () => {
  it('renders selected case detail', async () => {
    useQueueStore.setState({ selectedCaseId: 'CASE-1001' });
    renderWithClient(<CaseDetailPage />);
    expect(await screen.findByText('Case Detail')).toBeInTheDocument();
    expect(await screen.findByText('PLR_1024_MA')).toBeInTheDocument();
  });
});

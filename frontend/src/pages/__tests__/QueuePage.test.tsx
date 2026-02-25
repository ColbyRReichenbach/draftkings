import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { QueuePage } from '../QueuePage';

const renderWithClient = (ui: React.ReactElement) => {
  const client = new QueryClient();
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
};

describe('QueuePage', () => {
  it('renders queue filters', async () => {
    renderWithClient(<QueuePage />);
    expect(await screen.findByText('Search Player')).toBeInTheDocument();
  });

  it('shows empty-state message when all queue items are already in audit/status', async () => {
    renderWithClient(<QueuePage />);
    expect(await screen.findByText('No cases match the current filters.')).toBeInTheDocument();
  });
});

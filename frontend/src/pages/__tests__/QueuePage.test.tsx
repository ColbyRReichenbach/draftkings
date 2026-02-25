import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi } from 'vitest';
import { QueuePage } from '../QueuePage';

const renderWithClient = (ui: React.ReactElement) => {
  const client = new QueryClient();
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
};

describe('QueuePage', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders queue filters', async () => {
    renderWithClient(<QueuePage />);
    expect(await screen.findByText('Search Player')).toBeInTheDocument();
  });

  it('shows empty-state message when all queue items are already in audit/status', async () => {
    renderWithClient(<QueuePage />);
    expect(await screen.findByText('No cases match the current filters.')).toBeInTheDocument();
  });

  it('renders fallback safely when queue API fails', async () => {
    const originalFetch = global.fetch;
    vi.spyOn(global, 'fetch').mockImplementation((input: RequestInfo | URL, init?: RequestInit) => {
      const url = typeof input === 'string' ? input : input.toString();
      if (url.includes('/api/queue')) {
        return Promise.resolve(
          new Response('boom', {
            status: 500,
            headers: { 'Content-Type': 'text/plain' },
          })
        );
      }
      return originalFetch(input as RequestInfo, init);
    });

    renderWithClient(<QueuePage />);
    expect(await screen.findByText('No cases match the current filters.')).toBeInTheDocument();
  });
});

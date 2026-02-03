import React from 'react';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuditTrailPage } from '../AuditTrailPage';

const renderWithClient = (ui: React.ReactElement) => {
  const client = new QueryClient();
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
};

describe('AuditTrailPage', () => {
  it('renders audit trail heading', async () => {
    renderWithClient(<AuditTrailPage />);
    expect(await screen.findByText('Recent Actions')).toBeInTheDocument();
  });
});

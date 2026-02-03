import React from 'react';
import { render, screen } from '@testing-library/react';
import { RiskCaseCard } from '../RiskCaseCard';
import { RiskCase } from '../../types/risk';

const sampleCase: RiskCase = {
  case_id: 'CASE-0001',
  player_id: 'PLR_1001_MA',
  risk_category: 'HIGH',
  composite_risk_score: 0.78,
  score_calculated_at: '2026-02-03T08:14:00Z',
  state_jurisdiction: 'MA',
  key_evidence: ['Loss chase 0.72']
};

describe('RiskCaseCard', () => {
  it('renders player and score', () => {
    render(
      <RiskCaseCard riskCase={sampleCase} isSelected={false} onSelect={() => undefined} />
    );

    expect(screen.getByText('PLR_1001_MA')).toBeInTheDocument();
    expect(screen.getByText('78%')).toBeInTheDocument();
  });

  it('matches snapshot', () => {
    const { asFragment } = render(
      <RiskCaseCard riskCase={sampleCase} isSelected={false} onSelect={() => undefined} />
    );

    expect(asFragment()).toMatchSnapshot();
  });
});

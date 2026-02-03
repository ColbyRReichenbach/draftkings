import { AnalyticsSummary, AuditEntry, CaseDetail, RiskCase } from '../types/risk';

export const mockCases: RiskCase[] = [
  {
    case_id: 'CASE-1001',
    player_id: 'PLR_1024_MA',
    risk_category: 'CRITICAL',
    composite_risk_score: 0.92,
    score_calculated_at: '2026-02-03T08:14:00Z',
    state_jurisdiction: 'MA',
    key_evidence: ['Loss chase ratio 0.84', 'Escalation 2.4x', 'Night betting spike']
  },
  {
    case_id: 'CASE-1002',
    player_id: 'PLR_2331_NJ',
    risk_category: 'HIGH',
    composite_risk_score: 0.79,
    score_calculated_at: '2026-02-03T06:42:00Z',
    state_jurisdiction: 'NJ',
    key_evidence: ['Market drift 0.68', 'Late-night concentration 71%']
  },
  {
    case_id: 'CASE-1003',
    player_id: 'PLR_8890_PA',
    risk_category: 'HIGH',
    composite_risk_score: 0.73,
    score_calculated_at: '2026-02-02T22:25:00Z',
    state_jurisdiction: 'PA',
    key_evidence: ['Loss chase 0.71', 'Bet escalation 1.9x']
  },
  {
    case_id: 'CASE-1004',
    player_id: 'PLR_4109_MA',
    risk_category: 'MEDIUM',
    composite_risk_score: 0.55,
    score_calculated_at: '2026-02-02T19:11:00Z',
    state_jurisdiction: 'MA',
    key_evidence: ['Temporal risk 0.62', 'Market drift 0.44']
  },
  {
    case_id: 'CASE-1005',
    player_id: 'PLR_7712_NJ',
    risk_category: 'MEDIUM',
    composite_risk_score: 0.49,
    score_calculated_at: '2026-02-02T16:55:00Z',
    state_jurisdiction: 'NJ',
    key_evidence: ['Loss chase 0.53', 'Escalation 1.4x']
  },
  {
    case_id: 'CASE-1006',
    player_id: 'PLR_3033_PA',
    risk_category: 'LOW',
    composite_risk_score: 0.29,
    score_calculated_at: '2026-02-02T14:02:00Z',
    state_jurisdiction: 'PA',
    key_evidence: ['Stable wagering patterns', 'No abnormal spikes']
  }
];

export const mockCaseDetails: CaseDetail[] = [
  {
    case_id: 'CASE-1001',
    player_id: 'PLR_1024_MA',
    risk_category: 'CRITICAL',
    composite_risk_score: 0.92,
    score_calculated_at: '2026-02-03T08:14:00Z',
    state_jurisdiction: 'MA',
    evidence_snapshot: {
      total_bets_7d: 84,
      total_wagered_7d: 7420,
      loss_chase_score: 0.84,
      bet_escalation_score: 0.88,
      market_drift_score: 0.62,
      temporal_risk_score: 0.71,
      gamalyze_risk_score: 0.79
    },
    ai_explanation:
      'Loss-chasing behavior is severe and paired with a sharp escalation in bet sizing, indicating elevated risk. Betting frequency spikes during late-night hours and cross-market drift adds to volatility.',
    draft_nudge:
      'We noticed some unusual patterns in your recent play and want to make sure you are staying in control. You can choose to review tools in the Responsible Gaming Center at rg.draftkings.com. We are here to support you.',
    regulatory_notes: 'MA abnormal-play review completed; no 10x average trigger observed.',
    analyst_actions: ['Immediate outreach', 'Consider temporary limits', 'Documented in audit trail']
  },
  {
    case_id: 'CASE-1002',
    player_id: 'PLR_2331_NJ',
    risk_category: 'HIGH',
    composite_risk_score: 0.79,
    score_calculated_at: '2026-02-03T06:42:00Z',
    state_jurisdiction: 'NJ',
    evidence_snapshot: {
      total_bets_7d: 52,
      total_wagered_7d: 3810,
      loss_chase_score: 0.62,
      bet_escalation_score: 0.71,
      market_drift_score: 0.68,
      temporal_risk_score: 0.66,
      gamalyze_risk_score: 0.7
    },
    ai_explanation:
      'Betting patterns show market drift toward lower-tier markets and a late-night betting concentration. Escalation signals remain elevated compared to baseline.',
    draft_nudge:
      'We want to ensure your play stays safe. You can choose to set limits or explore support tools in the Responsible Gaming Center at rg.draftkings.com.',
    regulatory_notes: 'NJ multi-flag review pending; no 3+ flag trigger in last 30 days.',
    analyst_actions: ['Queue for follow-up', 'Monitor for additional flags']
  },
  {
    case_id: 'CASE-1003',
    player_id: 'PLR_8890_PA',
    risk_category: 'HIGH',
    composite_risk_score: 0.73,
    score_calculated_at: '2026-02-02T22:25:00Z',
    state_jurisdiction: 'PA',
    evidence_snapshot: {
      total_bets_7d: 46,
      total_wagered_7d: 2950,
      loss_chase_score: 0.71,
      bet_escalation_score: 0.65,
      market_drift_score: 0.51,
      temporal_risk_score: 0.48,
      gamalyze_risk_score: 0.69
    },
    ai_explanation:
      'Loss-chasing signals and escalation are both trending upward. Market drift remains moderate but consistent across late sessions.',
    draft_nudge:
      'We are here to support healthy play. You can choose to review limits and tools in the Responsible Gaming Center at rg.draftkings.com.',
    regulatory_notes: 'PA referral trigger not met (no 3+ exclusions).',
    analyst_actions: ['Schedule check-in', 'Document in audit trail']
  },
  {
    case_id: 'CASE-1004',
    player_id: 'PLR_4109_MA',
    risk_category: 'MEDIUM',
    composite_risk_score: 0.55,
    score_calculated_at: '2026-02-02T19:11:00Z',
    state_jurisdiction: 'MA',
    evidence_snapshot: {
      total_bets_7d: 28,
      total_wagered_7d: 1250,
      loss_chase_score: 0.48,
      bet_escalation_score: 0.52,
      market_drift_score: 0.44,
      temporal_risk_score: 0.62,
      gamalyze_risk_score: 0.51
    },
    ai_explanation:
      'Temporal risk increased with late-night betting patterns, while other signals remain moderate.',
    draft_nudge:
      'We want to make sure you have the support you need. You can choose to explore tools in the Responsible Gaming Center at rg.draftkings.com.',
    regulatory_notes: 'MA abnormal-play trigger not met.',
    analyst_actions: ['Send supportive nudge', 'Monitor weekly trend']
  },
  {
    case_id: 'CASE-1005',
    player_id: 'PLR_7712_NJ',
    risk_category: 'MEDIUM',
    composite_risk_score: 0.49,
    score_calculated_at: '2026-02-02T16:55:00Z',
    state_jurisdiction: 'NJ',
    evidence_snapshot: {
      total_bets_7d: 31,
      total_wagered_7d: 1390,
      loss_chase_score: 0.53,
      bet_escalation_score: 0.44,
      market_drift_score: 0.39,
      temporal_risk_score: 0.35,
      gamalyze_risk_score: 0.42
    },
    ai_explanation:
      'Loss-chasing is mild and largely contained, with no abrupt market shifts.',
    draft_nudge:
      'You can choose to check in on your play and set limits in the Responsible Gaming Center at rg.draftkings.com.',
    regulatory_notes: 'NJ 30-day multi-flag threshold not met.',
    analyst_actions: ['Monitor in queue', 'No immediate action']
  },
  {
    case_id: 'CASE-1006',
    player_id: 'PLR_3033_PA',
    risk_category: 'LOW',
    composite_risk_score: 0.29,
    score_calculated_at: '2026-02-02T14:02:00Z',
    state_jurisdiction: 'PA',
    evidence_snapshot: {
      total_bets_7d: 14,
      total_wagered_7d: 620,
      loss_chase_score: 0.25,
      bet_escalation_score: 0.22,
      market_drift_score: 0.18,
      temporal_risk_score: 0.19,
      gamalyze_risk_score: 0.24
    },
    ai_explanation:
      'Player activity remains stable with no indicators of risky escalation.',
    draft_nudge:
      'We are here to support safe play. You can choose to explore tools in the Responsible Gaming Center at rg.draftkings.com.',
    regulatory_notes: 'No PA triggers met.',
    analyst_actions: ['No action required']
  }
];

export const mockAnalyticsSummary: AnalyticsSummary = {
  total_cases: 614,
  avg_risk_score: 0.46,
  critical_share: 0.04,
  high_share: 0.12,
  medium_share: 0.22,
  low_share: 0.62,
  weekly_trend: [
    { week: 'Wk 1', cases: 480 },
    { week: 'Wk 2', cases: 512 },
    { week: 'Wk 3', cases: 569 },
    { week: 'Wk 4', cases: 603 },
    { week: 'Wk 5', cases: 614 }
  ]
};

export const mockAuditTrail: AuditEntry[] = [
  {
    audit_id: 'AUD-4001',
    player_id: 'PLR_1024_MA',
    analyst_id: 'Colby Reichenbach',
    action: 'Immediate outreach',
    risk_category: 'CRITICAL',
    state_jurisdiction: 'MA',
    timestamp: '2026-02-03T09:05:00Z',
    notes: 'Escalation and loss-chasing confirmed. Documented outreach plan.'
  },
  {
    audit_id: 'AUD-4002',
    player_id: 'PLR_2331_NJ',
    analyst_id: 'Colby Reichenbach',
    action: 'Monitor and follow-up',
    risk_category: 'HIGH',
    state_jurisdiction: 'NJ',
    timestamp: '2026-02-03T08:10:00Z',
    notes: 'No regulatory trigger met; keep in watchlist.'
  },
  {
    audit_id: 'AUD-4003',
    player_id: 'PLR_4109_MA',
    analyst_id: 'Colby Reichenbach',
    action: 'Send supportive nudge',
    risk_category: 'MEDIUM',
    state_jurisdiction: 'MA',
    timestamp: '2026-02-02T20:02:00Z',
    notes: 'Night betting spike; provide RG tools.'
  }
];

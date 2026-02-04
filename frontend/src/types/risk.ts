export type RiskCategory = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';

export interface RiskCase {
  case_id: string;
  player_id: string;
  risk_category: RiskCategory;
  composite_risk_score: number;
  score_calculated_at: string;
  state_jurisdiction: 'MA' | 'NJ' | 'PA';
  key_evidence: string[];
}

export interface CaseDetail {
  case_id: string;
  player_id: string;
  risk_category: RiskCategory;
  composite_risk_score: number;
  score_calculated_at: string;
  state_jurisdiction: 'MA' | 'NJ' | 'PA';
  evidence_snapshot: {
    total_bets_7d: number;
    total_wagered_7d: number;
    loss_chase_score: number;
    bet_escalation_score: number;
    market_drift_score: number;
    temporal_risk_score: number;
    gamalyze_risk_score: number;
  };
  ai_explanation: string;
  draft_nudge: string;
  regulatory_notes: string;
  analyst_actions: string[];
}

export interface AnalyticsSummary {
  total_cases: number;
  avg_risk_score: number;
  critical_share: number;
  high_share: number;
  medium_share: number;
  low_share: number;
  weekly_trend: {
    week: string;
    cases: number;
  }[];
}

export interface AuditEntry {
  audit_id: string;
  player_id: string;
  analyst_id: string;
  action: string;
  risk_category: RiskCategory;
  state_jurisdiction: 'MA' | 'NJ' | 'PA';
  timestamp: string;
  notes: string;
}

export interface RiskExplanationRequest {
  player_id: string;
  composite_risk_score: number;
  risk_category?: RiskCategory;
  total_bets_7d?: number;
  total_wagered_7d?: number;
  loss_chase_score?: number;
  bet_escalation_score?: number;
  market_drift_score?: number;
  temporal_risk_score?: number;
  gamalyze_risk_score?: number;
  state_jurisdiction?: 'MA' | 'NJ' | 'PA';
}

export interface RiskExplanationResponse {
  risk_verdict: RiskCategory;
  explanation: string;
  key_evidence: string[];
  recommended_action: string;
  draft_customer_nudge: string;
  regulatory_notes?: string;
}

export interface NudgeValidationResult {
  is_valid: boolean;
  violations: string[];
}

export interface AnalystNoteRequest {
  player_id: string;
  analyst_id: string;
  analyst_action: string;
  analyst_notes: string;
}

export interface AnalystNoteResponse {
  player_id: string;
  analyst_id: string;
  analyst_action: string;
  analyst_notes: string;
  created_at: string;
}

export interface PromptLogEntry {
  player_id: string;
  analyst_id: string;
  prompt_text: string;
  response_text: string;
  created_at: string;
}

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
  total_cases_started: number;
  total_cases_submitted: number;
  in_progress_count: number;
  avg_time_to_submit_hours: number;
  avg_time_in_progress_hours: number;
  sql_queries_logged: number;
  llm_prompts_logged: number;
  cases_with_sql_pct: number;
  cases_with_llm_pct: number;
  risk_mix: {
    critical: number;
    high: number;
    medium: number;
    low: number;
  };
  trigger_checks_run: number;
  nudges_validated: number;
  funnel: {
    queued: number;
    started: number;
    submitted: number;
  };
}

export interface AuditEntry {
  audit_id: string;
  case_id: string;
  player_id: string;
  analyst_id: string;
  action: string;
  risk_category: RiskCategory;
  state_jurisdiction: 'MA' | 'NJ' | 'PA';
  timestamp: string;
  notes: string;
  nudge_status?: string | null;
  nudge_excerpt?: string | null;
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

export interface NudgeLogRequest {
  player_id: string;
  analyst_id: string;
  draft_nudge: string;
  final_nudge: string;
  validation_status: string;
  validation_violations: string[];
}

export interface NudgeLogResponse {
  player_id: string;
  analyst_id: string;
  draft_nudge: string;
  final_nudge: string;
  validation_status: string;
  validation_violations: string[];
  created_at: string;
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

export interface AnalystNoteDraftRequest {
  player_id: string;
  analyst_id: string;
  draft_action: string;
  draft_notes: string;
}

export interface AnalystNoteDraftResponse {
  player_id: string;
  analyst_id: string;
  draft_action: string;
  draft_notes: string;
  updated_at: string;
}

export interface PromptLogEntry {
  player_id: string;
  analyst_id: string;
  prompt_text: string;
  response_text: string;
  route_type?: string | null;
  tool_used?: string | null;
  created_at: string;
}

export interface PromptRouteRequest {
  player_id: string;
  analyst_prompt: string;
}

export interface PromptRouteResponse {
  route: string;
  tool: string;
  reasoning: string;
  model_used: string | null;
  response_text?: string | null;
  draft_sql?: string | null;
  assumptions?: string[] | null;
}

export interface QueryDraftRequest {
  player_id: string;
  analyst_prompt: string;
}

export interface QueryDraftResponse {
  draft_sql: string;
  assumptions: string[];
}

export interface QueryLogEntry {
  player_id: string;
  analyst_id: string;
  prompt_text: string;
  draft_sql: string;
  final_sql: string;
  purpose: string;
  result_summary: string;
  created_at: string;
}

export interface QueryLogRequest {
  player_id: string;
  analyst_id: string;
  prompt_text: string;
  draft_sql: string;
  final_sql: string;
  purpose: string;
  result_summary: string;
}

export interface SqlExecuteRequest {
  player_id: string;
  sql_text: string;
  purpose: string;
  analyst_id?: string;
  prompt_text?: string;
  result_summary?: string;
  log?: boolean;
}

export interface SqlExecuteResponse {
  columns: string[];
  rows: Array<Array<unknown>>;
  row_count: number;
  duration_ms: number;
  result_summary: string;
}

export interface TriggerCheckResult {
  state: 'MA' | 'NJ' | 'PA';
  triggered: boolean;
  reason: string;
  sql_text: string;
  row_count: number;
  created_at?: string | null;
}

export interface CaseTimelineEntry {
  event_type: string;
  event_detail: string;
  created_at: string;
}

export type CaseStatus = 'NOT_STARTED' | 'IN_PROGRESS' | 'SUBMITTED';

export interface CaseStatusRequest {
  case_id: string;
  player_id: string;
  analyst_id: string;
}

export interface CaseStatusEntry {
  case_id: string;
  player_id: string;
  analyst_id: string;
  status: CaseStatus;
  started_at: string | null;
  submitted_at: string | null;
  updated_at: string;
}

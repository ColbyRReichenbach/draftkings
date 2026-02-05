import { useEffect, useMemo, useState } from 'react';
import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';
import { AuditEntry, CaseStatus, SqlExecuteResponse, TriggerCheckResult } from '../types/risk';
import { useCaseDetailByPlayer } from '../hooks/useRiskCases';
import {
  useAnalystNotes,
  useDraftAnalystNotes,
  useSaveDraftAnalystNotes,
  useSubmitAnalystNotes
} from '../hooks/useAnalystNotes';
import { useNudgeValidation, usePromptLogs, useSemanticAudit } from '../hooks/useAi';
import { useNudgeLog, useSaveNudge } from '../hooks/useNudgeLog';
import { useCaseTimeline, useSubmitCase } from '../hooks/useCaseTimeline';
import { useCreateQueryLog, useQueryLog } from '../hooks/useQueryLog';
import { useQueryDraft } from '../hooks/useQueryDraft';
import { usePromptRouter } from '../hooks/usePromptRouter';
import { useRunTriggerChecks, useSqlExecute, useTriggerChecks } from '../hooks/useSqlExecution';
import { PromptLogPanel } from '../components/PromptLogPanel';
import { NudgePreview } from '../components/NudgePreview';
import { InfoBadge } from '../components/InfoBadge';
import { RISK_STYLES } from '../styles/theme';
import { useQueryClient } from '@tanstack/react-query';

interface CaseFilePageProps {
  entry: AuditEntry;
  status: CaseStatus;
  onBack: () => void;
}

const BASE_ACTIONS = [
  'Provide Responsible Gaming Resources (RG Center)',
  'Offer Player Limits (Deposit/Wager/Time)',
  'Offer Cool-Off Period',
  'Offer Self-Exclusion',
  'Monitor & Document'
];

const ACTION_BY_RISK: Record<string, string[]> = {
  CRITICAL: [
    'Immediate analyst review (within 2 hours)',
    'Supportive nudge + timeout offer',
    'Escalate for senior review (manual limits/exclusion)'
  ],
  HIGH: ['Supportive nudge (within 24 hours)', 'Enhanced monitoring (daily)'],
  MEDIUM: ['Watchlist + weekly check-in', 'Optional check-in message'],
  LOW: ['No action (monitor only)']
};

const TRIGGER_ACTIONS: Record<string, string> = {
  NJ: 'Refer for mandatory 24-hour timeout + commission notification (NJ trigger)',
  PA: 'Refer to PA Problem Gambling Council + 72-hour cooling period (PA trigger)',
  MA: 'Internal documentation + analyst review (MA trigger)'
};

const STATUS_STYLES: Record<CaseStatus, { label: string; className: string }> = {
  NOT_STARTED: {
    label: 'Not Started',
    className: 'bg-slate-800 text-slate-300 border-slate-700'
  },
  IN_PROGRESS: {
    label: 'In Progress',
    className: 'bg-[#F3701B] text-black border-transparent'
  },
  SUBMITTED: {
    label: 'Submitted',
    className: 'bg-[#53B848] text-black border-transparent'
  }
};

const SCORE_TOOLTIP =
  'Normalized 0–1 scale. 0.00–0.39 = Low, 0.40–0.59 = Medium, 0.60–0.79 = High, 0.80–1.00 = Critical.';

const KPI_TOOLTIPS: Record<string, string> = {
  'Total Bets (7d)':
    'Total count of bets in the last 7 days. Minimum 2 bets required for ratios to be meaningful.',
  'Total Wagered (7d)':
    'Total wagered amount over the last 7 days. Use with bet count to normalize behavior.',
  'Loss Chase Score': `${SCORE_TOOLTIP} Higher values indicate bets placed after losses.`,
  'Bet Escalation': `${SCORE_TOOLTIP} Higher values indicate larger bets after losses vs wins.`,
  'Market Drift': `${SCORE_TOOLTIP} Higher values indicate drift into atypical sports/market tiers.`,
  'Temporal Risk': `${SCORE_TOOLTIP} Higher values indicate abnormal late-night activity vs baseline.`,
  'Gamalyze': `${SCORE_TOOLTIP} External neuro-marker composite (Mindway AI).`
};

export const CaseFilePage = ({ entry, status, onBack }: CaseFilePageProps) => {
  const { data: detail } = useCaseDetailByPlayer(entry.player_id);
  const notesQuery = useAnalystNotes(entry.player_id);
  const draftNotesQuery = useDraftAnalystNotes(entry.player_id);
  const submitNotes = useSubmitAnalystNotes();
  const saveDraftNotes = useSaveDraftAnalystNotes();
  const submitCase = useSubmitCase();
  const semanticAudit = useSemanticAudit();
  const nudgeValidation = useNudgeValidation();
  const nudgeLog = useNudgeLog(entry.player_id);
  const saveNudge = useSaveNudge();
  const promptLogs = usePromptLogs(entry.player_id);
  const queryLogs = useQueryLog(entry.player_id);
  const timeline = useCaseTimeline(entry.player_id);
  const queryDraft = useQueryDraft();
  const promptRouter = usePromptRouter();
  const sqlExecute = useSqlExecute();
  const createQueryLog = useCreateQueryLog();
  const triggerChecks = useTriggerChecks(entry.player_id);
  const rerunTriggerChecks = useRunTriggerChecks();
  const reactQuery = useQueryClient();

  const [notes, setNotes] = useState('');
  const [action, setAction] = useState('');
  const [prompt, setPrompt] = useState('');
  const [routerPrompt, setRouterPrompt] = useState('');
  const [draftSql, setDraftSql] = useState('');
  const [finalSql, setFinalSql] = useState('');
  const [purpose, setPurpose] = useState('');
  const [resultSummary, setResultSummary] = useState('');
  const [sqlOutput, setSqlOutput] = useState<SqlExecuteResponse | null>(null);
  const [openTriggerSql, setOpenTriggerSql] = useState<Record<string, boolean>>({});
  const [nudgeDraft, setNudgeDraft] = useState('');
  const [nudgeFinal, setNudgeFinal] = useState('');

  useEffect(() => {
    if (notesQuery.data) {
      setNotes(notesQuery.data.analyst_notes ?? '');
      setAction(notesQuery.data.analyst_action ?? '');
      return;
    }
    if (draftNotesQuery.data) {
      setNotes(draftNotesQuery.data.draft_notes ?? '');
      setAction(draftNotesQuery.data.draft_action ?? '');
    }
  }, [notesQuery.data, draftNotesQuery.data]);

  useEffect(() => {
    if (queryDraft.data?.draft_sql) {
      setDraftSql(queryDraft.data.draft_sql);
      setFinalSql(queryDraft.data.draft_sql);
    }
  }, [queryDraft.data]);

  useEffect(() => {
    if (semanticAudit.data?.draft_customer_nudge) {
      setNudgeDraft(semanticAudit.data.draft_customer_nudge);
      if (!nudgeFinal.trim()) {
        setNudgeFinal(semanticAudit.data.draft_customer_nudge);
      }
    }
  }, [semanticAudit.data, nudgeFinal]);

  useEffect(() => {
    if (nudgeLog.data) {
      setNudgeDraft(nudgeLog.data.draft_nudge);
      setNudgeFinal(nudgeLog.data.final_nudge);
    }
  }, [nudgeLog.data]);

  const isInProgress = status === 'IN_PROGRESS';
  const isSubmitted = status === 'SUBMITTED';

  const canSubmitNotes = notes.trim().length >= 10 && action.length > 0;
  const canSubmitDecision = isInProgress && canSubmitNotes;
  const canLogQuery =
    Boolean(sqlOutput) &&
    prompt.trim().length >= 10 &&
    finalSql.trim().length >= 10 &&
    purpose.trim().length >= 5 &&
    (resultSummary.trim().length >= 5 || Boolean(sqlOutput?.result_summary));

  const handleSubmitNotes = () => {
    if (!canSubmitDecision) {
      return;
    }
    submitNotes.mutate(
      {
        player_id: entry.player_id,
        analyst_id: entry.analyst_id,
        analyst_action: action,
        analyst_notes: notes.trim()
      },
      {
        onSuccess: () => {
          submitCase.mutate(
            {
              case_id: entry.case_id,
              player_id: entry.player_id,
              analyst_id: entry.analyst_id
            },
            {
              onSuccess: () => {
                reactQuery.invalidateQueries({ queryKey: ['case-statuses'] });
              }
            }
          );
        }
      }
    );
  };

  const handleSaveDraftNotes = () => {
    if (!isInProgress) {
      return;
    }
    saveDraftNotes.mutate({
      player_id: entry.player_id,
      analyst_id: entry.analyst_id,
      draft_action: action,
      draft_notes: notes
    });
  };

  const handleGenerateExplanation = () => {
    if (!detail) {
      return;
    }
    semanticAudit.mutate({
      player_id: detail.player_id,
      composite_risk_score: detail.composite_risk_score,
      risk_category: detail.risk_category,
      total_bets_7d: detail.evidence_snapshot.total_bets_7d,
      total_wagered_7d: detail.evidence_snapshot.total_wagered_7d,
      loss_chase_score: detail.evidence_snapshot.loss_chase_score,
      bet_escalation_score: detail.evidence_snapshot.bet_escalation_score,
      market_drift_score: detail.evidence_snapshot.market_drift_score,
      temporal_risk_score: detail.evidence_snapshot.temporal_risk_score,
      gamalyze_risk_score: detail.evidence_snapshot.gamalyze_risk_score,
      state_jurisdiction: detail.state_jurisdiction
    });
  };

  const handleValidateNudge = () => {
    const nudgeText = nudgeFinal.trim();
    if (!nudgeText) {
      return;
    }
    nudgeValidation.mutate(nudgeText);
  };

  const handleSaveNudge = () => {
    if (!isInProgress || nudgeFinal.trim().length < 10) {
      return;
    }
    const validationStatus = nudgeValidation.data?.is_valid
      ? 'VALID'
      : nudgeValidation.data
      ? 'INVALID'
      : 'UNVALIDATED';
    saveNudge.mutate(
      {
        player_id: entry.player_id,
        analyst_id: entry.analyst_id,
        draft_nudge: nudgeDraft.trim() || nudgeFinal.trim(),
        final_nudge: nudgeFinal.trim(),
        validation_status: validationStatus,
        validation_violations: nudgeValidation.data?.violations ?? []
      },
      {
        onSuccess: () => {
          reactQuery.invalidateQueries({ queryKey: ['nudge-log', entry.player_id] });
        }
      }
    );
  };

  const handleDraftSql = () => {
    if (!isInProgress) {
      return;
    }
    queryDraft.mutate({ player_id: entry.player_id, analyst_prompt: prompt.trim() });
  };

  const handleRunQuery = () => {
    if (!isInProgress || prompt.trim().length < 10 || finalSql.trim().length < 10) {
      return;
    }
    sqlExecute.mutate(
      {
        player_id: entry.player_id,
        analyst_id: entry.analyst_id,
        prompt_text: prompt.trim(),
        sql_text: finalSql.trim(),
        purpose: purpose.trim() || 'Ad hoc query',
        log: false
      },
      {
        onSuccess: (data) => {
          setSqlOutput(data);
          setResultSummary((prev) => (prev.trim().length > 0 ? prev : data.result_summary));
        }
      }
    );
  };

  const handleRoutePrompt = () => {
    if (!isInProgress || routerPrompt.trim().length < 8) {
      return;
    }
    promptRouter.mutate(
      {
        player_id: entry.player_id,
        analyst_prompt: routerPrompt.trim()
      },
      {
        onSuccess: (data) => {
          if (data.route === 'SQL_DRAFT' && data.draft_sql) {
            setFinalSql(data.draft_sql);
            setPrompt(routerPrompt.trim());
          }
        }
      }
    );
  };

  const handleLogQuery = () => {
    if (!canLogQuery || !isInProgress) {
      return;
    }
    createQueryLog.mutate(
      {
        player_id: entry.player_id,
        analyst_id: entry.analyst_id,
        prompt_text: prompt.trim(),
        draft_sql: draftSql.trim() || finalSql.trim(),
        final_sql: finalSql.trim(),
        purpose: purpose.trim(),
        result_summary: resultSummary.trim() || sqlOutput?.result_summary || 'Query executed.',
        result_columns: sqlOutput?.columns ?? null,
        result_rows: sqlOutput?.rows ?? null,
        row_count: sqlOutput?.row_count ?? null,
        duration_ms: sqlOutput?.duration_ms ?? null
      },
      {
        onSuccess: () => {
          reactQuery.invalidateQueries({ queryKey: ['query-log', entry.player_id] });
          reactQuery.invalidateQueries({ queryKey: ['case-timeline', entry.player_id] });
        }
      }
    );
  };

  const handleExportPdf = async () => {
    const pdf = new jsPDF({ unit: 'pt', format: 'letter' });
    const pageWidth = pdf.internal.pageSize.getWidth();
    const pageHeight = pdf.internal.pageSize.getHeight();
    const margin = 54;
    const contentWidth = pageWidth - margin * 2;
    const lineHeight = 14;
    const HEADER_HEIGHT_FIRST = 82;
    const HEADER_HEIGHT_OTHER = 62;
    const CONTENT_PADDING = 18;
    const FOOTER_RESERVE = 48;

    // Brand palette (typed as tuples for jsPDF compatibility)
    type RGB = [number, number, number];
    const GREEN: RGB = [83, 184, 72];       // #53B848
    const ORANGE: RGB = [243, 112, 27];     // #F3701B
    const DARK_NAVY: RGB = [15, 23, 42];    // #0F172A
    const OFF_WHITE: RGB = [250, 251, 252]; // #FAFBFC
    const LIGHT_GRAY: RGB = [243, 244, 246];// #F3F4F6
    const MID_GRAY: RGB = [156, 163, 175];  // #9CA3AF
    const DARK_GRAY: RGB = [55, 65, 81];    // #374151
    const RED: RGB = [220, 38, 38];         // #DC2626
    const YELLOW: RGB = [234, 179, 8];      // #EAB308
    const WHITE: RGB = [255, 255, 255];

    // Risk badge color map
    const RISK_COLORS: Record<string, RGB> = {
      CRITICAL: RED,
      HIGH: ORANGE,
      MEDIUM: YELLOW,
      LOW: GREEN
    };
    const RISK_TEXT_DARK = ['MEDIUM']; // badges that need dark text

    let totalPages = 1; // will be patched at the end
    const formatSummaryDate = () =>
      new Date().toLocaleString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: 'numeric',
        minute: '2-digit'
      });
    const formatTimestamp = (value: string | number | Date) =>
      new Date(value).toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });

    // ── Footer (drawn on current page) ──────────────────────────────────
    const addFooter = (pageNum: number) => {
      const footerY = pageHeight - 32;
      pdf.setDrawColor(...MID_GRAY);
      pdf.setLineWidth(0.5);
      pdf.line(margin, footerY - 6, pageWidth - margin, footerY - 6);

      pdf.setFont('helvetica', 'normal');
      pdf.setFontSize(7);
      pdf.setTextColor(...MID_GRAY);

      // Left: brand
      pdf.text('DK SENTINEL | Responsible Gaming Analytics', margin, footerY);
      // Center: confidential
      pdf.text('CONFIDENTIAL', pageWidth / 2, footerY, { align: 'center' });
      // Right: page number (placeholder — patched after all pages added)
      pdf.text(`Page ${pageNum}`, pageWidth - margin, footerY, { align: 'right' });
    };

    // ── Page header ──────────────────────────────────────────────────────
    const addPageHeader = (isFirstPage: boolean, appendixSubtitle?: string) => {
      // Green top accent strip
      pdf.setFillColor(...GREEN);
      pdf.rect(0, 0, pageWidth, 10, 'F');

      // Dark navy header block
      pdf.setFillColor(...DARK_NAVY);
      pdf.rect(0, 10, pageWidth, isFirstPage ? 72 : 52, 'F');

      if (isFirstPage) {
        // Brand mark
        pdf.setTextColor(83, 184, 72);
        pdf.setFont('helvetica', 'bold');
        pdf.setFontSize(13);
        pdf.text('DK SENTINEL', margin, 36);

        // Divider between brand and title
        pdf.setDrawColor(83, 184, 72);
        pdf.setLineWidth(1);
        pdf.line(margin, 42, margin + 48, 42);

        // Report title
        pdf.setTextColor(255, 255, 255);
        pdf.setFont('helvetica', 'bold');
        pdf.setFontSize(18);
        pdf.text('Analyst Case Report', margin, 62);

        // Meta info right-aligned
        const summaryDate = formatSummaryDate();
        pdf.setFont('helvetica', 'normal');
        pdf.setFontSize(8);
        pdf.setTextColor(...MID_GRAY);
        pdf.text(`Prepared by  ${entry.analyst_id}`, pageWidth - margin, 52, { align: 'right' });
        pdf.text(`Generated  ${summaryDate}`, pageWidth - margin, 62, { align: 'right' });

        // Bottom border of header
        pdf.setDrawColor(...GREEN);
        pdf.setLineWidth(2);
        pdf.line(0, 82, pageWidth, 82);
      } else {
        // Continuation / appendix pages
        pdf.setTextColor(83, 184, 72);
        pdf.setFont('helvetica', 'bold');
        pdf.setFontSize(9);
        pdf.text('DK SENTINEL', margin, 30);

        pdf.setTextColor(255, 255, 255);
        pdf.setFont('helvetica', 'bold');
        pdf.setFontSize(14);
        pdf.text(appendixSubtitle || 'Analyst Case Report', margin, 50);

        pdf.setDrawColor(...GREEN);
        pdf.setLineWidth(2);
        pdf.line(0, 62, pageWidth, 62);
      }
    };

    // ── Section title with left accent bar ───────────────────────────────
    const addSectionTitle = (label: string, y: number): number => {
      // Orange left bar
      pdf.setFillColor(...ORANGE);
      pdf.rect(margin, y - 9, 3, 14, 'F');

      pdf.setFont('helvetica', 'bold');
      pdf.setFontSize(11);
      pdf.setTextColor(...DARK_NAVY);
      pdf.text(label, margin + 9, y);

      pdf.setFont('helvetica', 'normal');
      pdf.setFontSize(9);
      pdf.setTextColor(...DARK_GRAY);
      return y + 18;
    };

    // ── Body paragraph ───────────────────────────────────────────────────
    const writeParagraph = (text: string, startY: number): number => {
      pdf.setTextColor(...DARK_GRAY);
      pdf.setFontSize(9);
      pdf.setFont('helvetica', 'normal');
      const lines = pdf.splitTextToSize(text, contentWidth);
      pdf.text(lines, margin, startY);
      return startY + lines.length * lineHeight;
    };

    // ── Risk badge pill ──────────────────────────────────────────────────
    const drawRiskBadge = (category: string, x: number, y: number) => {
      const badgeW = 72;
      const badgeH = 20;
      const color: RGB = RISK_COLORS[category] || MID_GRAY;
      pdf.setFillColor(...color);
      pdf.roundedRect(x, y, badgeW, badgeH, 4, 4, 'F');

      const isDark = RISK_TEXT_DARK.includes(category);
      pdf.setTextColor(isDark ? 55 : 255, isDark ? 65 : 255, isDark ? 81 : 255);
      pdf.setFont('helvetica', 'bold');
      pdf.setFontSize(8);
      pdf.text(category, x + badgeW / 2, y + badgeH / 2 + 2.5, { align: 'center' });
    };

    // ── KPI box (single card in the grid) ────────────────────────────────
    const drawKpiBox = (label: string, value: string, x: number, y: number, w: number, h: number, valueColor?: RGB) => {
      // Border
      pdf.setDrawColor(...LIGHT_GRAY);
      pdf.setLineWidth(0.75);
      pdf.roundedRect(x, y, w, h, 3, 3, 'S');

      // Background
      pdf.setFillColor(...OFF_WHITE);
      pdf.roundedRect(x, y, w, h, 3, 3, 'F');
      pdf.setDrawColor(...LIGHT_GRAY);
      pdf.roundedRect(x, y, w, h, 3, 3, 'S');

      // Label
      pdf.setFont('helvetica', 'normal');
      pdf.setFontSize(7.5);
      pdf.setTextColor(...MID_GRAY);
      pdf.text(label, x + w / 2, y + 14, { align: 'center' });

      // Value
      pdf.setFont('helvetica', 'bold');
      pdf.setFontSize(14);
      pdf.setTextColor(...(valueColor || DARK_NAVY));
      pdf.text(value, x + w / 2, y + h - 12, { align: 'center' });
    };

    // ── Page-break helper with footer + new page + header ────────────────
    const getContentTop = (isFirstPage: boolean) =>
      (isFirstPage ? HEADER_HEIGHT_FIRST : HEADER_HEIGHT_OTHER) + CONTENT_PADDING;
    const contentBottom = pageHeight - FOOTER_RESERVE - 8;

    const ensurePage = (
      neededHeight: number,
      curY: number,
      pageNum: { n: number },
      subtitle?: string
    ): number => {
      if (curY + neededHeight > contentBottom) {
        addFooter(pageNum.n);
        pdf.addPage();
        pageNum.n++;
        totalPages = pageNum.n;
        addPageHeader(false, subtitle);
        return getContentTop(false);
      }
      return curY;
    };

    // ────────────────────────────────────────────────────────────────────
    // PAGE 1 — Main report
    // ────────────────────────────────────────────────────────────────────
    const pageNum = { n: 1 };
    addPageHeader(true);

    // ── Case Identification Block ─────────────────────────────────────
    let cursorY = getContentTop(true);

    // Light background box
    pdf.setFillColor(...OFF_WHITE);
    pdf.roundedRect(margin, cursorY, contentWidth, 62, 4, 4, 'F');
    pdf.setDrawColor(...LIGHT_GRAY);
    pdf.setLineWidth(0.75);
    pdf.roundedRect(margin, cursorY, contentWidth, 62, 4, 4, 'S');

    // "CASE IDENTIFICATION" label
    pdf.setFont('helvetica', 'bold');
    pdf.setFontSize(7);
    pdf.setTextColor(...MID_GRAY);
    pdf.text('CASE IDENTIFICATION', margin + 16, cursorY + 14);

    // Player ID — large
    pdf.setFont('helvetica', 'bold');
    pdf.setFontSize(17);
    pdf.setTextColor(...DARK_NAVY);
    pdf.text(entry.player_id, margin + 16, cursorY + 35);

    // State + timestamp below player ID
    pdf.setFont('helvetica', 'normal');
    pdf.setFontSize(8);
    pdf.setTextColor(...MID_GRAY);
    pdf.text(
      `Jurisdiction: ${entry.state_jurisdiction}  •  Last Activity: ${formatTimestamp(entry.timestamp)}`,
      margin + 16,
      cursorY + 48
    );

    // Risk badge — right side
    drawRiskBadge(entry.risk_category, pageWidth - margin - 16 - 72, cursorY + 21);

    // Composite score below badge
    if (detail) {
      pdf.setFont('helvetica', 'bold');
      pdf.setFontSize(8);
      pdf.setTextColor(...DARK_GRAY);
      pdf.text(`Score: ${(detail.composite_risk_score * 100).toFixed(0)}`, pageWidth - margin - 16 - 72 + 36, cursorY + 50, { align: 'center' });
    }

    cursorY += 78;

    // ── Decision Summary ──────────────────────────────────────────────
    cursorY = addSectionTitle('Decision Summary', cursorY);
    const decisionText = notesQuery.data
      ? `${notesQuery.data.analyst_action}: ${notesQuery.data.analyst_notes}`
      : 'Decision pending. Analyst review in progress.';
    cursorY = writeParagraph(decisionText, cursorY);
    cursorY += 6;

    // Disclaimer line
    pdf.setFontSize(7);
    pdf.setTextColor(...MID_GRAY);
    pdf.setFont('helvetica', 'italic');
    pdf.text('Analyst ownership confirmed. AI drafts are assistive only.', margin, cursorY);
    pdf.setFont('helvetica', 'normal');
    cursorY += 20;

    // ── Key Metrics — KPI Grid ────────────────────────────────────────
    const kpiBoxW = (contentWidth - 16) / 3; // 3 columns, 8px gaps
    const kpiBoxH = 56;
    const gap = 8;
    const kpiGridHeight = kpiBoxH * 2 + gap + 24;
    cursorY = ensurePage(kpiGridHeight + 24, cursorY, pageNum);
    cursorY = addSectionTitle('Key Metrics', cursorY);

    const metrics = detail?.evidence_snapshot;
    if (!metrics) {
      cursorY = ensurePage(60, cursorY, pageNum);
      pdf.setFont('helvetica', 'normal');
      pdf.setFontSize(9);
      pdf.setTextColor(...MID_GRAY);
      pdf.text(
        'Evidence snapshot not available yet. Metrics will populate once data is loaded.',
        margin,
        cursorY
      );
      cursorY += 20;
    }

    const scoreColor = (val: number): RGB => {
      if (val >= 0.8) return RED;
      if (val >= 0.6) return ORANGE;
      return DARK_NAVY;
    };

    // Row 1
    drawKpiBox('Total Bets (7d)', metrics ? String(metrics.total_bets_7d) : '—', margin, cursorY, kpiBoxW, kpiBoxH);
    drawKpiBox('Total Wagered (7d)', metrics ? `$${metrics.total_wagered_7d.toLocaleString()}` : '—', margin + kpiBoxW + gap, cursorY, kpiBoxW, kpiBoxH);
    drawKpiBox('Loss Chase Score', metrics ? `${(metrics.loss_chase_score * 100).toFixed(0)}%` : '—', margin + (kpiBoxW + gap) * 2, cursorY, kpiBoxW, kpiBoxH, metrics ? scoreColor(metrics.loss_chase_score) : undefined);
    cursorY += kpiBoxH + gap;

    // Row 2
    drawKpiBox('Bet Escalation', metrics ? `${(metrics.bet_escalation_score * 100).toFixed(0)}%` : '—', margin, cursorY, kpiBoxW, kpiBoxH, metrics ? scoreColor(metrics.bet_escalation_score) : undefined);
    drawKpiBox('Market Drift', metrics ? `${(metrics.market_drift_score * 100).toFixed(0)}%` : '—', margin + kpiBoxW + gap, cursorY, kpiBoxW, kpiBoxH, metrics ? scoreColor(metrics.market_drift_score) : undefined);
    drawKpiBox('Temporal Risk', metrics ? `${(metrics.temporal_risk_score * 100).toFixed(0)}%` : '—', margin + (kpiBoxW + gap) * 2, cursorY, kpiBoxW, kpiBoxH, metrics ? scoreColor(metrics.temporal_risk_score) : undefined);
    cursorY += kpiBoxH + 24;

    // ── Analyst Write-up ──────────────────────────────────────────────
    cursorY = ensurePage(80, cursorY, pageNum);
    cursorY = addSectionTitle('Analyst Write-up', cursorY);
    cursorY = writeParagraph(notes.trim() || 'No analyst notes submitted yet.', cursorY);
    cursorY += 20;

    // ── Customer Nudge ────────────────────────────────────────────────
    cursorY = ensurePage(80, cursorY, pageNum);
    cursorY = addSectionTitle('Customer Nudge', cursorY);
    const nudgeText =
      nudgeLog.data?.final_nudge ||
      nudgeFinal.trim() ||
      semanticAudit.data?.draft_customer_nudge ||
      'No nudge drafted yet.';
    cursorY = writeParagraph(nudgeText, cursorY);
    const nudgeStatus = nudgeLog.data?.validation_status || 'UNVALIDATED';
    pdf.setFont('helvetica', 'bold');
    pdf.setFontSize(8);
    pdf.setTextColor(...DARK_GRAY);
    pdf.text(`Validation: ${nudgeStatus}`, margin, cursorY + 10);
    cursorY += 24;

    // ── Regulatory Trigger Summary ────────────────────────────────────
    cursorY = ensurePage(90, cursorY, pageNum);
    cursorY = addSectionTitle('Regulatory Trigger Summary', cursorY);
    if (!triggerChecks.data?.length) {
      cursorY = writeParagraph('No trigger checks recorded yet.', cursorY);
      cursorY += 12;
    } else {
      triggerChecks.data.forEach((check) => {
        cursorY = ensurePage(40, cursorY, pageNum);
        cursorY = writeParagraph(
          `${check.state}: ${check.triggered ? 'Triggered' : 'Not triggered'} — ${check.reason}`,
          cursorY
        );
        cursorY += 6;
      });
    }

    // ── Evidence & Log Summary ────────────────────────────────────────
    cursorY = ensurePage(90, cursorY, pageNum);
    cursorY = addSectionTitle('Evidence & Log Summary', cursorY);
    const sqlCount = queryLogs.data?.length ?? 0;
    const timelineCount = timeline.data?.length ?? 0;
    const summaryLines = [
      `SQL evidence logged (${sqlCount} ${sqlCount === 1 ? 'query' : 'queries'}). See Appendix for details.`,
      `Timeline entries logged (${timelineCount}). See Appendix for full timeline.`
    ];
    summaryLines.forEach((line) => {
      cursorY = ensurePage(32, cursorY, pageNum);
      cursorY = writeParagraph(line, cursorY);
      cursorY += 4;
    });

    // ────────────────────────────────────────────────────────────────────
    // APPENDIX PAGE(S)
    // ────────────────────────────────────────────────────────────────────
    const appendixSubtitle = 'Appendix — Evidence & Logs';
    addFooter(pageNum.n);
    pdf.addPage();
    pageNum.n++;
    totalPages = pageNum.n;
    addPageHeader(false, appendixSubtitle);
    cursorY = getContentTop(false);

    if (queryLogs.data?.length) {
      queryLogs.data.forEach((log, index) => {
        cursorY = ensurePage(160, cursorY, pageNum, appendixSubtitle);

        // Section title for each query
        cursorY = addSectionTitle(`Query ${index + 1}: ${log.purpose}`, cursorY);

        // Prompt label + text
        pdf.setFont('helvetica', 'bold');
        pdf.setFontSize(8);
        pdf.setTextColor(...DARK_GRAY);
        pdf.text('Analyst Prompt', margin, cursorY);
        cursorY += 14;
        cursorY = writeParagraph(log.prompt_text, cursorY);
        cursorY += 10;

        // Final SQL — code block
        pdf.setFont('helvetica', 'bold');
        pdf.setFontSize(8);
        pdf.setTextColor(...DARK_GRAY);
        pdf.text('Final SQL', margin, cursorY);
        cursorY += 14;

        const finalLines = pdf.splitTextToSize(log.final_sql, contentWidth - 24);
        const finalBlockH = finalLines.length * 11 + 16;
        pdf.setFillColor(...LIGHT_GRAY);
        pdf.roundedRect(margin, cursorY - 4, contentWidth, finalBlockH, 3, 3, 'F');
        pdf.setFont('courier', 'normal');
        pdf.setFontSize(7.5);
        pdf.setTextColor(...DARK_NAVY);
        pdf.text(finalLines, margin + 12, cursorY + 6);
        cursorY += finalBlockH + 12;

        const outputRows = (log.result_rows ?? []).slice(0, 10);
        const outputColumns = log.result_columns ?? [];
        if (outputRows.length && outputColumns.length) {
          cursorY = ensurePage(140, cursorY + 8, pageNum, appendixSubtitle);
          pdf.setFont('helvetica', 'bold');
          pdf.setFontSize(8);
          pdf.setTextColor(...DARK_GRAY);
          pdf.text('SQL Output Preview (top rows)', margin, cursorY);
          cursorY += 10;

          autoTable(pdf, {
            startY: cursorY,
            head: [outputColumns],
            body: outputRows.map((row) => row.map((cell) => String(cell))),
            styles: {
              fontSize: 7,
              textColor: DARK_GRAY,
              cellPadding: 4,
              lineColor: LIGHT_GRAY,
              lineWidth: 0.5,
              overflow: 'linebreak'
            },
            headStyles: {
              fillColor: DARK_NAVY,
              textColor: WHITE,
              fontStyle: 'bold',
              fontSize: 7
            },
            alternateRowStyles: { fillColor: OFF_WHITE },
            margin: { left: margin, right: margin, top: getContentTop(false), bottom: FOOTER_RESERVE },
            didDrawPage: () => {
              addPageHeader(false, appendixSubtitle);
            }
          });
          cursorY =
            (pdf as any).lastAutoTable?.finalY ? (pdf as any).lastAutoTable.finalY + 16 : cursorY + 16;
          cursorY = ensurePage(60, cursorY, pageNum, appendixSubtitle);
        } else {
          cursorY = ensurePage(40, cursorY, pageNum, appendixSubtitle);
          cursorY = writeParagraph('No SQL output snapshot stored for this query.', cursorY);
          cursorY += 12;
        }

        pdf.setFont('helvetica', 'bold');
        pdf.setFontSize(8);
        pdf.setTextColor(...DARK_GRAY);
        pdf.text('Result Summary', margin, cursorY);
        cursorY += 12;
        cursorY = writeParagraph(log.result_summary || 'No summary recorded.', cursorY);
        cursorY += 18;
      });
    } else {
      cursorY = ensurePage(60, cursorY, pageNum, appendixSubtitle);
      writeParagraph('No SQL queries logged for this case.', cursorY);
    }

    // ── Case Timeline ────────────────────────────────────────────────
    cursorY = ensurePage(80, cursorY + 10, pageNum, appendixSubtitle);
    cursorY = addSectionTitle('Case Timeline', cursorY);
    if (timeline.data?.length) {
      autoTable(pdf, {
        startY: cursorY,
        head: [['Event', 'Detail', 'Timestamp']],
        body: (timeline.data ?? []).map((item) => [
          item.event_type,
          item.event_detail,
          formatTimestamp(item.created_at)
        ]),
        styles: {
          fontSize: 8,
          textColor: DARK_GRAY,
          cellPadding: 5,
          lineColor: LIGHT_GRAY,
          lineWidth: 0.5
        },
        headStyles: {
          fillColor: DARK_NAVY,
          textColor: WHITE,
          fontStyle: 'bold',
          fontSize: 8
        },
        alternateRowStyles: { fillColor: OFF_WHITE },
        margin: { left: margin, right: margin, top: getContentTop(false), bottom: FOOTER_RESERVE },
        didDrawPage: () => {
          addPageHeader(false, appendixSubtitle);
        }
      });
      cursorY = (pdf as any).lastAutoTable?.finalY ? (pdf as any).lastAutoTable.finalY + 24 : cursorY + 24;
    } else {
      cursorY = writeParagraph('No timeline entries available yet.', cursorY);
      cursorY += 12;
    }

    // Footer on appendix page(s)
    addFooter(pageNum.n);

    // ── Patch page numbers now that we know totalPages ───────────────
    // Re-render footers with "Page X of Y" — jsPDF doesn't support true
    // live page counts, so we iterate and overwrite the page-number text.
    totalPages = pdf.getNumberOfPages();
    for (let i = 1; i <= totalPages; i++) {
      pdf.setPage(i);
      addFooter(i);
      // Overwrite just the page-number area with corrected text
      pdf.setFillColor(255, 255, 255); // white cover
      pdf.rect(pageWidth - margin - 52, pageHeight - 37, 52, 12, 'F');
      pdf.setFont('helvetica', 'normal');
      pdf.setFontSize(7);
      pdf.setTextColor(...MID_GRAY);
      pdf.text(`Page ${i} of ${totalPages}`, pageWidth - margin, pageHeight - 32, { align: 'right' });
    }

    pdf.save(`analyst-report-${entry.player_id}.pdf`);
  };

  const decisionSummary = useMemo(() => {
    if (!notesQuery.data) {
      return 'Decision pending. Analyst review in progress.';
    }
    return `${notesQuery.data.analyst_action} — ${notesQuery.data.analyst_notes}`;
  }, [notesQuery.data]);

  const actionOptions = useMemo(() => {
    const riskCategory = entry.risk_category ?? 'HIGH';
    const options = new Set<string>([...BASE_ACTIONS, ...(ACTION_BY_RISK[riskCategory] ?? [])]);
    (triggerChecks.data ?? []).forEach((check) => {
      if (check.triggered && TRIGGER_ACTIONS[check.state]) {
        options.add(TRIGGER_ACTIONS[check.state]);
      }
    });
    return Array.from(options);
  }, [entry.risk_category, triggerChecks.data]);

  const sqlErrorMessage = useMemo(() => {
    if (!sqlExecute.error) {
      return null;
    }
    const raw =
      sqlExecute.error instanceof Error
        ? sqlExecute.error.message
        : String(sqlExecute.error);
    const trimmed = raw.trim();
    if (trimmed.startsWith('{')) {
      try {
        const parsed = JSON.parse(trimmed);
        if (parsed?.detail) {
          return parsed.detail;
        }
      } catch {
        return raw;
      }
    }
    return raw;
  }, [sqlExecute.error]);

  return (
    <div className="grid gap-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-end gap-3">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
              Case File
            </p>
            <h2 className="font-display text-2xl text-slate-100">{entry.player_id}</h2>
            <p className="text-sm text-slate-400">
              {entry.state_jurisdiction}
            </p>
          </div>
          <span
            className={`mb-1 inline-block rounded-full px-3 py-0.5 text-xs font-semibold uppercase tracking-wide ${RISK_STYLES[entry.risk_category]?.badge ?? 'bg-slate-600 text-white'}`}
          >
            {entry.risk_category}
          </span>
          <span
            className={`mb-1 inline-flex items-center gap-2 rounded-full border px-3 py-0.5 text-xs font-semibold uppercase tracking-wide ${STATUS_STYLES[status].className}`}
          >
            {STATUS_STYLES[status].label}
          </span>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={handleExportPdf}
            className="hover-lift rounded-xl bg-[#53B848] px-4 py-2 text-xs font-semibold uppercase tracking-wide text-black"
          >
            Export Analyst Report (PDF)
          </button>
          <button
            type="button"
            onClick={onBack}
            className="hover-lift rounded-xl border border-slate-700 bg-slate-800 px-4 py-2 text-xs font-semibold uppercase tracking-wide text-slate-200"
          >
            Back to Audit Trail
          </button>
        </div>
      </div>

      {!isInProgress ? (
        <div className="glass-panel panel-sheen rounded-2xl border border-slate-800 bg-slate-900/70 p-4 text-sm text-slate-300">
          {isSubmitted ? (
            <span>
              This case has been submitted. Notes and SQL evidence are locked for audit integrity.
            </span>
          ) : (
            <span>
              This case is not started yet. Use <span className="font-semibold">Start Case Review</span> in
              Case Detail to open the workbench.
            </span>
          )}
        </div>
      ) : null}

      <div className="grid gap-4">
        <div className="glass-panel panel-sheen rounded-2xl p-5">
          <p className="border-l-[3px] border-[#53B848] pl-2 text-xs font-semibold uppercase tracking-wide text-slate-400">
            Decision Summary
          </p>
          <p className="mt-2 text-sm text-slate-200">{decisionSummary}</p>
          <p className="mt-2 text-xs text-slate-400">
            Analyst ownership confirmed. AI drafts are assistive only.
          </p>
        </div>

        <div className="glass-panel panel-sheen rounded-2xl p-5 overflow-visible">
          <p className="border-l-[3px] border-[#F3701B] pl-2 text-xs font-semibold uppercase tracking-wide text-slate-400">
            Evidence Snapshot
          </p>
          {detail ? (
            <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              <InfoBadge label={KPI_TOOLTIPS['Total Bets (7d)']} className="rounded-xl bg-slate-950/60 p-3">
                  <p className="text-xs text-slate-400">Total Bets (7d)</p>
                  <p className="text-lg font-semibold text-slate-100">
                    {detail.evidence_snapshot.total_bets_7d}
                  </p>
              </InfoBadge>
              <InfoBadge label={KPI_TOOLTIPS['Total Wagered (7d)']} className="rounded-xl bg-slate-950/60 p-3">
                  <p className="text-xs text-slate-400">Total Wagered (7d)</p>
                  <p className="text-lg font-semibold text-slate-100">
                    ${detail.evidence_snapshot.total_wagered_7d.toLocaleString()}
                  </p>
              </InfoBadge>
              <InfoBadge label={KPI_TOOLTIPS['Loss Chase Score']} className="rounded-xl bg-slate-950/60 p-3">
                  <p className="text-xs text-slate-400">Loss Chase Score</p>
                  <p className={`text-lg font-semibold ${detail.evidence_snapshot.loss_chase_score >= 0.8 ? 'text-red-400' : detail.evidence_snapshot.loss_chase_score >= 0.6 ? 'text-[#F3701B]' : 'text-slate-100'}`}>
                    {detail.evidence_snapshot.loss_chase_score.toFixed(2)}
                    <span className="ml-2 text-xs text-slate-500">
                      ({(detail.evidence_snapshot.loss_chase_score * 100).toFixed(0)}%)
                    </span>
                  </p>
              </InfoBadge>
              <InfoBadge label={KPI_TOOLTIPS['Bet Escalation']} className="rounded-xl bg-slate-950/60 p-3">
                  <p className="text-xs text-slate-400">Bet Escalation</p>
                  <p className={`text-lg font-semibold ${detail.evidence_snapshot.bet_escalation_score >= 0.8 ? 'text-red-400' : detail.evidence_snapshot.bet_escalation_score >= 0.6 ? 'text-[#F3701B]' : 'text-slate-100'}`}>
                    {detail.evidence_snapshot.bet_escalation_score.toFixed(2)}
                    <span className="ml-2 text-xs text-slate-500">
                      ({(detail.evidence_snapshot.bet_escalation_score * 100).toFixed(0)}%)
                    </span>
                  </p>
              </InfoBadge>
              <InfoBadge label={KPI_TOOLTIPS['Market Drift']} className="rounded-xl bg-slate-950/60 p-3">
                  <p className="text-xs text-slate-400">Market Drift</p>
                  <p className={`text-lg font-semibold ${detail.evidence_snapshot.market_drift_score >= 0.8 ? 'text-red-400' : detail.evidence_snapshot.market_drift_score >= 0.6 ? 'text-[#F3701B]' : 'text-slate-100'}`}>
                    {detail.evidence_snapshot.market_drift_score.toFixed(2)}
                    <span className="ml-2 text-xs text-slate-500">
                      ({(detail.evidence_snapshot.market_drift_score * 100).toFixed(0)}%)
                    </span>
                  </p>
              </InfoBadge>
              <InfoBadge label={KPI_TOOLTIPS['Temporal Risk']} className="rounded-xl bg-slate-950/60 p-3">
                  <p className="text-xs text-slate-400">Temporal Risk</p>
                  <p className={`text-lg font-semibold ${detail.evidence_snapshot.temporal_risk_score >= 0.8 ? 'text-red-400' : detail.evidence_snapshot.temporal_risk_score >= 0.6 ? 'text-[#F3701B]' : 'text-slate-100'}`}>
                    {detail.evidence_snapshot.temporal_risk_score.toFixed(2)}
                    <span className="ml-2 text-xs text-slate-500">
                      ({(detail.evidence_snapshot.temporal_risk_score * 100).toFixed(0)}%)
                    </span>
                  </p>
              </InfoBadge>
              <InfoBadge label={KPI_TOOLTIPS['Gamalyze']} className="rounded-xl bg-slate-950/60 p-3">
                  <p className="text-xs text-slate-400">Gamalyze</p>
                  <p className={`text-lg font-semibold ${detail.evidence_snapshot.gamalyze_risk_score >= 0.8 ? 'text-red-400' : detail.evidence_snapshot.gamalyze_risk_score >= 0.6 ? 'text-[#F3701B]' : 'text-slate-100'}`}>
                    {detail.evidence_snapshot.gamalyze_risk_score.toFixed(2)}
                    <span className="ml-2 text-xs text-slate-500">
                      ({(detail.evidence_snapshot.gamalyze_risk_score * 100).toFixed(0)}%)
                    </span>
                  </p>
              </InfoBadge>
            </div>
          ) : (
            <p className="mt-2 text-sm text-slate-400">Loading evidence snapshot...</p>
          )}
        </div>

        <div className="glass-panel panel-sheen rounded-2xl p-5">
          <p className="border-l-[3px] border-[#53B848] pl-2 text-xs font-semibold uppercase tracking-wide text-slate-400">
            Analyst Notes
          </p>
          <textarea
            value={notes}
            onChange={(event) => setNotes(event.target.value)}
            placeholder="Document rationale, evidence reviewed, and decision context..."
            readOnly={!isInProgress}
            className="mt-3 h-28 w-full rounded-xl border border-slate-700 bg-slate-950/60 px-3 py-2 text-sm text-slate-100 placeholder:text-slate-500 focus:border-[#53B848] focus:outline-none disabled:cursor-not-allowed disabled:bg-slate-900"
          />
          <div className="mt-3 flex flex-wrap items-center gap-3">
            <select
              value={action}
              onChange={(event) => setAction(event.target.value)}
              disabled={!isInProgress}
              className="rounded-xl border border-slate-700 bg-slate-950/60 px-3 py-2 text-sm text-slate-100"
            >
              <option value="" disabled>
                Select action
              </option>
              {actionOptions.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
            <button
              type="button"
              onClick={handleSaveDraftNotes}
              disabled={!isInProgress || saveDraftNotes.isPending}
              className="hover-lift rounded-xl border border-slate-700 bg-slate-900/70 px-4 py-2 text-xs font-semibold uppercase tracking-wide text-slate-200 disabled:cursor-not-allowed disabled:bg-slate-700 disabled:text-slate-400"
            >
              {saveDraftNotes.isPending ? 'Saving...' : 'Save Draft'}
            </button>
            <button
              type="button"
              onClick={handleSubmitNotes}
              disabled={!canSubmitDecision || submitNotes.isPending || submitCase.isPending}
              className="hover-lift rounded-xl border border-slate-700 bg-[#53B848] px-4 py-2 text-xs font-semibold uppercase tracking-wide text-black disabled:cursor-not-allowed disabled:bg-slate-700 disabled:text-slate-400"
            >
              {submitNotes.isPending || submitCase.isPending ? 'Saving...' : 'Submit Decision'}
            </button>
            {submitNotes.isSuccess ? (
              <span className="text-xs text-emerald-300">Saved.</span>
            ) : null}
            {saveDraftNotes.isSuccess ? (
              <span className="text-xs text-slate-400">Draft saved.</span>
            ) : null}
          </div>
        </div>

        <PromptLogPanel logs={promptLogs.data ?? []} />

        <div className="glass-panel panel-sheen rounded-2xl p-5">
          <p className="border-l-[3px] border-[#53B848] pl-2 text-xs font-semibold uppercase tracking-wide text-slate-400">
            AI Actions (Drafts Only)
          </p>
          <p className="mt-2 text-xs text-slate-400">
            AI drafts are assistive only. Analyst approval required before any action.
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            <button
              type="button"
              onClick={handleGenerateExplanation}
              disabled={!isInProgress || semanticAudit.isPending}
              className="hover-lift rounded-xl bg-[#53B848] px-4 py-2 text-xs font-semibold uppercase tracking-wide text-black disabled:cursor-not-allowed disabled:bg-slate-700 disabled:text-slate-400"
            >
              {semanticAudit.isPending ? 'Drafting...' : 'Draft AI Summary'}
            </button>
            <button
              type="button"
              onClick={handleValidateNudge}
              disabled={
                !isInProgress ||
                nudgeValidation.isPending ||
                !(semanticAudit.data?.draft_customer_nudge ?? detail?.draft_nudge)
              }
              className="hover-lift rounded-xl border border-slate-700 bg-slate-900/70 px-4 py-2 text-xs font-semibold uppercase tracking-wide text-slate-200 disabled:cursor-not-allowed disabled:bg-slate-700 disabled:text-slate-400"
            >
              {nudgeValidation.isPending ? 'Validating...' : 'Validate Nudge'}
            </button>
          </div>
          {semanticAudit.isError ? (
            <p className="mt-2 text-xs text-red-300">AI draft failed. Check API.</p>
          ) : null}
          {semanticAudit.data?.explanation ? (
            <div className="mt-3 rounded-xl bg-slate-950/60 p-3 text-xs text-slate-300">
              <p className="font-semibold text-slate-200">Draft AI Summary</p>
              <p className="mt-2">{semanticAudit.data.explanation}</p>
            </div>
          ) : null}
          <div className="mt-3 grid gap-3 lg:grid-cols-2">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">Draft Nudge</p>
              <textarea
                value={nudgeDraft}
                onChange={(event) => setNudgeDraft(event.target.value)}
                disabled={!isInProgress}
                className="mt-2 h-24 w-full rounded-xl border border-slate-700 bg-slate-950/60 px-3 py-2 text-xs text-slate-100"
                placeholder="Draft nudge from AI will appear here."
              />
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                Analyst Final Nudge
              </p>
              <textarea
                value={nudgeFinal}
                onChange={(event) => setNudgeFinal(event.target.value)}
                disabled={!isInProgress}
                className="mt-2 h-24 w-full rounded-xl border border-slate-700 bg-slate-950/60 px-3 py-2 text-xs text-slate-100"
                placeholder="Edit the nudge to reflect analyst tone and compliance."
              />
            </div>
          </div>
          <NudgePreview
            nudgeText={nudgeFinal.trim() || nudgeDraft.trim()}
            validationResult={nudgeValidation.data ?? null}
            isValidating={nudgeValidation.isPending}
          />
          <div className="mt-3 flex flex-wrap items-center gap-2 text-xs text-slate-400">
            <button
              type="button"
              onClick={handleSaveNudge}
              disabled={!isInProgress || saveNudge.isPending || nudgeFinal.trim().length < 10}
              className="rounded-xl border border-slate-700 bg-[#53B848] px-3 py-2 text-xs font-semibold uppercase tracking-wide text-black disabled:cursor-not-allowed disabled:bg-slate-700 disabled:text-slate-400"
            >
              {saveNudge.isPending ? 'Saving...' : 'Save Nudge'}
            </button>
            {saveNudge.isSuccess ? <span className="text-emerald-300">Saved.</span> : null}
            {nudgeLog.data?.created_at ? (
              <span>Last saved: {new Date(nudgeLog.data.created_at).toLocaleString()}</span>
            ) : null}
          </div>
        </div>

        <div className="glass-panel panel-sheen rounded-2xl p-5">
          <p className="border-l-[3px] border-[#53B848] pl-2 text-xs font-semibold uppercase tracking-wide text-slate-400">
            Regulatory Trigger Checks
          </p>
          <p className="mt-2 text-xs text-slate-400">
            Deterministic checks for state-mandated triggers. Logged as SQL evidence.
          </p>
          <div className="mt-2 flex flex-wrap items-center gap-2">
            <button
              type="button"
              onClick={() =>
                rerunTriggerChecks.mutate(entry.player_id, {
                  onSuccess: () =>
                    reactQuery.invalidateQueries({
                      queryKey: ['trigger-checks', entry.player_id]
                    })
                })
              }
              disabled={rerunTriggerChecks.isPending}
              className="rounded-lg border border-slate-700 bg-slate-950/60 px-3 py-1 text-[11px] font-semibold uppercase tracking-wide text-slate-200 hover:border-slate-500 disabled:cursor-not-allowed disabled:text-slate-500"
            >
              {rerunTriggerChecks.isPending ? 'Rechecking...' : 'Re-run Trigger Check'}
            </button>
          </div>
          {triggerChecks.isLoading ? (
            <p className="mt-3 text-sm text-slate-400">Running trigger checks...</p>
          ) : triggerChecks.data?.length ? (
            <div className="mt-3 space-y-3">
              {triggerChecks.data.map((check: TriggerCheckResult) => {
                const isOpen = openTriggerSql[check.state];
                return (
                  <div key={check.state} className="rounded-xl border border-slate-800 bg-slate-950/60 p-3">
                    <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-slate-300">
                      <div className="flex items-center gap-2">
                        <span className="rounded-full border border-slate-700 px-2 py-0.5">
                          {check.state}
                        </span>
                        <span
                          className={`rounded-full px-2 py-0.5 text-[11px] ${
                            check.triggered
                              ? 'bg-[#F3701B] text-black'
                              : 'bg-slate-800 text-slate-300'
                          }`}
                        >
                          {check.triggered ? 'Triggered' : 'Not Triggered'}
                        </span>
                      </div>
                      <button
                        type="button"
                        onClick={() =>
                          setOpenTriggerSql((prev) => ({
                            ...prev,
                            [check.state]: !prev[check.state]
                          }))
                        }
                        className="text-[11px] text-slate-400 hover:text-slate-200"
                      >
                        {isOpen ? 'Hide SQL' : 'View SQL'}
                      </button>
                    </div>
                    <p className="mt-2 text-xs text-slate-400">{check.reason}</p>
                    {check.created_at ? (
                      <p className="mt-1 text-[11px] text-slate-500">
                        Last checked: {new Date(check.created_at).toLocaleString()}
                      </p>
                    ) : null}
                    {isOpen ? (
                      <pre className="mt-3 whitespace-pre-wrap rounded-xl bg-slate-950/80 p-3 text-xs text-slate-200">
                        {check.sql_text}
                      </pre>
                    ) : null}
                  </div>
                );
              })}
            </div>
          ) : (
            <p className="mt-3 text-sm text-slate-400">No trigger checks available.</p>
          )}
        </div>

        <div className="glass-panel panel-sheen rounded-2xl p-5">
          <p className="border-l-[3px] border-[#53B848] pl-2 text-xs font-semibold uppercase tracking-wide text-slate-400">
            Analyst Prompt Router
          </p>
          <textarea
            value={routerPrompt}
            onChange={(event) => setRouterPrompt(event.target.value)}
            placeholder="Ask a question (SQL, regulatory, or external context)."
            readOnly={!isInProgress}
            className="mt-3 h-20 w-full rounded-xl border border-slate-700 bg-slate-950/60 px-3 py-2 text-sm text-slate-100 placeholder:text-slate-500 focus:border-[#53B848] focus:outline-none disabled:cursor-not-allowed disabled:bg-slate-900"
          />
          <div className="mt-3 flex flex-wrap items-center gap-2">
            <button
              type="button"
              onClick={handleRoutePrompt}
              disabled={!isInProgress || routerPrompt.trim().length < 8 || promptRouter.isPending}
              className="hover-lift rounded-xl border border-slate-700 bg-[#53B848] px-4 py-2 text-xs font-semibold uppercase tracking-wide text-black disabled:cursor-not-allowed disabled:bg-slate-700 disabled:text-slate-400"
            >
              {promptRouter.isPending ? 'Routing...' : 'Route Prompt'}
            </button>
            {promptRouter.data ? (
              <div className="flex flex-wrap gap-2 text-[11px] text-slate-300">
                <span className="rounded-full border border-slate-700 px-2 py-0.5">
                  Route: {promptRouter.data.route}
                </span>
                <span className="rounded-full border border-slate-700 px-2 py-0.5">
                  Tool: {promptRouter.data.tool}
                </span>
              </div>
            ) : null}
          </div>
          {promptRouter.isError ? (
            <p className="mt-2 text-xs text-red-300">Router failed. Check API key.</p>
          ) : null}
          {promptRouter.data?.reasoning ? (
            <p className="mt-2 text-xs text-slate-400">{promptRouter.data.reasoning}</p>
          ) : null}
          {promptRouter.data?.response_text ? (
            <div className="mt-3 rounded-xl bg-slate-950/60 p-3 text-xs text-slate-300">
              {promptRouter.data.response_text}
            </div>
          ) : null}
          {promptRouter.data?.draft_sql ? (
            <div className="mt-3 rounded-xl bg-slate-950/60 p-3 text-xs text-slate-300">
              <p className="font-semibold text-slate-200">Draft SQL</p>
              <pre className="mt-2 whitespace-pre-wrap">{promptRouter.data.draft_sql}</pre>
            </div>
          ) : null}
        </div>

        <div className="glass-panel panel-sheen rounded-2xl p-5">
          <p className="border-l-[3px] border-[#F3701B] pl-2 text-xs font-semibold uppercase tracking-wide text-slate-400">
            SQL Assistant
          </p>
          <p className="mt-2 text-xs text-slate-400">
            PII is restricted. Do not include names or emails in queries.
          </p>
          <textarea
            value={prompt}
            onChange={(event) => setPrompt(event.target.value)}
            placeholder='Ask the assistant to draft SQL (e.g., "Show the last 30 bets placed between 2–6 AM").'
            readOnly={!isInProgress}
            className="mt-3 h-20 w-full rounded-xl border border-slate-700 bg-slate-950/60 px-3 py-2 text-sm text-slate-100 placeholder:text-slate-500 focus:border-[#53B848] focus:outline-none disabled:cursor-not-allowed disabled:bg-slate-900"
          />
          <div className="mt-3 flex flex-wrap gap-2">
            <button
              type="button"
              onClick={handleDraftSql}
              disabled={!isInProgress || prompt.trim().length < 10 || queryDraft.isPending}
              className="hover-lift rounded-xl bg-[#53B848] px-4 py-2 text-xs font-semibold uppercase tracking-wide text-black disabled:cursor-not-allowed disabled:bg-slate-700 disabled:text-slate-400"
            >
              {queryDraft.isPending ? 'Drafting...' : 'Draft SQL'}
            </button>
            {queryDraft.isError ? (
              <span className="text-xs text-red-300">Draft failed. Check API.</span>
            ) : null}
          </div>
          {queryDraft.data?.assumptions?.length ? (
            <div className="mt-3 rounded-xl bg-slate-950/60 p-3 text-xs text-slate-300">
              <p className="font-semibold text-slate-200">Assumptions</p>
              <ul className="mt-2 list-disc space-y-1 pl-5">
                {queryDraft.data.assumptions.map((assumption) => (
                  <li key={assumption}>{assumption}</li>
                ))}
              </ul>
            </div>
          ) : null}
          <div className="mt-3 grid gap-3 lg:grid-cols-2">
            <div>
              <p className="text-xs text-slate-400">Draft SQL (editable)</p>
              <textarea
                value={finalSql}
                onChange={(event) => setFinalSql(event.target.value)}
                placeholder="LLM draft appears here."
                readOnly={!isInProgress}
                className="mt-2 h-40 w-full rounded-xl border border-slate-700 bg-slate-950/60 px-3 py-2 text-xs text-slate-100 placeholder:text-slate-500 focus:border-[#53B848] focus:outline-none disabled:cursor-not-allowed disabled:bg-slate-900"
              />
            </div>
            <div className="grid gap-3">
              <div>
                <p className="text-xs text-slate-400">Purpose</p>
                <input
                  value={purpose}
                  onChange={(event) => setPurpose(event.target.value)}
                  disabled={!isInProgress}
                  className="mt-2 w-full rounded-xl border border-slate-700 bg-slate-950/60 px-3 py-2 text-sm text-slate-100"
                  placeholder="Why this query was needed"
                />
              </div>
              <div>
                <p className="text-xs text-slate-400">Result Summary</p>
                <textarea
                  value={resultSummary}
                  onChange={(event) => setResultSummary(event.target.value)}
                  disabled={!isInProgress}
                  className="mt-2 h-24 w-full rounded-xl border border-slate-700 bg-slate-950/60 px-3 py-2 text-sm text-slate-100"
                  placeholder="Summarize findings from the query output (auto-filled after execution)."
                />
                {!sqlOutput ? (
                  <p className="mt-1 text-[11px] text-slate-500">
                    Run & log the query to capture sample output and prefill this summary.
                  </p>
                ) : null}
              </div>
              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={handleRunQuery}
                  disabled={!isInProgress || sqlExecute.isPending || finalSql.trim().length < 10}
                  className="hover-lift rounded-xl border border-slate-700 bg-[#53B848] px-4 py-2 text-xs font-semibold uppercase tracking-wide text-black disabled:cursor-not-allowed disabled:bg-slate-700 disabled:text-slate-400"
                >
              {sqlExecute.isPending ? 'Running...' : 'Run Query'}
            </button>
            <button
              type="button"
              onClick={handleLogQuery}
                  disabled={!isInProgress || !canLogQuery || createQueryLog.isPending}
                  className="hover-lift rounded-xl border border-slate-700 bg-slate-900/70 px-4 py-2 text-xs font-semibold uppercase tracking-wide text-slate-200 disabled:cursor-not-allowed disabled:bg-slate-700 disabled:text-slate-400"
                >
              {createQueryLog.isPending ? 'Logging...' : 'Log Result'}
            </button>
          </div>
          {sqlExecute.isError ? (
            <p className="text-xs text-red-300">
              SQL execution failed. {sqlErrorMessage ?? 'Check syntax and table names.'}
            </p>
          ) : null}
        </div>
      </div>
          <p className="mt-2 text-xs text-slate-400">
            SQL drafts are assistive only. Analyst review is required before logging.
            Snowflake SQL only (DATEADD, DATEDIFF, DATE_TRUNC, ILIKE, QUALIFY).
          </p>
        </div>

        <div className="glass-panel panel-sheen rounded-2xl p-5">
          <p className="border-l-[3px] border-[#F3701B] pl-2 text-xs font-semibold uppercase tracking-wide text-slate-400">
            SQL Output (Read-only)
          </p>
          {sqlOutput ? (
            <div className="mt-3 space-y-3">
              <div className="flex flex-wrap items-center gap-2 text-xs text-slate-400">
                <span>{sqlOutput.row_count} rows returned</span>
                <span>•</span>
                <span>{sqlOutput.duration_ms} ms</span>
              </div>
              <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-950/60">
                <table className="min-w-full text-xs text-slate-300">
                  <thead className="bg-slate-900/80 text-slate-400">
                    <tr>
                      {sqlOutput.columns.map((col) => (
                        <th key={col} className="px-3 py-2 text-left font-semibold">
                          {col}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {sqlOutput.rows.map((row, rowIndex) => (
                      <tr key={`row-${rowIndex}`} className="border-t border-slate-800">
                        {row.map((cell, cellIndex) => (
                          <td key={`cell-${rowIndex}-${cellIndex}`} className="px-3 py-2">
                            {cell === null || cell === undefined ? '—' : String(cell)}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : (
            <p className="mt-2 text-sm text-slate-400">
              No output yet. Run and log a query to capture sample results.
            </p>
          )}
        </div>

        <div className="glass-panel panel-sheen rounded-2xl p-5">
          <p className="border-l-[3px] border-[#F3701B] pl-2 text-xs font-semibold uppercase tracking-wide text-slate-400">
            SQL Query Log
          </p>
          {queryLogs.data?.length ? (
            <div className="mt-3 space-y-3">
              {queryLogs.data.map((log) => (
                <div key={log.created_at} className="rounded-xl bg-slate-950/60 p-3">
                  <div className="flex flex-wrap items-center justify-between text-xs text-slate-400">
                    <span>{log.purpose}</span>
                    <span>{new Date(log.created_at).toLocaleString()}</span>
                  </div>
                  <p className="mt-2 text-xs text-slate-300">{log.result_summary}</p>
                  <details className="mt-2">
                    <summary className="cursor-pointer text-xs font-semibold text-slate-300">
                      Prompt + Draft SQL
                    </summary>
                    <p className="mt-2 whitespace-pre-wrap text-xs text-slate-400">
                      {log.prompt_text}
                    </p>
                    <pre className="mt-2 whitespace-pre-wrap text-xs text-slate-400">
                      {log.draft_sql}
                    </pre>
                  </details>
                  <p className="mt-3 text-xs font-semibold text-slate-300">Final SQL</p>
                  <pre className="mt-2 whitespace-pre-wrap text-xs text-slate-400">
                    {log.final_sql}
                  </pre>
                </div>
              ))}
            </div>
          ) : (
            <p className="mt-2 text-sm text-slate-400">
              No query logs yet. Use the SQL assistant to log your analysis.
            </p>
          )}
        </div>

        <div className="glass-panel panel-sheen rounded-2xl p-5">
          <p className="border-l-[3px] border-[#53B848] pl-2 text-xs font-semibold uppercase tracking-wide text-slate-400">Timeline</p>
          {timeline.data?.length ? (
            <div className="mt-3 space-y-0">
              {timeline.data.map((item, idx) => (
                <div key={`${item.event_type}-${item.created_at}`} className="flex gap-3">
                  {/* vertical connector */}
                  <div className="flex flex-col items-center">
                    <div className="mt-1 h-2.5 w-2.5 rounded-full bg-[#53B848]" />
                    {idx < timeline.data!.length - 1 && (
                      <div className="w-0.5 flex-1 bg-slate-700" style={{ minHeight: '32px' }} />
                    )}
                  </div>
                  {/* content */}
                  <div className="pb-4 text-sm text-slate-300">
                    <p className="text-xs font-semibold text-slate-300">{item.event_type}</p>
                    <p>{item.event_detail}</p>
                    <p className="text-xs text-slate-500">
                      {new Date(item.created_at).toLocaleString()}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="mt-2 text-sm text-slate-400">No timeline events yet.</p>
          )}
        </div>
      </div>
    </div>
  );
};

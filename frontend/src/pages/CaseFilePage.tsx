import { useEffect, useMemo, useState } from 'react';
import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';
import { AuditEntry, CaseStatus } from '../types/risk';
import { useCaseDetailByPlayer } from '../hooks/useRiskCases';
import { useAnalystNotes, useSubmitAnalystNotes } from '../hooks/useAnalystNotes';
import { usePromptLogs } from '../hooks/useAi';
import { useCaseTimeline, useSubmitCase } from '../hooks/useCaseTimeline';
import { useCreateQueryLog, useQueryLog } from '../hooks/useQueryLog';
import { useQueryDraft } from '../hooks/useQueryDraft';
import { PromptLogPanel } from '../components/PromptLogPanel';
import { RISK_STYLES } from '../styles/theme';
import { useQueryClient } from '@tanstack/react-query';

interface CaseFilePageProps {
  entry: AuditEntry;
  status: CaseStatus;
  onBack: () => void;
}

const ACTION_OPTIONS = [
  'Provide Responsible Gaming Resources (RG Center)',
  'Offer Player Limits (Deposit/Wager/Time)',
  'Offer Cool Off Period',
  'Offer Self-Exclusion',
  'Monitor & Document'
];

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

export const CaseFilePage = ({ entry, status, onBack }: CaseFilePageProps) => {
  const { data: detail } = useCaseDetailByPlayer(entry.player_id);
  const notesQuery = useAnalystNotes(entry.player_id);
  const submitNotes = useSubmitAnalystNotes();
  const submitCase = useSubmitCase();
  const promptLogs = usePromptLogs(entry.player_id);
  const queryLogs = useQueryLog(entry.player_id);
  const timeline = useCaseTimeline(entry.player_id);
  const queryDraft = useQueryDraft();
  const createQueryLog = useCreateQueryLog();
  const reactQuery = useQueryClient();

  const [notes, setNotes] = useState('');
  const [action, setAction] = useState('');
  const [prompt, setPrompt] = useState('');
  const [draftSql, setDraftSql] = useState('');
  const [finalSql, setFinalSql] = useState('');
  const [purpose, setPurpose] = useState('');
  const [resultSummary, setResultSummary] = useState('');

  useEffect(() => {
    if (notesQuery.data) {
      setNotes(notesQuery.data.analyst_notes);
      setAction(notesQuery.data.analyst_action);
    }
  }, [notesQuery.data]);

  useEffect(() => {
    if (queryDraft.data?.draft_sql) {
      setDraftSql(queryDraft.data.draft_sql);
      setFinalSql(queryDraft.data.draft_sql);
    }
  }, [queryDraft.data]);

  const isInProgress = status === 'IN_PROGRESS';
  const isSubmitted = status === 'SUBMITTED';

  const canSubmitNotes = notes.trim().length >= 10 && action.length > 0;
  const canSubmitDecision = isInProgress && canSubmitNotes;
  const canLogQuery =
    prompt.trim().length >= 10 &&
    finalSql.trim().length >= 10 &&
    purpose.trim().length >= 5 &&
    resultSummary.trim().length >= 5;

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

  const handleDraftSql = () => {
    if (!isInProgress) {
      return;
    }
    queryDraft.mutate({ player_id: entry.player_id, analyst_prompt: prompt.trim() });
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
        result_summary: resultSummary.trim()
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
    const ensurePage = (neededHeight: number, curY: number, pageNum: { n: number }, subtitle?: string): number => {
      if (curY + neededHeight > pageHeight - 50) {
        addFooter(pageNum.n);
        pdf.addPage();
        pageNum.n++;
        totalPages = pageNum.n;
        addPageHeader(false, subtitle);
        return subtitle ? 72 : 72;
      }
      return curY;
    };

    // ────────────────────────────────────────────────────────────────────
    // PAGE 1 — Main report
    // ────────────────────────────────────────────────────────────────────
    const pageNum = { n: 1 };
    addPageHeader(true);

    // ── Case Identification Block ─────────────────────────────────────
    let cursorY = 100;

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

    // ── AI Transparency ───────────────────────────────────────────────
    cursorY = ensurePage(100, cursorY, pageNum);
    cursorY = addSectionTitle('AI Transparency', cursorY);
    const aiLog = promptLogs.data?.[0];
    if (aiLog) {
      pdf.setFont('helvetica', 'bold');
      pdf.setFontSize(8);
      pdf.setTextColor(...DARK_GRAY);
      pdf.text('Prompt', margin, cursorY);
      cursorY += 12;
      cursorY = writeParagraph(aiLog.prompt_text, cursorY);
      cursorY += 8;
      pdf.setFont('helvetica', 'bold');
      pdf.setFontSize(8);
      pdf.setTextColor(...DARK_GRAY);
      pdf.text('AI Draft Response', margin, cursorY);
      cursorY += 12;
      cursorY = writeParagraph(aiLog.response_text, cursorY);
    } else {
      cursorY = writeParagraph('No AI drafts logged yet.', cursorY);
    }
    cursorY += 20;

    // ── SQL Evidence Summary ──────────────────────────────────────────
    cursorY = ensurePage(120, cursorY, pageNum);
    cursorY = addSectionTitle('SQL Evidence Summary', cursorY);

    if (!queryLogs.data?.length) {
      cursorY = writeParagraph('No SQL evidence logged yet.', cursorY);
      cursorY += 12;
    } else {
      autoTable(pdf, {
        startY: cursorY,
        head: [['Purpose', 'Summary', 'Timestamp']],
        body: (queryLogs.data ?? []).map((log) => [
          log.purpose,
          log.result_summary,
          formatTimestamp(log.created_at)
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
        margin: { left: margin, right: margin }
      });

      cursorY = (pdf as any).lastAutoTable.finalY + 24;
    }

    // ── Case Timeline ─────────────────────────────────────────────────
    cursorY = ensurePage(120, cursorY, pageNum);
    cursorY = addSectionTitle('Case Timeline', cursorY);

    if (!timeline.data?.length) {
      cursorY = writeParagraph('No timeline entries available yet.', cursorY);
      cursorY += 12;
    } else {
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
        margin: { left: margin, right: margin }
      });
    }

    // Footer on last body page
    addFooter(pageNum.n);

    // ────────────────────────────────────────────────────────────────────
    // APPENDIX PAGE(S)
    // ────────────────────────────────────────────────────────────────────
    pdf.addPage();
    pageNum.n++;
    totalPages = pageNum.n;
    addPageHeader(false, 'Appendix — SQL Drafts & Prompts');
    cursorY = 78;

    if (queryLogs.data?.length) {
      queryLogs.data.forEach((log, index) => {
        cursorY = ensurePage(160, cursorY, pageNum, 'Appendix — SQL Drafts & Prompts');

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

        // Draft SQL — code block
        pdf.setFont('helvetica', 'bold');
        pdf.setFontSize(8);
        pdf.setTextColor(...DARK_GRAY);
        pdf.text('Draft SQL', margin, cursorY);
        cursorY += 14;

        const draftLines = pdf.splitTextToSize(log.draft_sql, contentWidth - 24);
        const codeBlockH = draftLines.length * 11 + 16;
        pdf.setFillColor(...LIGHT_GRAY);
        pdf.roundedRect(margin, cursorY - 4, contentWidth, codeBlockH, 3, 3, 'F');
        pdf.setFont('courier', 'normal');
        pdf.setFontSize(7.5);
        pdf.setTextColor(...DARK_NAVY);
        pdf.text(draftLines, margin + 12, cursorY + 6);
        cursorY += codeBlockH + 10;

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
        cursorY += finalBlockH + 20;
      });
    } else {
      cursorY = ensurePage(60, cursorY, pageNum, 'Appendix — SQL Drafts & Prompts');
      writeParagraph('No SQL queries logged for this case.', cursorY);
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

        <div className="glass-panel panel-sheen rounded-2xl p-5">
          <p className="border-l-[3px] border-[#F3701B] pl-2 text-xs font-semibold uppercase tracking-wide text-slate-400">
            Evidence Snapshot
          </p>
          {detail ? (
            <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              <div className="rounded-xl bg-slate-950/60 p-3">
                <p className="text-xs text-slate-400">Total Bets (7d)</p>
                <p className="text-lg font-semibold text-slate-100">
                  {detail.evidence_snapshot.total_bets_7d}
                </p>
              </div>
              <div className="rounded-xl bg-slate-950/60 p-3">
                <p className="text-xs text-slate-400">Total Wagered (7d)</p>
                <p className="text-lg font-semibold text-slate-100">
                  ${detail.evidence_snapshot.total_wagered_7d.toLocaleString()}
                </p>
              </div>
              <div className="rounded-xl bg-slate-950/60 p-3">
                <p className="text-xs text-slate-400">Loss Chase Score</p>
                <p className={`text-lg font-semibold ${detail.evidence_snapshot.loss_chase_score >= 0.8 ? 'text-red-400' : detail.evidence_snapshot.loss_chase_score >= 0.6 ? 'text-[#F3701B]' : 'text-slate-100'}`}>
                  {(detail.evidence_snapshot.loss_chase_score * 100).toFixed(0)}%
                </p>
              </div>
              <div className="rounded-xl bg-slate-950/60 p-3">
                <p className="text-xs text-slate-400">Bet Escalation</p>
                <p className={`text-lg font-semibold ${detail.evidence_snapshot.bet_escalation_score >= 0.8 ? 'text-red-400' : detail.evidence_snapshot.bet_escalation_score >= 0.6 ? 'text-[#F3701B]' : 'text-slate-100'}`}>
                  {(detail.evidence_snapshot.bet_escalation_score * 100).toFixed(0)}%
                </p>
              </div>
              <div className="rounded-xl bg-slate-950/60 p-3">
                <p className="text-xs text-slate-400">Market Drift</p>
                <p className={`text-lg font-semibold ${detail.evidence_snapshot.market_drift_score >= 0.8 ? 'text-red-400' : detail.evidence_snapshot.market_drift_score >= 0.6 ? 'text-[#F3701B]' : 'text-slate-100'}`}>
                  {(detail.evidence_snapshot.market_drift_score * 100).toFixed(0)}%
                </p>
              </div>
              <div className="rounded-xl bg-slate-950/60 p-3">
                <p className="text-xs text-slate-400">Temporal Risk</p>
                <p className={`text-lg font-semibold ${detail.evidence_snapshot.temporal_risk_score >= 0.8 ? 'text-red-400' : detail.evidence_snapshot.temporal_risk_score >= 0.6 ? 'text-[#F3701B]' : 'text-slate-100'}`}>
                  {(detail.evidence_snapshot.temporal_risk_score * 100).toFixed(0)}%
                </p>
              </div>
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
              {ACTION_OPTIONS.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
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
          </div>
        </div>

        <PromptLogPanel logs={promptLogs.data ?? []} />

        <div className="glass-panel panel-sheen rounded-2xl p-5">
          <p className="border-l-[3px] border-[#F3701B] pl-2 text-xs font-semibold uppercase tracking-wide text-slate-400">
            SQL Assistant
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
                  placeholder="Summarize findings from running the query"
                />
              </div>
              <button
                type="button"
                onClick={handleLogQuery}
                disabled={!isInProgress || !canLogQuery || createQueryLog.isPending}
                className="hover-lift rounded-xl border border-slate-700 bg-[#53B848] px-4 py-2 text-xs font-semibold uppercase tracking-wide text-black disabled:cursor-not-allowed disabled:bg-slate-700 disabled:text-slate-400"
              >
                {createQueryLog.isPending ? 'Logging...' : 'Confirm & Log'}
              </button>
            </div>
          </div>
          <p className="mt-2 text-xs text-slate-400">
            SQL drafts are assistive only. Analyst review is required before logging.
          </p>
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

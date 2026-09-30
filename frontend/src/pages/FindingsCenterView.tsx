import React, { useState } from 'react';
import {
  CheckCircle,
  ShieldCheck,
  X,
  MessageSquare,
  FileCheck,
  Info,
  ChevronRight,
  ChevronLeft,
  Download,
  ZoomIn,
  ZoomOut,
  Maximize,
  Minimize,
  Eye,
  EyeOff,
  FileText,
  Lock,
  Columns,
  Layers,
  ExternalLink,
} from 'lucide-react';
import {
  OfficerFinding,
  FindingReviewStatus,
  FindingSeverity,
  BidderApplicationDocument,
} from '../types';
import { DEMO_FINDINGS, DEMO_BIDDER_APPLICATION } from '../api/demoData';

interface FindingsCenterViewProps {
  findings: OfficerFinding[];
  onRefreshFindings: () => void;
}

// Structured Evidence Configuration mapping findings to real submitted files and exact pages
interface FindingEvidenceConfig {
  findingId: string;
  requirementId: string;
  clause: string;
  requirementText: string;
  defaultDocId: string;
  defaultDocFile: string;
  defaultPage: number;
  evidenceItems: Array<{
    label: string;
    docId: string;
    fileName: string;
    page: number;
    description: string;
  }>;
  verificationMethod: string;
  verificationOutcome: string;
  extractedValues: Array<{ label: string; value: string }>;
  varianceHighlight?: string;
}

const FINDING_EVIDENCE_MAP: Record<string, FindingEvidenceConfig> = {
  'FND-01': {
    findingId: 'FND-01',
    requirementId: 'REQ-CAG-07',
    clause: 'Annexure-2, Clause 2(d)(ii) (Page 3 & 14)',
    requirementText:
      'Mandatory notarized affidavit on non-judicial stamp paper confirming non-deployment of personnel with criminal antecedents in VVIP/sensitive areas.',
    defaultDocId: 'doc-05',
    defaultDocFile: '05_Statutory_Affidavits_and_Compliance_Undertakings.pdf',
    defaultPage: 1,
    evidenceItems: [
      {
        label: 'Inspect Submitted Affidavits (Page 1)',
        docId: 'doc-05',
        fileName: '05_Statutory_Affidavits_and_Compliance_Undertakings.pdf',
        page: 1,
        description:
          'Document 05 contains Annexure-7 (Terms), Annexure-8 (Non-conviction), and Annexure-10; Annexure-9 VVIP Affidavit is completely omitted.',
      },
    ],
    verificationMethod: 'Mandatory checklist document presence audit',
    verificationOutcome: 'EVIDENCE_MISSING',
    extractedValues: [
      { label: 'Expected Document', value: 'Annexure-9 Notarized VVIP Security Clearance Affidavit' },
      { label: 'Submitted Dossier', value: 'Annexures 7, 8, and 10 present; Annexure-9 NOT FOUND' },
    ],
    varianceHighlight: 'Mandatory statutory document missing: Annexure-9 not uploaded in application package',
  },
  'FND-02': {
    findingId: 'FND-02',
    requirementId: 'REQ-CAG-04',
    clause: 'Bid Data Sheet & Clause 2(e) (Page 1 & 4)',
    requirementText:
      'Minimum Average Annual Financial Turnover of Rs. 357.0 Lakhs in manpower services over FY 2017-18, 2018-19, and 2019-20, certified by CA with UDIN.',
    defaultDocId: 'doc-03',
    defaultDocFile: '03_Financial_Turnover_and_Audited_Statements.pdf',
    defaultPage: 1,
    evidenceItems: [
      {
        label: 'Open CA Evidence (Page 1)',
        docId: 'doc-03',
        fileName: '03_Financial_Turnover_and_Audited_Statements.pdf',
        page: 1,
        description:
          'CA Turnover Certificate (UDIN: 21543892BG1128) certifying FY 19-20 turnover as ₹6,20,50,000/- (Avg ₹5.06 Cr).',
      },
      {
        label: 'Open Audited Evidence (Page 2)',
        docId: 'doc-03',
        fileName: '03_Financial_Turnover_and_Audited_Statements.pdf',
        page: 2,
        description:
          'Audited P&L Schedule III reporting FY 19-20 Revenue from Operations as ₹5,40,35,000/-.',
      },
    ],
    verificationMethod: 'Cross-document reconciliation of CA Certificate vs Audited P&L',
    verificationOutcome: 'PARTIAL',
    extractedValues: [
      { label: 'CA Certificate FY 19-20', value: '₹6,20,50,000 (₹6.20 Cr) — UDIN 21543892BG1128' },
      { label: 'Audited P&L FY 19-20', value: '₹5,40,35,000 (₹5.40 Cr) — Schedule III' },
      { label: 'Unexplained Variance', value: '₹80,15,000 (₹80.15 Lakhs)' },
    ],
    varianceHighlight: '₹80.15 Lakhs unexplained variance between CA Certificate and Audited Financial Statement',
  },
  'FND-03': {
    findingId: 'FND-03',
    requirementId: 'REQ-CAG-06',
    clause: 'Bid Data Sheet Page 2, Clause 4',
    requirementText:
      'Executed at least 1 order of 80% (₹5.71 Cr) OR 2 orders of 50% (₹3.57 Cr) OR 3 orders of 40% (₹2.85 Cr) with client completion certificates.',
    defaultDocId: 'doc-04',
    defaultDocFile: '04_Past_Experience_Work_Orders_and_Completion.pdf',
    defaultPage: 2,
    evidenceItems: [
      {
        label: 'Open Projects 1 & 2 (Page 1)',
        docId: 'doc-04',
        fileName: '04_Past_Experience_Work_Orders_and_Completion.pdf',
        page: 1,
        description:
          'Project 1: CBDT ₹3.82 Cr (Completed) · Project 2: DPIIT ₹2.95 Cr (Completed) — Satisfactory completion certificates attached.',
      },
      {
        label: 'Open Project 3 SAIL Order (Page 2)',
        docId: 'doc-04',
        fileName: '04_Past_Experience_Work_Orders_and_Completion.pdf',
        page: 2,
        description:
          'Project 3: SAIL ₹1.90 Cr accompanied only by interim performance letter; final completion certificate missing.',
      },
    ],
    verificationMethod: 'Numerical threshold verification and completion certificate audit',
    verificationOutcome: 'PARTIAL',
    extractedValues: [
      { label: 'Project 1 (CBDT)', value: '₹3,82,40,000 (Pass — Exceeds ₹3.57 Cr threshold)' },
      { label: 'Project 2 (DPIIT)', value: '₹2,95,10,000 (Pass — Exceeds ₹2.85 Cr threshold)' },
      { label: 'Project 3 (SAIL)', value: '₹1,90,00,000 (Fails — Below ₹2.85 Cr threshold)' },
      { label: 'Completion Certificate 3', value: 'NOT FOUND (Interim letter only)' },
    ],
    varianceHighlight: 'Order shortfall of ₹95 Lakhs on Project 3 and missing final completion certificate',
  },
  'FND-04': {
    findingId: 'FND-04',
    requirementId: 'REQ-CAG-10',
    clause: 'Annexure-5 Technical Specifications (Page 5)',
    requirementText:
      'Clerical/Non-Technical Graduate personnel must demonstrate minimum 15,000 key depressions/hour typing speed.',
    defaultDocId: 'doc-05',
    defaultDocFile: '05_Statutory_Affidavits_and_Compliance_Undertakings.pdf',
    defaultPage: 2,
    evidenceItems: [
      {
        label: 'Open Typing Self-Declaration (Doc 05, Page 2)',
        docId: 'doc-05',
        fileName: '05_Statutory_Affidavits_and_Compliance_Undertakings.pdf',
        page: 2,
        description:
          'Internal company self-declaration asserting staff capability without third-party skill test logs or accredited typing institute certification.',
      },
      {
        label: 'Open Bid Form Checklist (Doc 01, Page 2)',
        docId: 'doc-01',
        fileName: '01_Bid_Submission_and_Technical_Bid_Form.pdf',
        page: 2,
        description: 'Technical Bid Form checklist citing internal qualification standards.',
      },
    ],
    verificationMethod: 'Technical qualification evidence audit',
    verificationOutcome: 'INSUFFICIENT_DATA / NOT_VERIFIABLE',
    extractedValues: [
      { label: 'Tender Requirement', value: '15,000 key depressions/hour proficiency' },
      { label: 'Submitted Evidence', value: 'Internal company self-declaration' },
      { label: 'Empirical Test Logs', value: 'NOT ATTACHED' },
    ],
    varianceHighlight: 'Technical ambiguity: Unverified empirical capability (lacks third-party test verification logs)',
  },
  'FND-05': {
    findingId: 'FND-05',
    requirementId: 'REQ-CAG-01 / REQ-CAG-03',
    clause: 'Annexure-2, Clause 2(a) & 2(b) (Page 3 & 4)',
    requirementText:
      'Legal entity registration continuity and statutory tax registrations under PAN and GST.',
    defaultDocId: 'doc-02',
    defaultDocFile: '02_Company_Incorporation_and_Statutory_Registrations.pdf',
    defaultPage: 1,
    evidenceItems: [
      {
        label: 'Open Incorporation Certificate (Page 1)',
        docId: 'doc-02',
        fileName: '02_Company_Incorporation_and_Statutory_Registrations.pdf',
        page: 1,
        description:
          'RoC Certificate: "Aravind Integrated Solutions Private Limited" (CIN: U74999DL2016PTC301429).',
      },
      {
        label: 'Open Tax Registration (Page 2)',
        docId: 'doc-02',
        fileName: '02_Company_Incorporation_and_Statutory_Registrations.pdf',
        page: 2,
        description:
          'GST REG-06: "Aravind Integrated Solutions Pvt. Ltd." (GSTIN: 07AAACA9182K1Z5, PAN: AAACA9182K).',
      },
    ],
    verificationMethod: 'Statutory code syntax and documentary verification',
    verificationOutcome: 'COMPLIANT',
    extractedValues: [
      { label: 'Incorporation Legal Name', value: 'Aravind Integrated Solutions Private Limited' },
      { label: 'Tax Registration Trade Name', value: 'Aravind Integrated Solutions Pvt. Ltd.' },
      { label: 'PAN Verification', value: 'AAACA9182K (Matches identically on both records)' },
    ],
    varianceHighlight: 'Acceptable legal abbreviation; entity identity and PAN continuity confirmed',
  },
};

export const FindingsCenterView: React.FC<FindingsCenterViewProps> = ({
  findings,
  onRefreshFindings: _onRefreshFindings,
}) => {
  const [activeFindings, setActiveFindings] = useState<OfficerFinding[]>(
    findings.length > 0 ? findings : DEMO_FINDINGS
  );
  // Default to FND-02 for immediate evidence-first review workspace
  const [activeFindingId, setActiveFindingId] = useState<string>('FND-02');
  const [viewMode, setViewMode] = useState<'WORKSPACE' | 'CARDS'>('WORKSPACE');

  // Documents submitted by bidder
  const documents: BidderApplicationDocument[] = DEMO_BIDDER_APPLICATION.documents;
  const initialDoc = documents.find((d) => d.id === 'doc-03') || documents[0];
  const [activeDocumentId, setActiveDocumentId] = useState<string>(initialDoc.id);
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [zoomLevel, setZoomLevel] = useState<number>(100);

  // Layout hide/show toggles
  const [isFindingPanelVisible, setIsFindingPanelVisible] = useState<boolean>(true);
  const [isDocListVisible, setIsDocListVisible] = useState<boolean>(true);
  const [isFullScreen, setIsFullScreen] = useState<boolean>(false);

  // Action Modals
  const [selectedFindingForAction, setSelectedFindingForAction] = useState<OfficerFinding | null>(null);
  const [actionModalType, setActionModalType] = useState<'REVIEW' | 'CLARIFICATION' | 'NOTE' | null>(null);
  const [noteText, setNoteText] = useState('');
  const [clarificationQuery, setClarificationQuery] = useState('');
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  // Filters for findings
  const [severityFilter, setSeverityFilter] = useState<string>('ALL');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [appFilter, setAppFilter] = useState<string>('ALL');

  const filteredFindings = activeFindings.filter((f) => {
    const matchesSeverity = severityFilter === 'ALL' || f.severity === severityFilter;
    const matchesStatus = statusFilter === 'ALL' || f.review_status === statusFilter;
    const matchesApp = appFilter === 'ALL' || f.application_id === appFilter || f.applicationId === appFilter;
    return matchesSeverity && matchesStatus && matchesApp;
  });

  const activeFinding =
    activeFindings.find((f) => f.id === activeFindingId) || activeFindings[0] || DEMO_FINDINGS[0];
  const activeEvidenceConfig = FINDING_EVIDENCE_MAP[activeFinding.id] || FINDING_EVIDENCE_MAP['FND-02'];
  const activeDocument =
    documents.find((d) => d.id === activeDocumentId) ||
    documents.find((d) => d.file_name === activeEvidenceConfig.defaultDocFile) ||
    documents[0];

  const totalPages = activeDocument.pages || 2;

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3500);
  };

  // Switch active finding and automatically jump to its primary source evidence document & page
  const handleSelectFinding = (findingId: string) => {
    setActiveFindingId(findingId);
    const config = FINDING_EVIDENCE_MAP[findingId];
    if (config) {
      setActiveDocumentId(config.defaultDocId);
      setCurrentPage(config.defaultPage);
    }
  };

  // Jump to specific evidence item (document + page)
  const handleJumpToEvidence = (docId: string, page: number) => {
    setActiveDocumentId(docId);
    setCurrentPage(page);
    showToast(`Navigated viewer to ${page > 1 ? `Page ${page}` : 'primary evidence'}`);
  };

  // Page controls
  const handlePrevPage = () => {
    setCurrentPage((prev) => Math.max(1, prev - 1));
  };

  const handleNextPage = () => {
    setCurrentPage((prev) => Math.min(totalPages, prev + 1));
  };

  // Zoom controls
  const handleZoomIn = () => {
    setZoomLevel((prev) => Math.min(180, prev + 20));
  };

  const handleZoomOut = () => {
    setZoomLevel((prev) => Math.max(60, prev - 20));
  };

  const handleFitWidth = () => {
    setZoomLevel(100);
  };

  // Open action modal
  const handleOpenAction = (finding: OfficerFinding, type: 'REVIEW' | 'CLARIFICATION' | 'NOTE') => {
    setSelectedFindingForAction(finding);
    setActionModalType(type);
    setNoteText(finding.officer_notes || '');
    setClarificationQuery(
      type === 'CLARIFICATION'
        ? `Clarification Notice under GFR Rule 144: Please provide formal Chartered Accountant reconciliation and audited supporting documents regarding ${finding.title}.`
        : ''
    );
  };

  const handleSaveAction = () => {
    if (!selectedFindingForAction) return;

    if (actionModalType === 'REVIEW') {
      const updated = activeFindings.map((f) =>
        f.id === selectedFindingForAction.id
          ? {
              ...f,
              review_status: 'ACCEPTED' as FindingReviewStatus,
              officer_notes: noteText || f.officer_notes,
            }
          : f
      );
      setActiveFindings(updated);
      showToast(`Finding ${selectedFindingForAction.id} reviewed and marked as ACCEPTED.`);
    } else if (actionModalType === 'CLARIFICATION') {
      const updated = activeFindings.map((f) =>
        f.id === selectedFindingForAction.id
          ? {
              ...f,
              review_status: 'CLARIFICATION_REQUESTED' as FindingReviewStatus,
              officer_notes: `Clarification dispatched: ${clarificationQuery}`,
            }
          : f
      );
      setActiveFindings(updated);
      showToast(`Clarification request notice registered for ${selectedFindingForAction.id}.`);
    } else if (actionModalType === 'NOTE') {
      const updated = activeFindings.map((f) =>
        f.id === selectedFindingForAction.id ? { ...f, officer_notes: noteText } : f
      );
      setActiveFindings(updated);
      showToast(`Officer audit note recorded for ${selectedFindingForAction.id}.`);
    }

    setActionModalType(null);
    setSelectedFindingForAction(null);
  };

  const getSeverityBadge = (severity: FindingSeverity) => {
    switch (severity) {
      case 'CRITICAL':
        return <span className="badge badge-noncompliant">CRITICAL</span>;
      case 'HIGH':
        return <span className="badge badge-noncompliant">HIGH</span>;
      case 'MEDIUM':
        return <span className="badge badge-partial">MEDIUM</span>;
      case 'LOW':
      default:
        return <span className="badge badge-blue">LOW</span>;
    }
  };

  const getStatusBadge = (status: FindingReviewStatus) => {
    switch (status) {
      case 'ACCEPTED':
        return <span className="badge badge-compliant">ACCEPTED / REVIEWED</span>;
      case 'CLARIFICATION_REQUESTED':
        return <span className="badge badge-clarification">CLARIFICATION REQUESTED</span>;
      case 'OVERRIDDEN':
        return <span className="badge badge-review">OVERRIDDEN</span>;
      case 'PENDING':
      default:
        return <span className="badge badge-partial">OPEN / PENDING</span>;
    }
  };

  // Determine grid columns class based on toggle states
  let gridColsClass = 'cols-3';
  if (!isDocListVisible && isFindingPanelVisible) {
    gridColsClass = 'cols-center-right';
  } else if (isDocListVisible && !isFindingPanelVisible) {
    gridColsClass = 'cols-left-center';
  } else if (!isDocListVisible && !isFindingPanelVisible) {
    gridColsClass = 'cols-center-only';
  }

  // Direct download URL for immutable applicant source file
  const downloadFileUrl = `/demo_documents/${activeDocument.file_name}`;

  return (
    <div className="evidence-workspace-container">
      {/* Header bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <span className="badge badge-noncompliant">Risk & Discrepancy Findings</span>
            <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
              Evidence-First Procurement Review Workspace
            </span>
          </div>
          <h1 style={{ fontSize: '1.45rem', fontWeight: 800, color: 'var(--text-primary)', letterSpacing: '-0.02em' }}>
            Risk & Findings Center
          </h1>
          <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
            Analytical discrepancies and omissions mapped directly to applicant-submitted source documents.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          {/* View Mode Switcher */}
          <div
            style={{
              display: 'flex',
              background: 'var(--bg-tertiary)',
              padding: '3px',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border-subtle)',
            }}
          >
            <button
              onClick={() => setViewMode('WORKSPACE')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '6px 12px',
                borderRadius: '6px',
                background: viewMode === 'WORKSPACE' ? 'var(--brand-blue)' : 'transparent',
                color: viewMode === 'WORKSPACE' ? '#ffffff' : 'var(--text-secondary)',
                border: 'none',
                cursor: 'pointer',
                fontSize: '0.76rem',
                fontWeight: 600,
                transition: 'all 0.15s ease',
              }}
            >
              <Columns size={14} /> Evidence Workspace
            </button>
            <button
              onClick={() => setViewMode('CARDS')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '6px 12px',
                borderRadius: '6px',
                background: viewMode === 'CARDS' ? 'var(--brand-blue)' : 'transparent',
                color: viewMode === 'CARDS' ? '#ffffff' : 'var(--text-secondary)',
                border: 'none',
                cursor: 'pointer',
                fontSize: '0.76rem',
                fontWeight: 600,
                transition: 'all 0.15s ease',
              }}
            >
              <Layers size={14} /> All Findings Cards ({activeFindings.length})
            </button>
          </div>

          <div
            style={{
              fontSize: '0.8rem',
              color: 'var(--text-secondary)',
              background: 'rgba(255,255,255,0.04)',
              padding: '6px 14px',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border-subtle)',
            }}
          >
            Officer Safeguard: <strong style={{ color: '#10b981' }}>Findings Require Officer Ruling</strong>
          </div>
        </div>
      </div>

      {toastMessage && (
        <div
          style={{
            background: 'rgba(16, 185, 129, 0.15)',
            border: '1px solid rgba(16, 185, 129, 0.35)',
            color: '#34d399',
            padding: '10px 16px',
            borderRadius: 'var(--radius-md)',
            fontSize: '0.82rem',
            fontWeight: 600,
          }}
        >
          ✓ {toastMessage}
        </div>
      )}

      {/* Canonical Context Banner */}
      <div
        className="glass-card"
        style={{
          padding: '14px 20px',
          background: '#eff6ff', border: '1px solid #bfdbfe',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '14px',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Tender:
            </span>
            <span style={{ fontSize: '0.82rem', fontWeight: 700, color: '#60a5fa', fontFamily: 'var(--font-mono)' }}>
              GEM/2021/B/1128240
            </span>
          </div>
          <div style={{ fontSize: '0.88rem', color: 'var(--text-primary)', fontWeight: 700 }}>
            Bidder Application: <span style={{ color: 'var(--brand-cyan)' }}>Aravind Integrated Solutions Private Limited (DEMO)</span>{' '}
            <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>(APP-001)</span>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div
            style={{
              background: 'var(--bg-tertiary)',
              padding: '6px 14px',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--border-subtle)',
              fontSize: '0.8rem',
              fontWeight: 700,
              color: '#34d399',
            }}
          >
            1 Application · 6 Documents · 5 Findings
          </div>
        </div>
      </div>

      {/* Finding Filter Bar */}
      <div
        className="glass-card"
        style={{
          padding: '10px 18px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '12px',
          background: 'var(--bg-card)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px', flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: 600 }}>Severity:</span>
            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              style={{
                background: 'var(--bg-tertiary)', color: 'var(--text-primary)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-sm)',
                padding: '4px 8px',
                fontSize: '0.76rem',
                outline: 'none',
                cursor: 'pointer',
              }}
            >
              <option value="ALL">All Severities (5)</option>
              <option value="CRITICAL">CRITICAL (1)</option>
              <option value="HIGH">HIGH (1)</option>
              <option value="MEDIUM">MEDIUM (1)</option>
              <option value="LOW">LOW (2)</option>
            </select>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: 600 }}>Status:</span>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              style={{
                background: 'var(--bg-tertiary)', color: 'var(--text-primary)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-sm)',
                padding: '4px 8px',
                fontSize: '0.76rem',
                outline: 'none',
                cursor: 'pointer',
              }}
            >
              <option value="ALL">All Statuses (5)</option>
              <option value="PENDING">PENDING (3)</option>
              <option value="CLARIFICATION_REQUESTED">CLARIFICATION REQUESTED (1)</option>
              <option value="ACCEPTED">ACCEPTED (1)</option>
            </select>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: 600 }}>Application:</span>
            <select
              value={appFilter}
              onChange={(e) => setAppFilter(e.target.value)}
              style={{
                background: 'var(--bg-tertiary)', color: 'var(--text-primary)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-sm)',
                padding: '4px 8px',
                fontSize: '0.76rem',
                outline: 'none',
                cursor: 'pointer',
              }}
            >
              <option value="ALL">Aravind Integrated Solutions Private Limited (DEMO) (5 Findings)</option>
            </select>
          </div>
        </div>

        <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
          Showing <strong>{filteredFindings.length}</strong> of 5 findings for this application
        </div>
      </div>

      {/* Non-Autonomous Notice */}
      <div
        style={{
          background: 'rgba(59, 130, 246, 0.08)',
          border: '1px solid rgba(59, 130, 246, 0.25)',
          borderRadius: 'var(--radius-md)',
          padding: '10px 16px',
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
        }}
      >
        <Info size={17} color="#60a5fa" style={{ flexShrink: 0 }} />
        <div style={{ fontSize: '0.76rem', color: '#93c5fd', lineHeight: 1.45 }}>
          <strong>Evidence-First Verification Principle:</strong> Findings are linked directly to original applicant-submitted PDF evidence. BidGuard does NOT compute a "bidder score" and does NOT rank bidders. The designated Procurement Officer makes all qualification determinations.
        </div>
      </div>

      {/* Finding Selector Tabs (Visible in Evidence Workspace) */}
      {viewMode === 'WORKSPACE' && (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            overflowX: 'auto',
            padding: '4px 0',
          }}
        >
          <span style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Target Finding:
          </span>
          {filteredFindings.map((f) => {
            const isSelected = f.id === activeFindingId;
            return (
              <button
                key={f.id}
                onClick={() => handleSelectFinding(f.id)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '7px 13px',
                  borderRadius: 'var(--radius-md)',
                  background: isSelected ? 'rgba(59, 130, 246, 0.2)' : 'rgba(255, 255, 255, 0.04)',
                  border: isSelected ? '1px solid var(--brand-blue)' : '1px solid var(--border-subtle)',
                  color: isSelected ? '#ffffff' : 'var(--text-secondary)',
                  cursor: 'pointer',
                  fontSize: '0.78rem',
                  fontWeight: isSelected ? 700 : 500,
                  transition: 'all 0.15s ease',
                  whiteSpace: 'nowrap',
                }}
              >
                <span
                  style={{
                    fontFamily: 'var(--font-mono)',
                    color: isSelected ? 'var(--brand-cyan)' : 'inherit',
                  }}
                >
                  {f.id}
                </span>
                <span>{f.id === 'FND-02' ? 'Financial Turnover Inconsistency' : f.id === 'FND-01' ? 'Annexure-9 Affidavit Omission' : f.id === 'FND-03' ? 'Experience Project 3 Shortfall' : f.id === 'FND-04' ? 'Typing Speed Ambiguity' : 'Entity Name Variation'}</span>
                {f.severity === 'CRITICAL' && (
                  <span style={{ background: '#ef4444', color: '#fff', fontSize: '0.62rem', padding: '1px 5px', borderRadius: '4px', fontWeight: 700 }}>
                    CRITICAL
                  </span>
                )}
                {f.severity === 'HIGH' && (
                  <span style={{ background: '#ef4444', color: '#fff', fontSize: '0.62rem', padding: '1px 5px', borderRadius: '4px', fontWeight: 700 }}>
                    HIGH
                  </span>
                )}
              </button>
            );
          })}
        </div>
      )}

      {/* VIEW 1: EVIDENCE-FIRST WORKSPACE (3 COLUMNS) */}
      {viewMode === 'WORKSPACE' && (
        <div className={`evidence-workspace-grid ${gridColsClass}`}>
          {/* COLUMN 1: APPLICATION DOCUMENTS LIST */}
          {isDocListVisible && (
            <div
              className="glass-card"
              style={{
                display: 'flex',
                flexDirection: 'column',
                padding: '16px',
                gap: '12px',
                overflowY: 'auto',
                maxHeight: 'calc(100vh - 240px)',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <h3 style={{ fontSize: '0.88rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                    Application Documents
                  </h3>
                  <p style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                    6 Submitted Files (16 Pages)
                  </p>
                </div>
                <button
                  onClick={() => setIsDocListVisible(false)}
                  title="Hide Evidence List"
                  aria-label="Hide Evidence List"
                  style={{
                    background: 'transparent',
                    border: 'none',
                    color: 'var(--text-muted)',
                    cursor: 'pointer',
                    padding: '4px',
                  }}
                >
                  <EyeOff size={15} />
                </button>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {documents.map((doc, idx) => {
                  const isDocActive = doc.id === activeDocument.id;
                  const isReferencedInActiveFinding =
                    doc.file_name === activeEvidenceConfig.defaultDocFile ||
                    activeEvidenceConfig.evidenceItems.some((e) => e.fileName === doc.file_name);

                  return (
                    <div
                      key={doc.id}
                      onClick={() => {
                        setActiveDocumentId(doc.id);
                        setCurrentPage(1);
                      }}
                      style={{
                        padding: '10px 12px',
                        borderRadius: 'var(--radius-sm)',
                        background: isDocActive
                          ? 'rgba(59, 130, 246, 0.18)'
                          : isReferencedInActiveFinding
                          ? 'rgba(59, 130, 246, 0.06)'
                          : 'rgba(255, 255, 255, 0.02)',
                        border: isDocActive
                          ? '1px solid var(--brand-blue)'
                          : isReferencedInActiveFinding
                          ? '1px solid rgba(59, 130, 246, 0.3)'
                          : '1px solid var(--border-subtle)',
                        cursor: 'pointer',
                        transition: 'all 0.15s ease',
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <FileText size={14} color={isDocActive ? 'var(--brand-cyan)' : 'var(--text-secondary)'} />
                          <span style={{ fontSize: '0.74rem', fontWeight: 700, color: isDocActive ? 'var(--brand-blue)' : 'var(--text-secondary)' }}>
                            0{idx + 1} {doc.title.split('&')[0]}
                          </span>
                        </div>
                        <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                          {doc.pages}p
                        </span>
                      </div>

                      <div style={{ fontSize: '0.66rem', color: 'var(--text-muted)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {doc.file_name}
                      </div>

                      {isReferencedInActiveFinding && (
                        <div style={{ marginTop: '6px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                          <span
                            style={{
                              fontSize: '0.62rem',
                              fontWeight: 700,
                              background: 'rgba(59, 130, 246, 0.25)',
                              color: '#93c5fd',
                              padding: '1px 6px',
                              borderRadius: '4px',
                            }}
                          >
                            ★ Target Evidence Source
                          </span>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* COLUMN 2: ORIGINAL APPLICANT-SUBMITTED DOCUMENT VIEWER */}
          <div
            className={`document-viewer-card ${isFullScreen ? 'document-viewer-fullscreen' : ''}`}
          >
            {/* Immutability Banner */}
            <div
              style={{
                background: '#f8fafc',
                padding: '6px 16px',
                borderBottom: '1px solid rgba(255, 255, 255, 0.06)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                fontSize: '0.7rem',
                color: 'var(--text-secondary)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Lock size={12} color="#10b981" />
                <span style={{ fontWeight: 700, color: '#34d399', letterSpacing: '0.04em' }}>
                  IMMUTABLE APPLICANT SUBMISSION
                </span>
                <span style={{ color: 'var(--text-muted)' }}>— Source Evidence (Read-Only)</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <span>Bidder: Aravind Integrated Solutions Pvt. Ltd.</span>
                {!isDocListVisible && (
                  <button
                    onClick={() => setIsDocListVisible(true)}
                    style={{
                      background: 'rgba(255,255,255,0.06)',
                      border: '1px solid var(--border-subtle)',
                      borderRadius: '4px',
                      color: 'var(--text-secondary)',
                      padding: '2px 8px',
                      cursor: 'pointer',
                      fontSize: '0.68rem',
                    }}
                  >
                    <Eye size={12} style={{ verticalAlign: 'middle', marginRight: '4px' }} />
                    Show Documents
                  </button>
                )}
                {!isFindingPanelVisible && (
                  <button
                    onClick={() => setIsFindingPanelVisible(true)}
                    style={{
                      background: 'rgba(59, 130, 246, 0.2)',
                      border: '1px solid rgba(59, 130, 246, 0.4)',
                      borderRadius: '4px',
                      color: '#93c5fd',
                      padding: '2px 8px',
                      cursor: 'pointer',
                      fontSize: '0.68rem',
                      fontWeight: 600,
                    }}
                  >
                    <Eye size={12} style={{ verticalAlign: 'middle', marginRight: '4px' }} />
                    Show Finding Panel
                  </button>
                )}
              </div>
            </div>

            {/* Document Controls Toolbar */}
            <div className="document-viewer-toolbar">
              {/* Document Title */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', minWidth: '220px' }}>
                <FileText size={16} color="var(--brand-cyan)" />
                <div>
                  <div style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-primary)', lineHeight: 1.2 }}>
                    {activeDocument.title}
                  </div>
                  <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                    {activeDocument.file_name}
                  </div>
                </div>
              </div>

              {/* Page Controls */}
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  background: 'var(--bg-tertiary)',
                  padding: '3px 8px',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--border-subtle)',
                }}
              >
                <button
                  onClick={handlePrevPage}
                  disabled={currentPage <= 1}
                  aria-label="Previous Page"
                  title="Previous Page"
                  style={{
                    background: 'transparent',
                    border: 'none',
                    color: currentPage <= 1 ? 'var(--text-muted)' : 'var(--text-primary)',
                    cursor: currentPage <= 1 ? 'not-allowed' : 'pointer',
                    padding: '3px',
                    display: 'flex',
                    alignItems: 'center',
                  }}
                >
                  <ChevronLeft size={16} />
                </button>
                <span style={{ fontSize: '0.74rem', color: 'var(--text-primary)', fontWeight: 600, minWidth: '70px', textAlign: 'center' }}>
                  Page {currentPage} of {totalPages}
                </span>
                <button
                  onClick={handleNextPage}
                  disabled={currentPage >= totalPages}
                  aria-label="Next Page"
                  title="Next Page"
                  style={{
                    background: 'transparent',
                    border: 'none',
                    color: currentPage >= totalPages ? 'var(--text-muted)' : 'var(--text-primary)',
                    cursor: currentPage >= totalPages ? 'not-allowed' : 'pointer',
                    padding: '3px',
                    display: 'flex',
                    alignItems: 'center',
                  }}
                >
                  <ChevronRight size={16} />
                </button>
              </div>

              {/* Zoom Controls */}
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  background: 'var(--bg-tertiary)',
                  padding: '3px 8px',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--border-subtle)',
                }}
              >
                <button
                  onClick={handleZoomOut}
                  aria-label="Zoom Out"
                  title="Zoom Out"
                  style={{
                    background: 'transparent',
                    border: 'none',
                    color: '#ffffff',
                    cursor: 'pointer',
                    padding: '3px',
                    display: 'flex',
                    alignItems: 'center',
                  }}
                >
                  <ZoomOut size={15} />
                </button>
                <span style={{ fontSize: '0.74rem', color: 'var(--text-secondary)', minWidth: '40px', textAlign: 'center' }}>
                  {zoomLevel}%
                </span>
                <button
                  onClick={handleZoomIn}
                  aria-label="Zoom In"
                  title="Zoom In"
                  style={{
                    background: 'transparent',
                    border: 'none',
                    color: '#ffffff',
                    cursor: 'pointer',
                    padding: '3px',
                    display: 'flex',
                    alignItems: 'center',
                  }}
                >
                  <ZoomIn size={15} />
                </button>
                <button
                  onClick={handleFitWidth}
                  aria-label="Fit Width"
                  title="Fit Width"
                  style={{
                    background: 'transparent',
                    border: 'none',
                    color: 'var(--text-secondary)',
                    cursor: 'pointer',
                    padding: '3px 6px',
                    fontSize: '0.72rem',
                    borderLeft: '1px solid var(--border-subtle)',
                  }}
                >
                  Fit
                </button>
              </div>

              {/* Fullscreen & Download Buttons */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <button
                  onClick={() => setIsFullScreen(!isFullScreen)}
                  aria-label={isFullScreen ? 'Exit Full Screen' : 'Full Screen'}
                  title={isFullScreen ? 'Exit Full Screen' : 'Full Screen'}
                  style={{
                    background: 'rgba(255, 255, 255, 0.05)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-sm)',
                    color: 'var(--text-secondary)',
                    cursor: 'pointer',
                    padding: '5px 9px',
                    fontSize: '0.74rem',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px',
                  }}
                >
                  {isFullScreen ? <Minimize size={14} /> : <Maximize size={14} />}
                  <span>{isFullScreen ? 'Exit' : 'Full Screen'}</span>
                </button>

                <a
                  href={downloadFileUrl}
                  download={activeDocument.file_name}
                  aria-label="Download Original File"
                  title="Download unmodified original applicant PDF"
                  className="btn btn-secondary"
                  style={{
                    fontSize: '0.74rem',
                    padding: '5px 12px',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '5px',
                    textDecoration: 'none',
                    color: '#ffffff',
                  }}
                >
                  <Download size={14} /> Download Original
                </a>
              </div>
            </div>

            {/* Quick Evidence Jump Pills for Target Finding */}
            {activeEvidenceConfig.evidenceItems && activeEvidenceConfig.evidenceItems.length > 0 && (
              <div
                style={{
                  background: '#f8fafc',
                  padding: '7px 16px',
                  borderBottom: '1px solid var(--border-subtle)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  flexWrap: 'wrap',
                }}
              >
                <span style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                  Cited Evidence Pages:
                </span>
                {activeEvidenceConfig.evidenceItems.map((item, idx) => {
                  const isCurrent =
                    activeDocument.file_name === item.fileName && currentPage === item.page;
                  return (
                    <button
                      key={idx}
                      onClick={() => handleJumpToEvidence(item.docId, item.page)}
                      className={`evidence-jump-pill ${isCurrent ? 'active' : ''}`}
                    >
                      <ExternalLink size={12} />
                      <span>{item.label}</span>
                    </button>
                  );
                })}
              </div>
            )}

            {/* Primary Center Document Viewport: Native PDF Embed */}
            <div className="doc-viewer-viewport-wrap">
              <iframe
                src={`/demo_documents/${activeDocument.file_name}#page=${currentPage}&zoom=${zoomLevel}`}
                className="pdf-iframe-viewport"
                title={`Original Applicant Submission - ${activeDocument.title}`}
              />
            </div>
          </div>

          {/* COLUMN 3: FINDING REPORT / VERIFICATION / OFFICER REVIEW PANEL */}
          {isFindingPanelVisible && (
            <div
              className="glass-card"
              style={{
                display: 'flex',
                flexDirection: 'column',
                padding: '18px',
                gap: '14px',
                overflowY: 'auto',
                maxHeight: 'calc(100vh - 240px)',
              }}
            >
              {/* Finding Header */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '12px' }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                    <span
                      style={{
                        fontSize: '0.76rem',
                        fontWeight: 800,
                        color: 'var(--brand-cyan)',
                        fontFamily: 'var(--font-mono)',
                        background: 'rgba(6, 182, 212, 0.1)',
                        padding: '2px 7px',
                        borderRadius: '4px',
                        border: '1px solid rgba(6, 182, 212, 0.3)',
                      }}
                    >
                      {activeFinding.id}
                    </span>
                    {getSeverityBadge(activeFinding.severity)}
                  </div>
                  <h3 style={{ fontSize: '0.96rem', fontWeight: 700, color: 'var(--text-primary)', lineHeight: 1.3 }}>
                    {activeFinding.title}
                  </h3>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <button
                    onClick={() => setIsFindingPanelVisible(false)}
                    title="Hide Finding Panel"
                    aria-label="Hide Finding Panel"
                    style={{
                      background: 'transparent',
                      border: 'none',
                      color: 'var(--text-muted)',
                      cursor: 'pointer',
                      padding: '4px',
                    }}
                  >
                    <EyeOff size={16} />
                  </button>
                </div>
              </div>

              {/* Application Context */}
              <div
                style={{
                  background: 'var(--bg-tertiary)',
                  padding: '10px 12px',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--border-subtle)',
                  fontSize: '0.74rem',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '3px',
                }}
              >
                <div style={{ fontSize: '0.66rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                  Application Context:
                </div>
                <div>
                  <strong style={{ color: 'var(--text-secondary)' }}>Tender:</strong>{' '}
                  <span style={{ color: '#60a5fa' }}>GEM/2021/B/1128240</span>
                </div>
                <div>
                  <strong style={{ color: 'var(--text-secondary)' }}>Bidder:</strong>{' '}
                  <span style={{ color: 'var(--text-primary)' }}>Aravind Integrated Solutions Private Limited (DEMO)</span>
                </div>
                <div>
                  <strong style={{ color: 'var(--text-secondary)' }}>Application:</strong>{' '}
                  <span style={{ color: 'var(--brand-cyan)', fontFamily: 'var(--font-mono)' }}>APP-001</span>
                </div>
                <div>
                  <strong style={{ color: 'var(--text-secondary)' }}>Finding:</strong>{' '}
                  <span style={{ color: '#f87171', fontWeight: 700 }}>{activeFinding.id}</span>
                </div>
              </div>

              {/* Status Badge */}
              <div>
                <div style={{ fontSize: '0.68rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '4px' }}>
                  Current Review Status:
                </div>
                {getStatusBadge(activeFinding.review_status)}
              </div>

              {/* Section 1: Requirement */}
              <div
                style={{
                  background: 'var(--bg-tertiary)',
                  padding: '12px',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--border-subtle)',
                }}
              >
                <div style={{ fontSize: '0.68rem', fontWeight: 700, color: '#60a5fa', textTransform: 'uppercase', marginBottom: '4px' }}>
                  Requirement & Tender Clause:
                </div>
                <div style={{ fontSize: '0.76rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '3px' }}>
                  {activeEvidenceConfig.clause}
                </div>
                <p style={{ fontSize: '0.74rem', color: 'var(--text-secondary)', lineHeight: 1.45 }}>
                  {activeEvidenceConfig.requirementText}
                </p>
              </div>

              {/* Section 2: Evidence Citations */}
              <div
                style={{
                  background: 'var(--bg-tertiary)',
                  padding: '12px',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--border-subtle)',
                }}
              >
                <div style={{ fontSize: '0.68rem', fontWeight: 700, color: 'var(--brand-cyan)', textTransform: 'uppercase', marginBottom: '6px' }}>
                  Evidence Source References:
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  {activeEvidenceConfig.evidenceItems.map((item, idx) => (
                    <div
                      key={idx}
                      style={{
                        padding: '8px 10px',
                        background: 'rgba(255, 255, 255, 0.03)',
                        borderRadius: 'var(--radius-sm)',
                        border: '1px solid var(--border-subtle)',
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '3px' }}>
                        <span style={{ fontSize: '0.74rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                          {item.label}
                        </span>
                        <button
                          onClick={() => handleJumpToEvidence(item.docId, item.page)}
                          style={{
                            fontSize: '0.66rem',
                            padding: '2px 8px',
                            background: 'rgba(59, 130, 246, 0.2)',
                            color: '#93c5fd',
                            border: '1px solid rgba(59, 130, 246, 0.35)',
                            borderRadius: '4px',
                            cursor: 'pointer',
                          }}
                        >
                          Jump to Page
                        </button>
                      </div>
                      <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>
                        {item.description}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Section 3: Verification Result & Extracted Values */}
              <div
                style={{
                  background: 'var(--bg-tertiary)',
                  padding: '12px',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--border-subtle)',
                }}
              >
                <div style={{ fontSize: '0.68rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '6px' }}>
                  Analytical Verification:
                </div>
                <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', marginBottom: '8px' }}>
                  Method: <strong style={{ color: 'var(--text-primary)' }}>{activeEvidenceConfig.verificationMethod}</strong>
                </div>

                {/* Extracted Values Table */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', marginBottom: '10px' }}>
                  {activeEvidenceConfig.extractedValues.map((ev, idx) => (
                    <div
                      key={idx}
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        padding: '4px 6px',
                        background: 'rgba(255, 255, 255, 0.02)',
                        borderRadius: '3px',
                        fontSize: '0.72rem',
                      }}
                    >
                      <span style={{ color: 'var(--text-muted)' }}>{ev.label}:</span>
                      <span style={{ fontWeight: 600, color: 'var(--text-primary)', textAlign: 'right' }}>{ev.value}</span>
                    </div>
                  ))}
                </div>

                {/* Variance / Discrepancy Alert */}
                {activeEvidenceConfig.varianceHighlight && (
                  <div
                    style={{
                      background: 'rgba(239, 68, 68, 0.1)',
                      border: '1px solid rgba(239, 68, 68, 0.3)',
                      padding: '8px 10px',
                      borderRadius: 'var(--radius-sm)',
                    }}
                  >
                    <div style={{ fontSize: '0.68rem', fontWeight: 700, color: '#f87171', textTransform: 'uppercase' }}>
                      Discrepancy / Variance:
                    </div>
                    <div style={{ fontSize: '0.74rem', color: '#b91c1c', fontWeight: 600, marginTop: '2px' }}>
                      {activeEvidenceConfig.varianceHighlight}
                    </div>
                  </div>
                )}
              </div>

              {/* Section 4: Officer Audit Notes */}
              {activeFinding.officer_notes && (
                <div
                  style={{
                    background: 'rgba(59, 130, 246, 0.08)',
                    borderLeft: '3px solid var(--brand-blue)',
                    padding: '8px 12px',
                    borderRadius: '0 var(--radius-sm) var(--radius-sm) 0',
                    fontSize: '0.74rem',
                    color: 'var(--text-secondary)',
                  }}
                >
                  <strong style={{ color: 'var(--text-primary)' }}>Officer Audit Record:</strong> {activeFinding.officer_notes}
                </div>
              )}

              {/* Section 5: Officer Action Buttons */}
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(3, 1fr)',
                  gap: '8px',
                  borderTop: '1px solid var(--border-subtle)',
                  paddingTop: '12px',
                  marginTop: 'auto',
                }}
              >
                <button
                  className="btn btn-secondary"
                  style={{ fontSize: '0.74rem', padding: '7px 8px' }}
                  onClick={() => handleOpenAction(activeFinding, 'REVIEW')}
                >
                  <CheckCircle size={14} /> Review
                </button>

                <button
                  className="btn btn-secondary"
                  style={{ fontSize: '0.74rem', padding: '7px 8px' }}
                  onClick={() => handleOpenAction(activeFinding, 'CLARIFICATION')}
                >
                  <MessageSquare size={14} /> Clarification
                </button>

                <button
                  className="btn btn-primary"
                  style={{ fontSize: '0.74rem', padding: '7px 8px' }}
                  onClick={() => handleOpenAction(activeFinding, 'NOTE')}
                >
                  <FileCheck size={14} /> Add Note
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* VIEW 2: ALL FINDING CARDS OVERVIEW */}
      {viewMode === 'CARDS' && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(460px, 1fr))', gap: '18px' }}>
          {filteredFindings.map((f) => {
            const config = FINDING_EVIDENCE_MAP[f.id] || FINDING_EVIDENCE_MAP['FND-02'];
            return (
              <div
                key={f.id}
                className="glass-card"
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  padding: '20px',
                  border: '1px solid var(--border-subtle)',
                  background: 'var(--bg-card)',
                }}
              >
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      {getSeverityBadge(f.severity)}
                      <span style={{ fontSize: '0.72rem', color: 'var(--brand-cyan)', fontFamily: 'var(--font-mono)' }}>
                        {f.id}
                      </span>
                    </div>
                    {getStatusBadge(f.review_status)}
                  </div>

                  <h3 style={{ fontSize: '1.02rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '10px' }}>
                    {f.title}
                  </h3>

                  {/* Bidder Application Context */}
                  <div style={{ marginBottom: '12px', padding: '8px 12px', background: 'rgba(59, 130, 246, 0.08)', borderRadius: '4px', border: '1px solid rgba(59, 130, 246, 0.2)' }}>
                    <div style={{ fontSize: '0.66rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                      Bidder Application
                    </div>
                    <div style={{ color: 'var(--brand-cyan)', fontWeight: 700, fontSize: '0.82rem', marginTop: '1px' }}>
                      Aravind Integrated Solutions Private Limited (DEMO)
                    </div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>
                      Application: APP-001 · 1 Application / Multiple Findings
                    </div>
                  </div>

                  <div
                    style={{
                      background: 'var(--bg-tertiary)',
                      padding: '12px 14px',
                      borderRadius: 'var(--radius-md)',
                      border: '1px solid var(--border-subtle)',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '8px',
                      fontSize: '0.8rem',
                      marginBottom: '14px',
                    }}
                  >
                    <div>
                      <div style={{ fontSize: '0.68rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                        Clause & Requirement:
                      </div>
                      <div style={{ color: 'var(--text-primary)', marginTop: '1px', fontWeight: 600 }}>
                        {config.clause}
                      </div>
                    </div>

                    <div>
                      <div style={{ fontSize: '0.68rem', fontWeight: 700, color: 'var(--brand-cyan)', textTransform: 'uppercase' }}>
                        Applicant Evidence:
                      </div>
                      <div style={{ color: '#e2e8f0', marginTop: '1px' }}>
                        {config.defaultDocFile} (Page {config.defaultPage})
                      </div>
                    </div>

                    {config.varianceHighlight && (
                      <div style={{ background: 'rgba(239, 68, 68, 0.1)', padding: '6px 10px', borderRadius: '4px', border: '1px solid rgba(239, 68, 68, 0.25)' }}>
                        <div style={{ fontSize: '0.68rem', fontWeight: 700, color: '#f87171', textTransform: 'uppercase' }}>
                          Variance / Discrepancy:
                        </div>
                        <div style={{ color: 'var(--text-primary)', fontWeight: 600, marginTop: '1px', fontSize: '0.76rem' }}>
                          {config.varianceHighlight}
                        </div>
                      </div>
                    )}
                  </div>

                  {f.officer_notes && (
                    <div
                      style={{
                        background: 'rgba(59, 130, 246, 0.08)',
                        borderLeft: '3px solid var(--brand-blue)',
                        padding: '8px 12px',
                        borderRadius: '0 var(--radius-sm) var(--radius-sm) 0',
                        marginBottom: '14px',
                        fontSize: '0.74rem',
                        color: 'var(--text-secondary)',
                      }}
                    >
                      <strong style={{ color: 'var(--text-primary)' }}>Officer Audit Note:</strong> {f.officer_notes}
                    </div>
                  )}
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', borderTop: '1px solid var(--border-subtle)', paddingTop: '14px' }}>
                  <button
                    className="btn btn-primary"
                    style={{ fontSize: '0.76rem', padding: '8px 14px', width: '100%', display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '6px' }}
                    onClick={() => {
                      handleSelectFinding(f.id);
                      setViewMode('WORKSPACE');
                    }}
                  >
                    <Columns size={15} /> Inspect Original Applicant File (Workspace)
                  </button>

                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px' }}>
                    <button
                      className="btn btn-secondary"
                      style={{ fontSize: '0.74rem', padding: '6px 8px' }}
                      onClick={() => handleOpenAction(f, 'REVIEW')}
                    >
                      <CheckCircle size={13} /> Review
                    </button>
                    <button
                      className="btn btn-secondary"
                      style={{ fontSize: '0.74rem', padding: '6px 8px' }}
                      onClick={() => handleOpenAction(f, 'CLARIFICATION')}
                    >
                      <MessageSquare size={13} /> Clarify
                    </button>
                    <button
                      className="btn btn-secondary"
                      style={{ fontSize: '0.74rem', padding: '6px 8px' }}
                      onClick={() => handleOpenAction(f, 'NOTE')}
                    >
                      <FileCheck size={13} /> Note
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Action Dialog Modal (Review, Clarification, Note) */}
      {actionModalType && selectedFindingForAction && (
        <div className="modal-backdrop" onClick={() => setActionModalType(null)}>
          <div
            className="modal-content"
            onClick={(e) => e.stopPropagation()}
            style={{ maxWidth: '560px' }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <ShieldCheck size={20} color="var(--brand-cyan)" />
                <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                  {actionModalType === 'REVIEW' && 'Officer Finding Determination'}
                  {actionModalType === 'CLARIFICATION' && 'Draft Clarification Notice'}
                  {actionModalType === 'NOTE' && 'Record Officer Audit Note'}
                </h3>
              </div>
              <button
                onClick={() => setActionModalType(null)}
                style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
              >
                <X size={18} />
              </button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', fontSize: '0.82rem' }}>
              <div style={{ background: 'var(--bg-tertiary)', padding: '10px 14px', borderRadius: 'var(--radius-sm)' }}>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Target Finding:</div>
                <div style={{ fontWeight: 700, color: 'var(--text-primary)' }}>
                  {selectedFindingForAction.id}: {selectedFindingForAction.title}
                </div>
              </div>

              {actionModalType === 'REVIEW' && (
                <div>
                  <label style={{ fontSize: '0.74rem', fontWeight: 600, color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>
                    Officer Review Ruling:
                  </label>
                  <textarea
                    rows={3}
                    placeholder="Enter formal justification note for procurement committee record..."
                    value={noteText}
                    onChange={(e) => setNoteText(e.target.value)}
                    style={{
                      width: '100%',
                      background: 'var(--bg-tertiary)',
                      border: '1px solid var(--border-subtle)',
                      borderRadius: 'var(--radius-sm)',
                      padding: '10px',
                      color: '#ffffff',
                      fontSize: '0.8rem',
                      outline: 'none',
                    }}
                  />
                </div>
              )}

              {actionModalType === 'CLARIFICATION' && (
                <div>
                  <label style={{ fontSize: '0.74rem', fontWeight: 600, color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>
                    Clarification Notice Text (Dispatched via GeM Portal):
                  </label>
                  <textarea
                    rows={4}
                    value={clarificationQuery}
                    onChange={(e) => setClarificationQuery(e.target.value)}
                    style={{
                      width: '100%',
                      background: 'var(--bg-tertiary)',
                      border: '1px solid var(--border-subtle)',
                      borderRadius: 'var(--radius-sm)',
                      padding: '10px',
                      color: '#ffffff',
                      fontSize: '0.8rem',
                      outline: 'none',
                    }}
                  />
                </div>
              )}

              {actionModalType === 'NOTE' && (
                <div>
                  <label style={{ fontSize: '0.74rem', fontWeight: 600, color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>
                    Officer Note:
                  </label>
                  <textarea
                    rows={3}
                    placeholder="Enter confidential observation note for evaluation file..."
                    value={noteText}
                    onChange={(e) => setNoteText(e.target.value)}
                    style={{
                      width: '100%',
                      background: 'var(--bg-tertiary)',
                      border: '1px solid var(--border-subtle)',
                      borderRadius: 'var(--radius-sm)',
                      padding: '10px',
                      color: '#ffffff',
                      fontSize: '0.8rem',
                      outline: 'none',
                    }}
                  />
                </div>
              )}
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '16px' }}>
              <button className="btn btn-secondary" onClick={() => setActionModalType(null)}>
                Cancel
              </button>
              <button className="btn btn-primary" onClick={handleSaveAction}>
                Confirm & Record in Audit Log
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

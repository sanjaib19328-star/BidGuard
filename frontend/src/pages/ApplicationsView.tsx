import React, { useState } from 'react';
import {
  FolderKanban,
  FileText,
  ShieldCheck,
  AlertTriangle,
  Eye,
  CheckCircle2,
  Clock,
  ArrowLeft,
  ChevronRight,
  ExternalLink,
  MessageSquare,
  FileCheck,
  Building,
  Calendar,
  AlertCircle,
  FileSpreadsheet,
} from 'lucide-react';
import {
  Tender,
  BidderApplicationPackage,
  BidderApplicationDocument,
  DocumentVerificationCheck,
} from '../types';
import {
  DEMO_CAG_TENDER,
  DEMO_BIDDER_APPLICATION,
  DEMO_VERIFICATION_CHECKS,
  DEMO_FINDINGS,
} from '../api/demoData';

interface ApplicationsViewProps {
  activeTender: Tender | null;
  onNavigate: (tab: any) => void;
}

export const ApplicationsView: React.FC<ApplicationsViewProps> = ({
  activeTender,
  onNavigate,
}) => {
  const application = DEMO_BIDDER_APPLICATION;
  const [selectedDocId, setSelectedDocId] = useState<string>(application.documents[2].id); // Default to Financials (doc-03)
  const [activePage, setActivePage] = useState<number>(1);
  const [isWorkspaceOpen, setIsWorkspaceOpen] = useState<boolean>(true);
  const [officerNote, setOfficerNote] = useState<string>('');
  const [officerNotesList, setOfficerNotesList] = useState<string[]>([
    'Cross-checked CA turnover against P&L Schedule III. ₹80.15L discrepancy confirmed.',
  ]);
  const [actionNotice, setActionNotice] = useState<string | null>(null);

  const selectedDoc =
    application.documents.find((d) => d.id === selectedDocId) || application.documents[0];

  // Map selected document to associated verification check
  const getAssociatedCheck = (doc: BidderApplicationDocument): DocumentVerificationCheck => {
    const found = DEMO_VERIFICATION_CHECKS.find((chk) => chk.source_document === doc.file_name);
    return found || DEMO_VERIFICATION_CHECKS[0];
  };

  const currentCheck = getAssociatedCheck(selectedDoc);

  const handleAddNote = () => {
    if (!officerNote.trim()) return;
    setOfficerNotesList([officerNote.trim(), ...officerNotesList]);
    setOfficerNote('');
    setActionNotice('Officer note recorded in audit log.');
    setTimeout(() => setActionNotice(null), 3500);
  };

  const handleRequestClarification = () => {
    setActionNotice(`Clarification request notice drafted for ${currentCheck.requirement_title}.`);
    setTimeout(() => setActionNotice(null), 4000);
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'COMPLIANT':
        return <span className="badge badge-compliant">COMPLIANT</span>;
      case 'PARTIAL':
        return <span className="badge badge-partial">PARTIAL</span>;
      case 'EVIDENCE_MISSING':
        return <span className="badge badge-evidence-missing">EVIDENCE MISSING</span>;
      case 'CLARIFICATION_PENDING':
        return <span className="badge badge-clarification">CLARIFICATION PENDING</span>;
      case 'NON_COMPLIANT':
        return <span className="badge badge-noncompliant">NON COMPLIANT</span>;
      default:
        return <span className="badge badge-review">{status}</span>;
    }
  };

  if (!isWorkspaceOpen) {
    // Package overview view
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '22px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h1 style={{ fontSize: '1.45rem', fontWeight: 800, color: 'var(--text-primary)', letterSpacing: '-0.02em' }}>
              Bidder Application Packages
            </h1>
            <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
              Complete documentary submissions received for GeM Bid GEM/2021/B/1128240
            </p>
          </div>
          <span className="badge badge-synthetic">SYNTHETIC DEMO APPLICATION</span>
        </div>

        {/* Application Package Card */}
        <div
          className="glass-card"
          style={{
            border: '1px solid rgba(59, 130, 246, 0.35)',
            background: 'var(--bg-card)',
            padding: '24px 28px',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '14px' }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px' }}>
                <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--text-primary)' }}>
                  {application.bidder_name}
                </h2>
                <span className="badge badge-synthetic">DEMO / SYNTHETIC DATA</span>
              </div>
              <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
                <strong>Trade Name:</strong> {application.trade_name} &nbsp;·&nbsp;{' '}
                <strong>CIN:</strong> {application.cin} &nbsp;·&nbsp;{' '}
                <strong>Registered Office:</strong> {application.registered_address}
              </p>
            </div>

            <div style={{ textAlign: 'right' }}>
              <span className="badge badge-partial" style={{ fontSize: '0.78rem', padding: '6px 12px' }}>
                REVIEW REQUIRED
              </span>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                Submitted: 24-03-2021 (On-Time)
              </div>
            </div>
          </div>

          {/* Quick Metrics Bar */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(6, 1fr)',
              gap: '10px',
              background: 'var(--bg-tertiary)',
              padding: '14px 18px',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border-subtle)',
              marginBottom: '20px',
            }}
          >
            <div>
              <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>Bidder Applications</div>
              <div style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--text-primary)' }}>
                1 Package
              </div>
            </div>
            <div>
              <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>Documents Uploaded</div>
              <div style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--text-primary)' }}>
                6 Documents
              </div>
            </div>
            <div>
              <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>Total Pages</div>
              <div style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--text-primary)' }}>
                16 Pages
              </div>
            </div>
            <div>
              <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>Verification Checks</div>
              <div style={{ fontSize: '1.1rem', fontWeight: 800, color: '#60a5fa' }}>
                10 Checks
              </div>
            </div>
            <div>
              <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>Associated Findings</div>
              <div style={{ fontSize: '1.1rem', fontWeight: 800, color: '#f87171' }}>
                5 Findings
              </div>
            </div>
            <div>
              <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>Review Status</div>
              <div style={{ fontSize: '1.1rem', fontWeight: 800, color: '#fbbf24' }}>
                Review Required
              </div>
            </div>
          </div>

          {/* List of 6 Application Documents */}
          <div style={{ marginBottom: '20px' }}>
            <h4 style={{ fontSize: '0.88rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '10px' }}>
              Submission Document Manifest (6 Files)
            </h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {application.documents.map((doc, idx) => (
                <div
                  key={doc.id}
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    padding: '10px 14px',
                    background: 'var(--bg-tertiary)',
                    borderRadius: 'var(--radius-sm)',
                    border: '1px solid var(--border-subtle)',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <span style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--brand-cyan)' }}>
                      0{idx + 1}.
                    </span>
                    <div>
                      <div style={{ fontSize: '0.84rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                        {doc.title}
                      </div>
                      <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                        {doc.file_name} · {doc.pages} pages · {doc.description}
                      </div>
                    </div>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <span style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>
                      {doc.extraction_status === 'COMPLETE' ? '✓ Extracted' : '⚠ Partial'}
                    </span>
                    {getStatusBadge(doc.verification_status)}
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div style={{ display: 'flex', gap: '12px' }}>
            <button
              className="btn btn-primary"
              style={{ padding: '10px 22px' }}
              onClick={() => setIsWorkspaceOpen(true)}
            >
              <Eye size={16} /> Open Document Verification Workspace
            </button>
            <button className="btn btn-secondary" onClick={() => onNavigate('findings')}>
              <AlertTriangle size={16} /> View Risk Findings (5)
            </button>
          </div>
        </div>
      </div>
    );
  }

  // 3-COLUMN WORKSPACE: LEFT (Doc List), CENTER (Doc/Evidence Viewer), RIGHT (Verification Result)
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
      {/* Workspace Top Action Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <button
            className="btn btn-secondary"
            style={{ fontSize: '0.78rem', padding: '6px 12px' }}
            onClick={() => setIsWorkspaceOpen(false)}
          >
            <ArrowLeft size={14} /> Back to Application Overview
          </button>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <h2 style={{ fontSize: '1.15rem', fontWeight: 800, color: 'var(--text-primary)' }}>
                {application.bidder_name}
              </h2>
              <span className="badge badge-blue">APP-001</span>
              <span className="badge badge-synthetic">DEMO / SYNTHETIC</span>
            </div>
            <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
              GeM Bid: GEM/2021/B/1128240 · <strong>1 Application Package · 6 Submitted Documents · 16 Pages · 10 Verification Checks · 5 Findings</strong>
            </div>
          </div>
        </div>

        {actionNotice && (
          <div
            style={{
              background: 'rgba(16, 185, 129, 0.15)',
              border: '1px solid rgba(16, 185, 129, 0.4)',
              color: '#34d399',
              padding: '6px 14px',
              borderRadius: 'var(--radius-md)',
              fontSize: '0.78rem',
              fontWeight: 600,
            }}
          >
            ✓ {actionNotice}
          </div>
        )}
      </div>

      {/* 3-Column Layout */}
      <div className="workspace-layout">
        {/* ================= COLUMN 1: LEFT DOCUMENT LIST ================= */}
        <div
          className="glass-card"
          style={{
            padding: '16px',
            display: 'flex',
            flexDirection: 'column',
            gap: '12px',
            maxHeight: 'calc(100vh - 180px)',
            overflowY: 'auto',
          }}
        >
          <div style={{ borderBottom: '1px solid var(--border-subtle)', paddingBottom: '10px' }}>
            <h3 style={{ fontSize: '0.88rem', fontWeight: 700, color: 'var(--text-primary)' }}>
              Application Documents
            </h3>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
              6 extractable vector PDF files
            </span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {application.documents.map((doc, idx) => {
              const isSelected = doc.id === selectedDoc.id;
              return (
                <div
                  key={doc.id}
                  onClick={() => {
                    setSelectedDocId(doc.id);
                    setActivePage(1);
                  }}
                  style={{
                    padding: '10px 12px',
                    borderRadius: 'var(--radius-md)',
                    background: isSelected ? '#eff6ff' : '#f8fafc',
                    border: isSelected ? '1px solid rgba(59, 130, 246, 0.4)' : '1px solid var(--border-subtle)',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '4px' }}>
                    <span style={{ fontSize: '0.72rem', fontWeight: 700, color: isSelected ? '#60a5fa' : 'var(--text-muted)' }}>
                      Doc 0{idx + 1}
                    </span>
                    <span style={{ fontSize: '0.68rem', color: 'var(--text-secondary)' }}>
                      {doc.pages} Pgs
                    </span>
                  </div>

                  <div style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-primary)', lineHeight: 1.3, marginBottom: '6px' }}>
                    {doc.title}
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>
                      {doc.evidence_availability === 'AVAILABLE' ? 'Evidence Ready' : 'Omission Flag'}
                    </span>
                    {getStatusBadge(doc.verification_status)}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* ================= COLUMN 2: CENTER DOCUMENT/EVIDENCE VIEWER ================= */}
        <div
          className="glass-card"
          style={{
            padding: '20px',
            display: 'flex',
            flexDirection: 'column',
            gap: '14px',
            maxHeight: 'calc(100vh - 180px)',
            overflowY: 'auto',
            background: 'var(--bg-card)',
          }}
        >
          {/* Document Header & Page Navigation */}
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              borderBottom: '1px solid var(--border-subtle)',
              paddingBottom: '12px',
            }}
          >
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <FileText size={17} color="var(--brand-cyan)" />
                <h3 style={{ fontSize: '0.98rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                  {selectedDoc.title}
                </h3>
              </div>
              <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                {selectedDoc.file_name} · {selectedDoc.document_type}
              </span>
            </div>

            {/* Page Buttons */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Page:</span>
              {Array.from({ length: selectedDoc.pages }, (_, i) => i + 1).map((pg) => (
                <button
                  key={pg}
                  onClick={() => setActivePage(pg)}
                  style={{
                    width: '26px',
                    height: '26px',
                    borderRadius: '4px',
                    background: activePage === pg ? 'var(--brand-blue)' : 'rgba(255, 255, 255, 0.05)',
                    color: activePage === pg ? '#ffffff' : 'var(--text-secondary)',
                    border: '1px solid var(--border-subtle)',
                    fontSize: '0.74rem',
                    fontWeight: 700,
                    cursor: 'pointer',
                  }}
                >
                  {pg}
                </button>
              ))}
            </div>
          </div>

          {/* Synthetic Data Banner */}
          <div
            style={{
              background: 'rgba(234, 88, 12, 0.12)',
              border: '1px solid rgba(234, 88, 12, 0.3)',
              borderRadius: 'var(--radius-sm)',
              padding: '8px 12px',
              fontSize: '0.72rem',
              color: '#fb923c',
              fontWeight: 600,
              textAlign: 'center',
            }}
          >
            [DEMO / SYNTHETIC DATA — FOR TESTING AND EVALUATION ONLY — NOT A REAL GOVERNMENT RECORD]
          </div>

          {/* Extracted Key Items Table */}
          {selectedDoc.extracted_items && selectedDoc.extracted_items.length > 0 && (
            <div style={{ background: 'var(--bg-tertiary)', padding: '12px 14px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: '0.74rem', fontWeight: 700, color: 'var(--brand-cyan)', textTransform: 'uppercase', marginBottom: '8px', letterSpacing: '0.04em' }}>
                Extracted Evidence Points (LayoutLM & Regex Anchors)
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                {selectedDoc.extracted_items.map((item, idx) => (
                  <div
                    key={idx}
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      fontSize: '0.78rem',
                      padding: '4px 0',
                      borderBottom: '1px solid rgba(255, 255, 255, 0.04)',
                    }}
                  >
                    <span style={{ color: 'var(--text-secondary)' }}>
                      {item.label} (Pg {item.page}):
                    </span>
                    <span style={{ fontWeight: 600, color: item.discrepancy_note ? '#b45309' : 'var(--text-primary)', textAlign: 'right' }}>
                      {item.value}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Document Content Extracted Text Preview */}
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: '0.74rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '6px' }}>
              Extracted OCR / Vector Text (Page {activePage} of {selectedDoc.pages})
            </div>
            <pre
              style={{
                background: '#070a13',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-md)',
                padding: '16px',
                color: '#e2e8f0',
                fontSize: '0.78rem',
                fontFamily: 'var(--font-mono)',
                whiteSpace: 'pre-wrap',
                lineHeight: 1.6,
                maxHeight: '340px',
                overflowY: 'auto',
              }}
            >
              {selectedDoc.content_preview}
            </pre>
          </div>
        </div>

        {/* ================= COLUMN 3: RIGHT VERIFICATION RESULT PANEL ================= */}
        <div
          className="glass-card"
          style={{
            padding: '20px',
            display: 'flex',
            flexDirection: 'column',
            gap: '16px',
            maxHeight: 'calc(100vh - 180px)',
            overflowY: 'auto',
          }}
        >
          <div style={{ borderBottom: '1px solid var(--border-subtle)', paddingBottom: '12px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
              <span className="badge badge-blue">{currentCheck.category} Verification</span>
              {getStatusBadge(currentCheck.result)}
            </div>
            <h3 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)' }}>
              {currentCheck.requirement_title}
            </h3>
            <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
              Tender Clause: {currentCheck.requirement_clause}
            </span>
          </div>

          {/* Verification Comparison Blocks */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '0.8rem' }}>
            <div style={{ background: 'var(--bg-tertiary)', padding: '10px 12px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: '0.68rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                Tender Requirement
              </div>
              <div style={{ color: 'var(--text-primary)', marginTop: '2px', lineHeight: 1.4 }}>
                {currentCheck.requirement_text}
              </div>
            </div>

            <div style={{ background: 'var(--bg-tertiary)', padding: '10px 12px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: '0.68rem', fontWeight: 700, color: '#60a5fa', textTransform: 'uppercase' }}>
                Extracted Bidder Evidence
              </div>
              <div style={{ color: 'var(--text-primary)', marginTop: '2px', fontWeight: 600 }}>
                {currentCheck.submitted_evidence}
              </div>
            </div>

            {currentCheck.cross_document_evidence && (
              <div style={{ background: 'rgba(245, 158, 11, 0.1)', padding: '10px 12px', borderRadius: 'var(--radius-sm)', border: '1px solid rgba(245, 158, 11, 0.3)' }}>
                <div style={{ fontSize: '0.68rem', fontWeight: 700, color: '#fbbf24', textTransform: 'uppercase' }}>
                  Cross-Document Cross-Check
                </div>
                <div style={{ color: 'var(--text-primary)', marginTop: '2px' }}>
                  {currentCheck.cross_document_evidence}
                </div>
              </div>
            )}

            {currentCheck.variance && (
              <div style={{ background: 'rgba(239, 68, 68, 0.12)', padding: '10px 12px', borderRadius: 'var(--radius-sm)', border: '1px solid rgba(239, 68, 68, 0.3)' }}>
                <div style={{ fontSize: '0.68rem', fontWeight: 700, color: '#f87171', textTransform: 'uppercase' }}>
                  Difference / Discrepancy
                </div>
                <div style={{ color: 'var(--text-primary)', marginTop: '2px', fontWeight: 600 }}>
                  {currentCheck.variance}
                </div>
              </div>
            )}

            <div style={{ background: 'var(--bg-tertiary)', padding: '10px 12px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: '0.68rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                Verification Methodology
              </div>
              <div style={{ color: 'var(--text-secondary)', marginTop: '2px' }}>
                {currentCheck.verification_method}
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '8px', marginTop: '4px' }}>
            <button
              className="btn btn-secondary"
              style={{ fontSize: '0.74rem', padding: '7px 8px' }}
              onClick={() => {
                setActionNotice(`Displaying evidence snippet for ${currentCheck.requirement_title}`);
                setTimeout(() => setActionNotice(null), 3000);
              }}
            >
              <Eye size={14} /> View Evidence
            </button>

            <button
              className="btn btn-secondary"
              style={{ fontSize: '0.74rem', padding: '7px 8px' }}
              onClick={() => onNavigate('findings')}
            >
              <AlertTriangle size={14} /> Open Finding
            </button>

            <button
              className="btn btn-secondary"
              style={{ fontSize: '0.74rem', padding: '7px 8px' }}
              onClick={handleRequestClarification}
            >
              <MessageSquare size={14} /> Clarification
            </button>

            <button
              className="btn btn-primary"
              style={{ fontSize: '0.74rem', padding: '7px 8px' }}
              onClick={() => {
                const el = document.getElementById('officer-note-input');
                if (el) el.focus();
              }}
            >
              <FileCheck size={14} /> Add Note
            </button>
          </div>

          {/* Officer Note Section */}
          <div style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: '12px' }}>
            <div style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '6px' }}>
              Officer Safeguard Notes ({officerNotesList.length})
            </div>

            <div style={{ display: 'flex', gap: '6px', marginBottom: '8px' }}>
              <input
                id="officer-note-input"
                type="text"
                placeholder="Enter evaluation finding note..."
                value={officerNote}
                onChange={(e) => setOfficerNote(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') handleAddNote();
                }}
                style={{
                  flex: 1,
                  background: 'var(--bg-tertiary)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-sm)',
                  padding: '6px 10px',
                  color: '#ffffff',
                  fontSize: '0.76rem',
                  outline: 'none',
                }}
              />
              <button className="btn btn-secondary" style={{ fontSize: '0.72rem', padding: '6px 10px' }} onClick={handleAddNote}>
                Save
              </button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', maxHeight: '110px', overflowY: 'auto' }}>
              {officerNotesList.map((n, i) => (
                <div
                  key={i}
                  style={{
                    fontSize: '0.72rem',
                    color: 'var(--text-secondary)',
                    background: 'var(--bg-tertiary)',
                    padding: '6px 8px',
                    borderRadius: '4px',
                    borderLeft: '2px solid var(--brand-blue)',
                  }}
                >
                  {n}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

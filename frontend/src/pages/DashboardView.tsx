import React from 'react';
import {
  FileText,
  ShieldCheck,
  AlertTriangle,
  FolderKanban,
  CheckCircle2,
  Clock,
  ArrowRight,
  ExternalLink,
  HelpCircle,
  FileSpreadsheet,
  Building2,
  ChevronRight,
  UserCheck,
  Search,
} from 'lucide-react';
import { Tender, Bidder, OfficerFinding } from '../types';
import { DEMO_CAG_TENDER, DEMO_BIDDER_APPLICATION, DEMO_VERIFICATION_CHECKS, DEMO_FINDINGS } from '../api/demoData';

interface DashboardViewProps {
  tenders: Tender[];
  bidders: Bidder[];
  findings: OfficerFinding[];
  activeTender: Tender | null;
  onSelectTender: (tender: Tender) => void;
  onNavigate: (tab: any) => void;
}

export const DashboardView: React.FC<DashboardViewProps> = ({
  tenders,
  bidders,
  findings,
  activeTender,
  onSelectTender,
  onNavigate,
}) => {
  const currentTender = activeTender || DEMO_CAG_TENDER;

  // Verification statistics from demo or live checks
  const totalReqs = DEMO_VERIFICATION_CHECKS.length;
  const verifiedCount = DEMO_VERIFICATION_CHECKS.filter((c) => c.result === 'COMPLIANT').length;
  const evidenceMissingCount = DEMO_VERIFICATION_CHECKS.filter((c) => c.result === 'EVIDENCE_MISSING').length;
  const partialCount = DEMO_VERIFICATION_CHECKS.filter((c) => c.result === 'PARTIAL').length;
  const nonCompliantCount = DEMO_VERIFICATION_CHECKS.filter((c) => c.result === 'NON_COMPLIANT').length;
  const notVerifiableCount = DEMO_VERIFICATION_CHECKS.filter((c) => c.result === 'NOT_VERIFIABLE').length;
  const clarificationPendingCount = DEMO_VERIFICATION_CHECKS.filter((c) => c.result === 'CLARIFICATION_PENDING').length;

  // Use canonical demo findings as guaranteed fallback so counts never desynchronize
  const effectiveFindings: OfficerFinding[] = findings && findings.length > 0 ? findings : DEMO_FINDINGS;
  const openFindingsCount = effectiveFindings.filter(
    (f: OfficerFinding) => f.review_status !== 'ACCEPTED' && f.review_status !== 'REJECTED'
  ).length;

  // Risk overview counts derived from canonical findings
  const criticalFindings = effectiveFindings.filter((f: OfficerFinding) => f.severity === 'CRITICAL').length;
  const highFindings = effectiveFindings.filter((f: OfficerFinding) => f.severity === 'HIGH').length;
  const mediumFindings = effectiveFindings.filter((f: OfficerFinding) => f.severity === 'MEDIUM').length;
  const lowFindings = effectiveFindings.filter((f: OfficerFinding) => f.severity === 'LOW').length;

  // Recent Officer Actions
  const recentOfficerActions = [
    {
      type: 'reviewed_finding',
      title: 'Reviewed Cross-Document Discrepancy (FND-02)',
      details: 'CA certified turnover (₹6.20 Cr) vs Audited P&L (₹5.40 Cr). Variance ₹80.15L flagged under GFR Rule 144.',
      time: '12 mins ago',
      badge: 'REVIEWED',
      badgeColor: '#60a5fa',
    },
    {
      type: 'clarification_requested',
      title: 'Clarification Notice Issued to Bidder',
      details: 'Formal 3-day notice issued requiring Chartered Accountant reconciliation for FY 2019-20 turnover figures.',
      time: '45 mins ago',
      badge: 'CLARIFICATION',
      badgeColor: '#a78bfa',
    },
    {
      type: 'evidence_accepted',
      title: 'EMD Bank Guarantee Document Verified (CHK-04)',
      details: 'State Bank of India BG No. 0069121BG0004128 for ₹35,73,639 verified against document format. 180-day validity confirmed.',
      time: '2 hours ago',
      badge: 'ACCEPTED',
      badgeColor: '#34d399',
    },
    {
      type: 'officer_override',
      title: 'Name Variation Accepted with Cross-Check (FND-05)',
      details: 'Trade name abbreviation "Pvt. Ltd." reconciled with legal entity name "Private Limited" via PAN AAACA9182K continuity.',
      time: '4 hours ago',
      badge: 'OVERRIDE',
      badgeColor: '#fbbf24',
    },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Top Banner: Active Tender Procurement Spotlight */}
      <div
        style={{
          background: 'linear-gradient(135deg, #1e3a8a 0%, #2563eb 100%)',
          border: '1px solid rgba(59, 130, 246, 0.25)',
          borderRadius: 'var(--radius-xl)',
          padding: '24px 28px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          boxShadow: '0 10px 25px -5px rgba(37, 99, 235, 0.25)',
        }}
      >
        <div style={{ maxWidth: '820px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
            <span className="badge badge-blue">ACTIVE TENDER SPOTLIGHT</span>
            <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
              GeM Bid Number: <strong style={{ color: '#ffffff' }}>{currentTender.tender_number}</strong>
            </span>
            <span className="badge badge-conditional">{currentTender.status}</span>
          </div>

          <h1 style={{ fontSize: '1.45rem', fontWeight: 800, color: '#ffffff', letterSpacing: '-0.02em', marginBottom: '6px' }}>
            {currentTender.title}
          </h1>

          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '18px', marginTop: '12px', fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
            <div>
              <span style={{ color: 'var(--text-muted)' }}>Procuring Organization:</span>{' '}
              <strong style={{ color: '#ffffff' }}>{currentTender.issuing_authority}</strong>
            </div>
            <div>
              <span style={{ color: 'var(--text-muted)' }}>Estimated Value:</span>{' '}
              <strong style={{ color: 'var(--brand-cyan)' }}>{currentTender.estimated_value_display || '₹7.14 Cr'}</strong>
            </div>
            <div>
              <span style={{ color: 'var(--text-muted)' }}>Turnover Rule:</span>{' '}
              <strong style={{ color: '#ffffff' }}>≥ ₹357.36 Lakhs</strong>
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', minWidth: '220px' }}>
          <button className="btn btn-primary" onClick={() => onNavigate('applications')}>
            <FolderKanban size={16} /> Open Bidder Application
          </button>
          <button className="btn btn-secondary" onClick={() => onNavigate('verification')}>
            <ShieldCheck size={16} /> Document Verification Center
          </button>
        </div>
      </div>

      {/* 4 Main Verification Overview Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '18px' }}>
        {/* Card 1: Requirements Verified */}
        <div className="glass-card" style={{ cursor: 'pointer' }} onClick={() => onNavigate('compliance')}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Requirements Verified</span>
            <div style={{ padding: '6px', borderRadius: '6px', background: 'rgba(16, 185, 129, 0.15)', color: '#34d399' }}>
              <CheckCircle2 size={18} />
            </div>
          </div>
          <div style={{ fontSize: '1.9rem', fontWeight: 800, color: 'var(--text-primary)', marginBottom: '4px' }}>
            {verifiedCount} <span style={{ fontSize: '1rem', color: 'var(--text-muted)', fontWeight: 500 }}>/ {totalReqs}</span>
          </div>
          <div style={{ fontSize: '0.74rem', color: '#10b981', fontWeight: 600 }}>
            60% Requirements Fully Compliant
          </div>
        </div>

        {/* Card 2: Applications & Documents Processed */}
        <div className="glass-card" style={{ cursor: 'pointer' }} onClick={() => onNavigate('applications')}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Bidder Applications</span>
            <div style={{ padding: '6px', borderRadius: '6px', background: 'rgba(59, 130, 246, 0.15)', color: '#60a5fa' }}>
              <FolderKanban size={18} />
            </div>
          </div>
          <div style={{ fontSize: '1.9rem', fontWeight: 800, color: 'var(--text-primary)', marginBottom: '4px' }}>
            1 Package <span style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>(6 Docs / 16 Pgs)</span>
          </div>
          <div style={{ fontSize: '0.74rem', color: '#60a5fa', fontWeight: 600 }}>
            100% Text & Clauses Extracted
          </div>
        </div>

        {/* Card 3: Issues Requiring Officer Action */}
        <div className="glass-card" style={{ cursor: 'pointer' }} onClick={() => onNavigate('findings')}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Review Findings</span>
            <div style={{ padding: '6px', borderRadius: '6px', background: 'rgba(239, 68, 68, 0.15)', color: '#f87171' }}>
              <AlertTriangle size={18} />
            </div>
          </div>
          <div style={{ fontSize: '1.9rem', fontWeight: 800, color: 'var(--text-primary)', marginBottom: '4px' }}>
            {effectiveFindings.length} Findings <span style={{ fontSize: '0.9rem', color: '#f87171' }}>({criticalFindings + highFindings} Critical/High)</span>
          </div>
          <div style={{ fontSize: '0.74rem', color: '#f59e0b', fontWeight: 600 }}>
            {openFindingsCount} Open Findings · {partialCount} Partial · {evidenceMissingCount} Missing
          </div>
        </div>

        {/* Card 4: Officer Decision Support Safeguard */}
        <div className="glass-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Authority Safeguard</span>
            <div style={{ padding: '6px', borderRadius: '6px', background: 'rgba(16, 185, 129, 0.15)', color: '#34d399' }}>
              <UserCheck size={18} />
            </div>
          </div>
          <div style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '4px' }}>
            Non-Autonomous
          </div>
          <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)', lineHeight: 1.35 }}>
            No winner declaration. All findings submitted for human procurement evaluation.
          </div>
        </div>
      </div>

      {/* Middle Grid: Detailed Verification Breakdown & Risk Overview */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '20px' }}>
        {/* Verification Overview Section */}
        <div className="glass-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <div>
              <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                Verification Breakdown
              </h3>
              <p style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
                Detailed status distribution across all 10 tender requirements
              </p>
            </div>
            <button className="btn btn-secondary" style={{ fontSize: '0.76rem', padding: '6px 12px' }} onClick={() => onNavigate('verification')}>
              View Matrix <ChevronRight size={14} />
            </button>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '12px' }}>
            <div style={{ background: 'var(--bg-tertiary)', padding: '12px 14px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                <span className="badge badge-compliant">COMPLIANT</span>
                <strong style={{ fontSize: '1.2rem', color: '#34d399' }}>{verifiedCount}</strong>
              </div>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                Identity, local office, EMD, statutory codes, ISO, minimum wages
              </div>
            </div>

            <div style={{ background: 'var(--bg-tertiary)', padding: '12px 14px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                <span className="badge badge-evidence-missing">EVIDENCE MISSING</span>
                <strong style={{ fontSize: '1.2rem', color: '#fb7185' }}>{evidenceMissingCount}</strong>
              </div>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                Annexure-9 VVIP security affidavit omitted from dossier
              </div>
            </div>

            <div style={{ background: 'var(--bg-tertiary)', padding: '12px 14px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                <span className="badge badge-partial">PARTIAL</span>
                <strong style={{ fontSize: '1.2rem', color: '#fbbf24' }}>{partialCount}</strong>
              </div>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                Turnover discrepancy (₹80.15L) & Project 3 below threshold
              </div>
            </div>

            <div style={{ background: 'var(--bg-tertiary)', padding: '12px 14px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                <span className="badge badge-clarification">CLARIFICATION PENDING</span>
                <strong style={{ fontSize: '1.2rem', color: '#a78bfa' }}>{clarificationPendingCount}</strong>
              </div>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                Typing speed 15,000 depressions/hr self-declaration
              </div>
            </div>
          </div>
        </div>

        {/* Risk & Severity Overview */}
        <div className="glass-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <div>
              <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                Risk & Findings Severity
              </h3>
              <p style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
                Commercial and technical deviations flagged for officer review
              </p>
            </div>
            <button className="btn btn-secondary" style={{ fontSize: '0.76rem', padding: '6px 12px' }} onClick={() => onNavigate('findings')}>
              Open Findings ({findings.length})
            </button>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 14px', background: 'rgba(239, 68, 68, 0.1)', borderRadius: 'var(--radius-md)', border: '1px solid rgba(239, 68, 68, 0.25)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#ef4444' }} />
                <div>
                  <div style={{ fontSize: '0.82rem', fontWeight: 700, color: '#f87171' }}>Critical Severity</div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Mandatory document omission (Annexure-9)</div>
                </div>
              </div>
              <strong style={{ fontSize: '1.1rem', color: '#f87171' }}>{criticalFindings}</strong>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 14px', background: 'rgba(249, 115, 22, 0.1)', borderRadius: 'var(--radius-md)', border: '1px solid rgba(249, 115, 22, 0.25)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#f97316' }} />
                <div>
                  <div style={{ fontSize: '0.82rem', fontWeight: 700, color: '#fb923c' }}>High Severity</div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Cross-document financial mismatch (₹80.15 Lakhs)</div>
                </div>
              </div>
              <strong style={{ fontSize: '1.1rem', color: '#fb923c' }}>{highFindings}</strong>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 14px', background: 'rgba(245, 158, 11, 0.1)', borderRadius: 'var(--radius-md)', border: '1px solid rgba(245, 158, 11, 0.25)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#f59e0b' }} />
                <div>
                  <div style={{ fontSize: '0.82rem', fontWeight: 700, color: '#fbbf24' }}>Medium Severity</div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Experience Project 3 shortfall and missing completion cert</div>
                </div>
              </div>
              <strong style={{ fontSize: '1.1rem', color: '#fbbf24' }}>{mediumFindings}</strong>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 14px', background: 'rgba(59, 130, 246, 0.1)', borderRadius: 'var(--radius-md)', border: '1px solid rgba(59, 130, 246, 0.25)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#3b82f6' }} />
                <div>
                  <div style={{ fontSize: '0.82rem', fontWeight: 700, color: '#60a5fa' }}>Low Severity / Informational</div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Typing speed ambiguity & entity name normalization</div>
                </div>
              </div>
              <strong style={{ fontSize: '1.1rem', color: '#60a5fa' }}>{lowFindings}</strong>
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Section: Recent Officer Actions */}
      <div className="glass-card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <div>
            <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-primary)' }}>
              Recent Officer Verification Actions
            </h3>
            <p style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
              Audit-recorded decisions and human review events for GeM bid evaluation
            </p>
          </div>
          <button className="btn btn-secondary" style={{ fontSize: '0.76rem', padding: '6px 12px' }} onClick={() => onNavigate('audit')}>
            View Immutable Audit Trail <ChevronRight size={14} />
          </button>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {recentOfficerActions.map((action, idx) => (
            <div
              key={idx}
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '12px 16px',
                background: 'var(--bg-tertiary)',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--border-subtle)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                <span
                  style={{
                    padding: '3px 8px',
                    borderRadius: '4px',
                    background: `${action.badgeColor}20`,
                    color: action.badgeColor,
                    fontSize: '0.68rem',
                    fontWeight: 700,
                    letterSpacing: '0.04em',
                  }}
                >
                  {action.badge}
                </span>
                <div>
                  <div style={{ fontSize: '0.86rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                    {action.title}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                    {action.details}
                  </div>
                </div>
              </div>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
                {action.time}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

import React, { useState } from 'react';
import {
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  FolderKanban,
  FileText,
  Building,
  CreditCard,
  Layers,
  ArrowDown,
  Info,
  ExternalLink,
  Filter,
} from 'lucide-react';
import { Bidder, Tender, DocumentVerificationCheck, DetailedVerificationResult } from '../types';
import {
  DEMO_CAG_TENDER,
  DEMO_BIDDER_APPLICATION,
  DEMO_VERIFICATION_CHECKS,
} from '../api/demoData';

interface VerificationCenterViewProps {
  verifications: any[];
  bidders: Bidder[];
  activeTender: Tender | null;
}

type VerificationCategory =
  | 'ALL'
  | 'Identity'
  | 'Financial'
  | 'Experience'
  | 'Statutory'
  | 'Authorization'
  | 'EMD'
  | 'Technical'
  | 'Declarations';

export const VerificationCenterView: React.FC<VerificationCenterViewProps> = ({
  verifications,
  bidders,
  activeTender,
}) => {
  const [selectedCategory, setSelectedCategory] = useState<VerificationCategory>('ALL');
  const [filterResult, setFilterResult] = useState<string>('ALL');

  // Load checks
  const checks: DocumentVerificationCheck[] = DEMO_VERIFICATION_CHECKS;

  const categories: VerificationCategory[] = [
    'ALL',
    'Identity',
    'Financial',
    'Experience',
    'Statutory',
    'Authorization',
    'EMD',
    'Technical',
    'Declarations',
  ];

  const filteredChecks = checks.filter((chk) => {
    const matchesCategory = selectedCategory === 'ALL' || chk.category === selectedCategory;
    const matchesResult = filterResult === 'ALL' || chk.result === filterResult;
    return matchesCategory && matchesResult;
  });

  const getResultBadge = (result: DetailedVerificationResult) => {
    switch (result) {
      case 'COMPLIANT':
        return <span className="badge badge-compliant">COMPLIANT</span>;
      case 'NON_COMPLIANT':
        return <span className="badge badge-noncompliant">NON_COMPLIANT</span>;
      case 'PARTIAL':
        return <span className="badge badge-partial">PARTIAL</span>;
      case 'EVIDENCE_MISSING':
        return <span className="badge badge-evidence-missing">EVIDENCE_MISSING</span>;
      case 'CLARIFICATION_PENDING':
        return <span className="badge badge-clarification">CLARIFICATION_PENDING</span>;
      case 'NOT_VERIFIABLE':
        return <span className="badge badge-not-verifiable">NOT_VERIFIABLE</span>;
      case 'NOT_EVALUATED':
      default:
        return <span className="badge badge-not-evaluated">NOT_EVALUATED</span>;
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '22px' }}>
      {/* Header bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <span className="badge badge-blue">Document Verification Center</span>
            <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
              GeM Bid: GEM/2021/B/1128240 · Manpower Hiring Services (CAG)
            </span>
          </div>
          <h1 style={{ fontSize: '1.45rem', fontWeight: 800, color: 'var(--text-primary)', letterSpacing: '-0.02em' }}>
            Document Verification Cards
          </h1>
          <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
            Each check inspects: Requirement → Submitted Evidence → Extraction → Verification → Result.
          </p>
        </div>

        <div style={{ textAlign: 'right' }}>
          <span className="badge badge-synthetic">DEMO BIDDER EVALUATION</span>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '4px' }}>
            Aravind Integrated Solutions Pvt. Ltd.
          </div>
        </div>
      </div>

      {/* External Portal Limitation Banner */}
      <div
        style={{
          background: 'rgba(30, 41, 59, 0.6)',
          border: '1px solid var(--border-subtle)',
          borderRadius: 'var(--radius-md)',
          padding: '12px 18px',
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
        }}
      >
        <Info size={18} color="var(--brand-cyan)" style={{ flexShrink: 0 }} />
        <div style={{ fontSize: '0.76rem', color: 'var(--text-secondary)', lineHeight: 1.45 }}>
          <strong style={{ color: 'var(--text-primary)' }}>External Portal Status: NOT_CONFIGURED / UNSUPPORTED_LOOKUP.</strong>{' '}
          In accordance with procurement evaluation policy, verification is performed strictly against submitted document evidence and format validation. BidGuard does NOT claim live government database confirmation.
        </div>
      </div>

      {/* Category Filter Tabs */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', alignItems: 'center' }}>
        <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontWeight: 600, marginRight: '4px' }}>
          Category:
        </span>
        {categories.map((cat) => {
          const isActive = selectedCategory === cat;
          const count = cat === 'ALL' ? checks.length : checks.filter((c) => c.category === cat).length;
          return (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              style={{
                background: isActive ? '#eff6ff' : '#f8fafc',
                color: isActive ? 'var(--brand-blue)' : 'var(--text-secondary)',
                border: isActive ? '1px solid #93c5fd' : '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-sm)',
                padding: '6px 12px',
                fontSize: '0.78rem',
                fontWeight: isActive ? 700 : 500,
                cursor: 'pointer',
                transition: 'all 0.15s ease',
              }}
            >
              {cat} ({count})
            </button>
          );
        })}
      </div>

      {/* Grid of Document Verification Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(580px, 1fr))', gap: '18px' }}>
        {filteredChecks.map((chk) => (
          <div
            key={chk.id}
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
              {/* Card Header */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '14px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <span
                    style={{
                      fontSize: '0.72rem',
                      fontWeight: 700,
                      fontFamily: 'var(--font-mono)',
                      color: 'var(--brand-cyan)',
                      background: 'rgba(6, 182, 212, 0.1)',
                      padding: '3px 8px',
                      borderRadius: '4px',
                      border: '1px solid rgba(6, 182, 212, 0.25)',
                    }}
                  >
                    {chk.id}
                  </span>
                  <span className="badge badge-blue">{chk.category}</span>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  {getResultBadge(chk.result)}
                </div>
              </div>

              <h3 style={{ fontSize: '1.02rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '4px' }}>
                {chk.requirement_title}
              </h3>
              <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)', marginBottom: '16px' }}>
                Clause Reference: {chk.requirement_clause}
              </div>

              {/* 5-Step Pipeline Layout */}
              <div
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '8px',
                  background: 'var(--bg-tertiary)',
                  padding: '14px',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--border-subtle)',
                  marginBottom: '16px',
                }}
              >
                {/* Step 1: Requirement */}
                <div>
                  <div style={{ fontSize: '0.68rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                    1. Tender Requirement
                  </div>
                  <div style={{ fontSize: '0.78rem', color: 'var(--text-primary)', marginTop: '2px', lineHeight: 1.4 }}>
                    {chk.requirement_text}
                  </div>
                </div>

                <div style={{ display: 'flex', justifyContent: 'center', color: 'var(--text-muted)', margin: '-2px 0' }}>
                  <ArrowDown size={14} />
                </div>

                {/* Step 2: Submitted Evidence */}
                <div>
                  <div style={{ fontSize: '0.68rem', fontWeight: 700, color: '#60a5fa', textTransform: 'uppercase' }}>
                    2. Submitted Evidence
                  </div>
                  <div style={{ fontSize: '0.78rem', color: '#e2e8f0', marginTop: '2px', fontWeight: 500 }}>
                    {chk.submitted_evidence}
                  </div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                    Source: {chk.source_document} (Page {chk.source_page})
                  </div>
                </div>

                <div style={{ display: 'flex', justifyContent: 'center', color: 'var(--text-muted)', margin: '-2px 0' }}>
                  <ArrowDown size={14} />
                </div>

                {/* Step 3: Extraction Details */}
                <div>
                  <div style={{ fontSize: '0.68rem', fontWeight: 700, color: '#34d399', textTransform: 'uppercase' }}>
                    3. AI Layout & Text Extraction
                  </div>
                  <div style={{ fontSize: '0.78rem', color: 'var(--text-primary)', marginTop: '2px', fontFamily: 'var(--font-mono)' }}>
                    {chk.extraction_details}
                  </div>
                  {chk.cross_document_evidence && (
                    <div style={{ fontSize: '0.74rem', color: '#fbbf24', marginTop: '4px' }}>
                      Cross-Check: {chk.cross_document_evidence}
                    </div>
                  )}
                  {chk.variance && (
                    <div style={{ fontSize: '0.74rem', color: '#f87171', marginTop: '2px', fontWeight: 600 }}>
                      Variance: {chk.variance}
                    </div>
                  )}
                </div>

                <div style={{ display: 'flex', justifyContent: 'center', color: 'var(--text-muted)', margin: '-2px 0' }}>
                  <ArrowDown size={14} />
                </div>

                {/* Step 4: Verification Method */}
                <div>
                  <div style={{ fontSize: '0.68rem', fontWeight: 700, color: 'var(--brand-cyan)', textTransform: 'uppercase' }}>
                    4. Verification Method
                  </div>
                  <div style={{ fontSize: '0.76rem', color: 'var(--text-secondary)', marginTop: '2px' }}>
                    {chk.verification_method}
                  </div>
                </div>

                <div style={{ display: 'flex', justifyContent: 'center', color: 'var(--text-muted)', margin: '-2px 0' }}>
                  <ArrowDown size={14} />
                </div>

                {/* Step 5: Result */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '4px' }}>
                  <div>
                    <div style={{ fontSize: '0.68rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                      5. Final Check Result
                    </div>
                    <div style={{ fontSize: '0.84rem', fontWeight: 700, marginTop: '2px' }}>
                      {getResultBadge(chk.result)}
                    </div>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>Confidence</div>
                    <div style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                      {chk.confidence}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Footer action / finding link */}
            {chk.finding_id && (
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  background: 'rgba(239, 68, 68, 0.1)',
                  padding: '8px 12px',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid rgba(239, 68, 68, 0.25)',
                }}
              >
                <div style={{ fontSize: '0.74rem', color: '#f87171', fontWeight: 600 }}>
                  Associated Finding: {chk.finding_id} — {chk.finding_title}
                </div>
                <span className="badge badge-noncompliant" style={{ fontSize: '0.66rem' }}>
                  REVIEW REQD
                </span>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

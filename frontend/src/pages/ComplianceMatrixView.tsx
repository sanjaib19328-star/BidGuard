import React, { useState } from 'react';
import {
  FileSpreadsheet,
  CheckCircle2,
  AlertTriangle,
  ExternalLink,
  Search,
  Filter,
  Eye,
  X,
  FileText,
  Building,
  ChevronRight,
} from 'lucide-react';
import { Tender, Bidder, DetailedVerificationResult } from '../types';
import {
  DEMO_CAG_TENDER,
  DEMO_BIDDER_APPLICATION,
  DEMO_VERIFICATION_CHECKS,
} from '../api/demoData';

interface ComplianceMatrixViewProps {
  matrixItems: any[];
  activeTender: Tender | null;
  bidders: Bidder[];
  onNavigate: (tab: any) => void;
}

export const ComplianceMatrixView: React.FC<ComplianceMatrixViewProps> = ({
  matrixItems,
  activeTender,
  bidders,
  onNavigate,
}) => {
  const currentTender = activeTender || DEMO_CAG_TENDER;
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [selectedRow, setSelectedRow] = useState<any | null>(null);

  const checks = DEMO_VERIFICATION_CHECKS;

  const filteredChecks = checks.filter((c) => {
    const matchesSearch =
      c.requirement_title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      c.submitted_evidence.toLowerCase().includes(searchTerm.toLowerCase()) ||
      c.verification_method.toLowerCase().includes(searchTerm.toLowerCase()) ||
      c.source_document.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'ALL' || c.result === statusFilter;
    return matchesSearch && matchesStatus;
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
            <span className="badge badge-blue">{currentTender.tender_number}</span>
            <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
              Procurement Verification Matrix
            </span>
          </div>
          <h1 style={{ fontSize: '1.45rem', fontWeight: 800, color: 'var(--text-primary)', letterSpacing: '-0.02em' }}>
            Compliance Matrix
          </h1>
          <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
            Cross-examination of mandatory tender requirements against submitted bidder documentation. Click any row to inspect underlying evidence.
          </p>
        </div>

        <div style={{ textAlign: 'right' }}>
          <span className="badge badge-synthetic">DEMO BIDDER</span>
          <div style={{ fontSize: '0.74rem', color: 'var(--text-primary)', fontWeight: 600, marginTop: '4px' }}>
            {DEMO_BIDDER_APPLICATION.bidder_name}
          </div>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
            CIN: {DEMO_BIDDER_APPLICATION.cin}
          </div>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div
        className="glass-card"
        style={{
          padding: '14px 20px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          gap: '16px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flex: 1 }}>
          <Search size={17} color="var(--text-muted)" />
          <input
            type="text"
            placeholder="Search requirement, evidence, or source document..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{
              background: 'transparent',
              border: 'none',
              color: 'var(--text-primary)',
              fontSize: '0.85rem',
              outline: 'none',
              width: '100%',
            }}
          />
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Filter size={15} color="var(--text-muted)" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            style={{
              background: 'var(--bg-tertiary)',
              color: 'var(--text-primary)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-sm)',
              padding: '6px 12px',
              fontSize: '0.8rem',
              outline: 'none',
              cursor: 'pointer',
            }}
          >
            <option value="ALL">All Statuses ({checks.length})</option>
            <option value="COMPLIANT">COMPLIANT (6)</option>
            <option value="PARTIAL">PARTIAL (2)</option>
            <option value="EVIDENCE_MISSING">EVIDENCE_MISSING (1)</option>
            <option value="CLARIFICATION_PENDING">CLARIFICATION_PENDING (1)</option>
            <option value="NOT_VERIFIABLE">NOT_VERIFIABLE (0)</option>
            <option value="NOT_EVALUATED">NOT_EVALUATED (0)</option>
          </select>
        </div>
      </div>

      {/* Main Compliance Matrix Table */}
      <div className="glass-card" style={{ padding: '0', overflow: 'hidden' }}>
        <table className="custom-table">
          <thead>
            <tr>
              <th style={{ width: '20%' }}>Requirement</th>
              <th style={{ width: '16%' }}>Application</th>
              <th style={{ width: '22%' }}>Evidence</th>
              <th style={{ width: '18%' }}>Verification</th>
              <th style={{ width: '10%' }}>Status</th>
              <th style={{ width: '6%' }}>Conf.</th>
              <th style={{ width: '8%' }}>Source</th>
            </tr>
          </thead>
          <tbody>
            {filteredChecks.map((row) => (
              <tr
                key={row.id}
                onClick={() => setSelectedRow(row)}
                style={{ cursor: 'pointer', transition: 'background 0.15s ease' }}
              >
                <td>
                  <div style={{ fontSize: '0.84rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                    {row.requirement_title}
                  </div>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                    {row.requirement_clause}
                  </div>
                </td>

                <td>
                  <div style={{ fontSize: '0.78rem', color: 'var(--brand-cyan)', fontWeight: 600 }}>
                    Aravind Integrated Solutions
                  </div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                    APP-001
                  </div>
                  {row.finding_id && (
                    <div style={{ marginTop: '3px' }}>
                      <span
                        className="badge badge-noncompliant"
                        style={{ fontSize: '0.62rem', padding: '1px 5px', cursor: 'pointer' }}
                        onClick={(e) => {
                          e.stopPropagation();
                          onNavigate('findings');
                        }}
                        title={`Inspect finding ${row.finding_id}`}
                      >
                        {row.finding_id}
                      </span>
                    </div>
                  )}
                </td>

                <td>
                  <div style={{ fontSize: '0.8rem', color: '#e2e8f0', lineHeight: 1.35 }}>
                    {row.submitted_evidence}
                  </div>
                  {row.cross_document_evidence && (
                    <div style={{ fontSize: '0.72rem', color: '#fbbf24', marginTop: '3px' }}>
                      Cross-Check: {row.cross_document_evidence}
                    </div>
                  )}
                </td>

                <td>
                  <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                    {row.variance ? (
                      <span style={{ color: '#f87171', fontWeight: 600 }}>{row.variance}</span>
                    ) : (
                      row.verification_method
                    )}
                  </div>
                </td>

                <td>{getResultBadge(row.result)}</td>

                <td>
                  <span
                    style={{
                      fontSize: '0.74rem',
                      fontWeight: 700,
                      color: row.confidence === 'HIGH' ? '#34d399' : '#fbbf24',
                    }}
                  >
                    {row.confidence}
                  </span>
                </td>

                <td>
                  <div style={{ fontSize: '0.74rem', color: '#60a5fa', fontFamily: 'var(--font-mono)' }}>
                    {row.source_document.slice(0, 12)}...
                  </div>
                  <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>
                    Page {row.source_page}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Row Evidence Details Modal */}
      {selectedRow && (
        <div className="modal-backdrop" onClick={() => setSelectedRow(null)}>
          <div
            className="modal-content"
            onClick={(e) => e.stopPropagation()}
            style={{ maxWidth: '640px' }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <FileSpreadsheet size={20} color="var(--brand-cyan)" />
                <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                  Evidence & Verification Citation
                </h3>
              </div>
              <button
                onClick={() => setSelectedRow(null)}
                style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
              >
                <X size={18} />
              </button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', fontSize: '0.82rem' }}>
              {/* Application Context */}
              <div style={{ background: 'rgba(59, 130, 246, 0.08)', padding: '10px 14px', borderRadius: 'var(--radius-md)', border: '1px solid rgba(59, 130, 246, 0.25)' }}>
                <div style={{ fontSize: '0.68rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                  Bidder Application
                </div>
                <div style={{ fontSize: '0.86rem', fontWeight: 700, color: 'var(--brand-cyan)', marginTop: '2px' }}>
                  Aravind Integrated Solutions Private Limited (DEMO)
                </div>
                <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                  Application ID: APP-001 · 1 Application Package
                </div>
              </div>

              {selectedRow.finding_id && (
                <div style={{ background: 'rgba(239, 68, 68, 0.1)', padding: '10px 14px', borderRadius: 'var(--radius-md)', border: '1px solid rgba(239, 68, 68, 0.3)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <div style={{ fontSize: '0.68rem', fontWeight: 700, color: '#f87171', textTransform: 'uppercase' }}>
                      Associated Finding
                    </div>
                    <div style={{ fontSize: '0.84rem', fontWeight: 700, color: 'var(--text-primary)', marginTop: '2px' }}>
                      {selectedRow.finding_id}: {selectedRow.finding_title}
                    </div>
                  </div>
                  <button
                    className="btn btn-secondary"
                    style={{ fontSize: '0.72rem', padding: '4px 10px' }}
                    onClick={() => {
                      setSelectedRow(null);
                      onNavigate('findings');
                    }}
                  >
                    Inspect Finding
                  </button>
                </div>
              )}

              <div style={{ background: 'var(--bg-tertiary)', padding: '12px 14px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                <div style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                  Requirement Clause
                </div>
                <div style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--text-primary)', marginTop: '2px' }}>
                  {selectedRow.requirement_title} ({selectedRow.requirement_clause})
                </div>
                <div style={{ color: 'var(--text-secondary)', marginTop: '4px', lineHeight: 1.4 }}>
                  {selectedRow.requirement_text}
                </div>
              </div>

              <div style={{ background: 'var(--bg-tertiary)', padding: '12px 14px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                <div style={{ fontSize: '0.7rem', fontWeight: 700, color: '#60a5fa', textTransform: 'uppercase' }}>
                  Submitted Bidder Evidence
                </div>
                <div style={{ color: 'var(--text-primary)', marginTop: '2px', fontWeight: 600 }}>
                  {selectedRow.submitted_evidence}
                </div>
                <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                  Source: <strong>{selectedRow.source_document}</strong> (Page {selectedRow.source_page})
                </div>
              </div>

              {selectedRow.cross_document_evidence && (
                <div style={{ background: 'rgba(245, 158, 11, 0.1)', padding: '12px 14px', borderRadius: 'var(--radius-md)', border: '1px solid rgba(245, 158, 11, 0.3)' }}>
                  <div style={{ fontSize: '0.7rem', fontWeight: 700, color: '#fbbf24', textTransform: 'uppercase' }}>
                    Cross-Document Finding
                  </div>
                  <div style={{ color: 'var(--text-primary)', marginTop: '2px' }}>
                    {selectedRow.cross_document_evidence}
                  </div>
                  {selectedRow.variance && (
                    <div style={{ color: '#f87171', fontWeight: 600, marginTop: '2px' }}>
                      Variance: {selectedRow.variance}
                    </div>
                  )}
                </div>
              )}

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'var(--bg-tertiary)', padding: '10px 14px', borderRadius: 'var(--radius-md)' }}>
                <div>
                  <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Status: </span>
                  {getResultBadge(selectedRow.result)}
                </div>
                <div>
                  <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Confidence: </span>
                  <strong style={{ color: 'var(--text-primary)' }}>{selectedRow.confidence}</strong>
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '18px' }}>
              <button
                className="btn btn-primary"
                onClick={() => {
                  setSelectedRow(null);
                  onNavigate('applications');
                }}
              >
                Inspect in Application Workspace <ChevronRight size={15} />
              </button>
              <button className="btn btn-secondary" onClick={() => setSelectedRow(null)}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

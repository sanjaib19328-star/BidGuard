import React, { useState } from 'react';
import {
  Shield,
  Info,
  FolderKanban,
  PlusCircle,
  Eye,
  X,
} from 'lucide-react';
import { Bidder, Tender } from '../types';
import {
  DEMO_CAG_TENDER,
  DEMO_BIDDER_APPLICATION,
  DEMO_FINDINGS,
} from '../api/demoData';

interface ComparisonViewProps {
  bidders: Bidder[];
  activeTender: Tender | null;
  onNavigate: (tab: any) => void;
}

export const ComparisonView: React.FC<ComparisonViewProps> = ({
  bidders: _bidders,
  activeTender,
  onNavigate,
}) => {
  const currentTender = activeTender || DEMO_CAG_TENDER;
  const application = DEMO_BIDDER_APPLICATION;
  const [selectedAppModal, setSelectedAppModal] = useState<boolean>(false);
  const [addAppNotice, setAddAppNotice] = useState<string | null>(null);

  // Exact metrics required by specification
  const applicationsReceived = 1;
  const fullyVerified = 0;
  const pendingVerification = 1;
  const clarificationPending = 1;
  const openFindings = 4; // 4 pending review or clarification
  const criticalFindings = 1; // FND-01
  const highFindings = 1; // FND-02
  const documentsSubmitted = 6;

  const handleAddBidderClick = () => {
    setAddAppNotice(
      "To add another application, upload the bidder's application package through the Applications Workspace. Once a second application is registered, the comparison workspace will become available."
    );
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '22px' }}>
      {/* Top Header Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '14px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <span className="badge badge-blue">{currentTender.tender_number}</span>
          </div>
          <h1 style={{ fontSize: '1.45rem', fontWeight: 800, color: 'var(--text-primary)', letterSpacing: '-0.02em', marginBottom: '4px' }}>
            Multi-Bidder Comparison
          </h1>
          <div style={{ fontSize: '0.84rem', fontWeight: 700, color: '#60a5fa', marginBottom: '4px' }}>
            Tender: {currentTender.tender_number}
          </div>
          <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: 1.45 }}>
            Application-level comparison and verification status. Each bidder application is evaluated from its submitted evidence, verification checks, compliance state, and officer findings.
          </p>
        </div>

        <div style={{ textAlign: 'right' }}>
          <div style={{ fontSize: '0.78rem', color: '#10b981', fontWeight: 700 }}>
            NON-AUTONOMOUS EVALUATION
          </div>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
            No winner declaration or automated ranking
          </div>
        </div>
      </div>

      {/* Strict Non-Autonomous Guardrail Banner */}
      <div
        style={{
          background: 'rgba(16, 185, 129, 0.08)',
          border: '1px solid rgba(16, 185, 129, 0.25)',
          borderRadius: 'var(--radius-md)',
          padding: '12px 18px',
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
        }}
      >
        <Shield size={18} color="#10b981" style={{ flexShrink: 0 }} />
        <div style={{ fontSize: '0.76rem', color: '#a7f3d0', lineHeight: 1.45 }}>
          <strong>Statutory Procurement Notice:</strong> BidGuard AI compares submitted bidder applications strictly on documentary evidence and verification results. The system does NOT calculate a "bidder score", does NOT rank bidders, and does NOT declare a winner. Award authority strictly rests with the designated Procurement Officer and Tender Committee.
        </div>
      </div>

      {/* Top 8 Summary Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(135px, 1fr))', gap: '12px' }}>
        <div className="glass-card" style={{ padding: '14px 16px', background: 'var(--bg-card)' }}>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: '4px' }}>Applications Received</div>
          <div style={{ fontSize: '1.45rem', fontWeight: 800, color: 'var(--text-primary)' }}>{applicationsReceived}</div>
          <div style={{ fontSize: '0.68rem', color: '#60a5fa', marginTop: '2px' }}>1 Package</div>
        </div>

        <div className="glass-card" style={{ padding: '14px 16px', background: 'var(--bg-card)' }}>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: '4px' }}>Fully Verified</div>
          <div style={{ fontSize: '1.45rem', fontWeight: 800, color: '#94a3b8' }}>{fullyVerified}</div>
          <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', marginTop: '2px' }}>Pending final sign-off</div>
        </div>

        <div className="glass-card" style={{ padding: '14px 16px', background: 'var(--bg-card)' }}>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: '4px' }}>Pending Verification</div>
          <div style={{ fontSize: '1.45rem', fontWeight: 800, color: '#fbbf24' }}>{pendingVerification}</div>
          <div style={{ fontSize: '0.68rem', color: '#fbbf24', marginTop: '2px' }}>APP-001 In Review</div>
        </div>

        <div className="glass-card" style={{ padding: '14px 16px', background: 'var(--bg-card)' }}>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: '4px' }}>Clarification Pending</div>
          <div style={{ fontSize: '1.45rem', fontWeight: 800, color: '#a78bfa' }}>{clarificationPending}</div>
          <div style={{ fontSize: '0.68rem', color: '#a78bfa', marginTop: '2px' }}>Turnover discrepancy</div>
        </div>

        <div className="glass-card" style={{ padding: '14px 16px', background: 'var(--bg-card)' }}>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: '4px' }}>Open Findings</div>
          <div style={{ fontSize: '1.45rem', fontWeight: 800, color: '#f87171' }}>{openFindings}</div>
          <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', marginTop: '2px' }}>Total 5 Findings</div>
        </div>

        <div className="glass-card" style={{ padding: '14px 16px', background: 'var(--bg-card)' }}>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: '4px' }}>Critical Findings</div>
          <div style={{ fontSize: '1.45rem', fontWeight: 800, color: '#ef4444' }}>{criticalFindings}</div>
          <div style={{ fontSize: '0.68rem', color: '#f87171', marginTop: '2px' }}>Annexure-9 Omission</div>
        </div>

        <div className="glass-card" style={{ padding: '14px 16px', background: 'var(--bg-card)' }}>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: '4px' }}>High Findings</div>
          <div style={{ fontSize: '1.45rem', fontWeight: 800, color: '#fb923c' }}>{highFindings}</div>
          <div style={{ fontSize: '0.68rem', color: '#fb923c', marginTop: '2px' }}>₹80.15L Turnover Variance</div>
        </div>

        <div className="glass-card" style={{ padding: '14px 16px', background: 'var(--bg-card)' }}>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: '4px' }}>Documents Submitted</div>
          <div style={{ fontSize: '1.45rem', fontWeight: 800, color: '#34d399' }}>{documentsSubmitted}</div>
          <div style={{ fontSize: '0.68rem', color: '#34d399', marginTop: '2px' }}>16 Pages Extracted</div>
        </div>
      </div>

      {/* Application Comparison Table */}
      <div className="glass-card" style={{ padding: '0', overflow: 'hidden' }}>
        <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border-subtle)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h3 style={{ fontSize: '1.02rem', fontWeight: 700, color: 'var(--text-primary)' }}>
              Participating Bidder Applications ({applicationsReceived})
            </h3>
            <p style={{ fontSize: '0.74rem', color: 'var(--text-muted)', marginTop: '2px' }}>
              Application-level documentary and verification standing across submitted packages
            </p>
          </div>
          <span className="badge badge-blue">1 Tender · 1 Bidder Application · 5 Findings</span>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table className="custom-table" style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr>
                <th style={{ width: '9%' }}>Application</th>
                <th style={{ width: '19%' }}>Bidder</th>
                <th style={{ width: '9%' }}>Documents</th>
                <th style={{ width: '9%' }}>Verification</th>
                <th style={{ width: '22%' }}>Compliance</th>
                <th style={{ width: '6%' }}>Critical</th>
                <th style={{ width: '6%' }}>High</th>
                <th style={{ width: '9%' }}>Clarification</th>
                <th style={{ width: '9%' }}>Officer Review</th>
                <th style={{ width: '11%' }}>Action</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>
                  <div style={{ fontSize: '0.82rem', fontWeight: 800, color: 'var(--brand-cyan)', fontFamily: 'var(--font-mono)' }}>
                    APP-001
                  </div>
                  <span className="badge badge-synthetic" style={{ fontSize: '0.62rem', padding: '1px 5px' }}>
                    DEMO
                  </span>
                </td>

                <td>
                  <div style={{ fontSize: '0.84rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                    {application.bidder_name}
                  </div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                    CIN: {application.cin}
                  </div>
                </td>

                <td>
                  <div style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                    6 / 6
                  </div>
                  <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>
                    16 Pages
                  </div>
                </td>

                <td>
                  <span className="badge badge-partial" style={{ fontSize: '0.72rem' }}>
                    PENDING
                  </span>
                </td>

                <td>
                  <div style={{ fontSize: '0.76rem', color: '#e2e8f0', lineHeight: 1.4 }}>
                    <span style={{ color: '#34d399', fontWeight: 700 }}>6 Compliant</span> /{' '}
                    <span style={{ color: '#fbbf24', fontWeight: 700 }}>2 Partial</span> /{' '}
                    <span style={{ color: '#f87171', fontWeight: 700 }}>1 Missing</span> /{' '}
                    <span style={{ color: '#a78bfa', fontWeight: 700 }}>1 Clarification Pending</span>
                  </div>
                </td>

                <td>
                  <div style={{ fontSize: '0.88rem', fontWeight: 800, color: '#ef4444' }}>
                    1
                  </div>
                </td>

                <td>
                  <div style={{ fontSize: '0.88rem', fontWeight: 800, color: '#fb923c' }}>
                    1
                  </div>
                </td>

                <td>
                  <span className="badge badge-clarification" style={{ fontSize: '0.7rem' }}>
                    REQUIRED
                  </span>
                </td>

                <td>
                  <span className="badge badge-review" style={{ fontSize: '0.7rem' }}>
                    PENDING
                  </span>
                </td>

                <td>
                  <div style={{ display: 'flex', gap: '6px' }}>
                    <button
                      className="btn btn-primary"
                      style={{ fontSize: '0.72rem', padding: '5px 10px' }}
                      onClick={() => onNavigate('applications')}
                      title="Open full application workspace"
                    >
                      Open Application
                    </button>
                    <button
                      className="btn btn-secondary"
                      style={{ fontSize: '0.72rem', padding: '5px 8px' }}
                      onClick={() => setSelectedAppModal(true)}
                      title="Inspect review summary"
                    >
                      <Eye size={13} />
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Empty / Single Application State Notice */}
      <div
        className="glass-card"
        style={{
          padding: '22px 26px',
          background: 'rgba(30, 58, 138, 0.12)',
          border: '1px solid rgba(59, 130, 246, 0.3)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '16px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '14px', maxWidth: '720px' }}>
          <Info size={22} color="#60a5fa" style={{ flexShrink: 0, marginTop: '2px' }} />
          <div>
            <h4 style={{ fontSize: '0.98rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '4px' }}>
              Single Application
            </h4>
            <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
              Only 1 bidder application is currently registered for this tender. Multi-bidder comparison requires 2 or more registered applications.
            </p>
          </div>
        </div>

        <button
          className="btn btn-primary"
          style={{ fontSize: '0.82rem', padding: '8px 18px', display: 'flex', alignItems: 'center', gap: '8px' }}
          onClick={handleAddBidderClick}
        >
          <PlusCircle size={15} /> + Add Bidder Application
        </button>
      </div>

      {addAppNotice && (
        <div
          style={{
            background: 'rgba(59, 130, 246, 0.15)',
            border: '1px solid rgba(59, 130, 246, 0.35)',
            color: '#93c5fd',
            padding: '14px 18px',
            borderRadius: 'var(--radius-md)',
            fontSize: '0.82rem',
            lineHeight: 1.5,
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <div>
            <strong>Ingestion Guidance:</strong> {addAppNotice}
          </div>
          <button
            onClick={() => setAddAppNotice(null)}
            style={{ background: 'transparent', border: 'none', color: '#93c5fd', cursor: 'pointer', padding: '4px' }}
          >
            <X size={16} />
          </button>
        </div>
      )}

      {/* APPLICATION DETAIL / REVIEW SUMMARY MODAL */}
      {selectedAppModal && (
        <div className="modal-backdrop" onClick={() => setSelectedAppModal(false)}>
          <div
            className="modal-content"
            onClick={(e) => e.stopPropagation()}
            style={{ maxWidth: '780px', width: '92%' }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '14px', marginBottom: '18px' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                  <span className="badge badge-blue">APP-001</span>
                  <span className="badge badge-synthetic">DEMO / SYNTHETIC</span>
                </div>
                <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--text-primary)' }}>
                  {application.bidder_name}
                </h2>
                <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                  Trade: {application.trade_name} · CIN: {application.cin}
                </div>
              </div>
              <button
                onClick={() => setSelectedAppModal(false)}
                style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', padding: '4px' }}
              >
                <X size={18} />
              </button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', fontSize: '0.82rem' }}>
              {/* Context Grid */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px' }}>
                <div style={{ background: 'var(--bg-tertiary)', padding: '10px 12px', borderRadius: 'var(--radius-sm)' }}>
                  <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>Submission Status</div>
                  <div style={{ fontSize: '0.84rem', fontWeight: 700, color: '#34d399', marginTop: '2px' }}>
                    Submitted On-Time
                  </div>
                  <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>24-03-2021 14:30</div>
                </div>

                <div style={{ background: 'var(--bg-tertiary)', padding: '10px 12px', borderRadius: 'var(--radius-sm)' }}>
                  <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>Documents Uploaded</div>
                  <div style={{ fontSize: '0.84rem', fontWeight: 700, color: 'var(--text-primary)', marginTop: '2px' }}>
                    {application.total_documents} PDF Files
                  </div>
                  <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>{application.total_pages} Total Pages</div>
                </div>

                <div style={{ background: 'var(--bg-tertiary)', padding: '10px 12px', borderRadius: 'var(--radius-sm)' }}>
                  <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>Officer Review Status</div>
                  <div style={{ fontSize: '0.84rem', fontWeight: 700, color: '#fbbf24', marginTop: '2px' }}>
                    Pending Committee Ruling
                  </div>
                  <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>5 Findings Flagged</div>
                </div>
              </div>

              {/* Compliance Breakdown */}
              <div style={{ background: 'var(--bg-tertiary)', padding: '12px 16px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                <div style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--brand-cyan)', textTransform: 'uppercase', marginBottom: '8px' }}>
                  Verification & Compliance Breakdown (10 Checks)
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '8px', textAlign: 'center' }}>
                  <div style={{ background: 'rgba(16, 185, 129, 0.1)', padding: '8px', borderRadius: '4px', border: '1px solid rgba(16, 185, 129, 0.25)' }}>
                    <div style={{ fontSize: '1.1rem', fontWeight: 800, color: '#34d399' }}>6</div>
                    <div style={{ fontSize: '0.68rem', color: '#a7f3d0' }}>Compliant</div>
                  </div>
                  <div style={{ background: 'rgba(245, 158, 11, 0.1)', padding: '8px', borderRadius: '4px', border: '1px solid rgba(245, 158, 11, 0.25)' }}>
                    <div style={{ fontSize: '1.1rem', fontWeight: 800, color: '#fbbf24' }}>2</div>
                    <div style={{ fontSize: '0.68rem', color: '#fef08a' }}>Partial</div>
                  </div>
                  <div style={{ background: 'rgba(239, 68, 68, 0.1)', padding: '8px', borderRadius: '4px', border: '1px solid rgba(239, 68, 68, 0.25)' }}>
                    <div style={{ fontSize: '1.1rem', fontWeight: 800, color: '#f87171' }}>1</div>
                    <div style={{ fontSize: '0.68rem', color: '#fecaca' }}>Missing</div>
                  </div>
                  <div style={{ background: 'rgba(168, 85, 247, 0.1)', padding: '8px', borderRadius: '4px', border: '1px solid rgba(168, 85, 247, 0.25)' }}>
                    <div style={{ fontSize: '1.1rem', fontWeight: 800, color: '#a78bfa' }}>1</div>
                    <div style={{ fontSize: '0.68rem', color: '#e9d5ff' }}>Clarification</div>
                  </div>
                </div>
              </div>

              {/* Findings List for this single application */}
              <div style={{ background: 'var(--bg-tertiary)', padding: '12px 16px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                <div style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '8px' }}>
                  Associated Risk Findings (5 Records for Application APP-001)
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  {DEMO_FINDINGS.map((f) => (
                    <div
                      key={f.id}
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        padding: '6px 10px',
                        background: 'var(--bg-tertiary)',
                        borderRadius: '4px',
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span style={{ fontSize: '0.72rem', fontWeight: 800, color: 'var(--brand-cyan)', fontFamily: 'var(--font-mono)' }}>
                          {f.id}
                        </span>
                        <span style={{ fontSize: '0.78rem', color: 'var(--text-primary)' }}>{f.title}</span>
                      </div>
                      <span
                        className={`badge ${
                          f.severity === 'CRITICAL' || f.severity === 'HIGH'
                            ? 'badge-noncompliant'
                            : 'badge-partial'
                        }`}
                        style={{ fontSize: '0.65rem' }}
                      >
                        {f.severity}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '20px', borderTop: '1px solid var(--border-subtle)', paddingTop: '14px' }}>
              <button
                className="btn btn-primary"
                onClick={() => {
                  setSelectedAppModal(false);
                  onNavigate('applications');
                }}
              >
                <FolderKanban size={15} /> Open Full Application Workspace
              </button>
              <button
                className="btn btn-secondary"
                onClick={() => {
                  setSelectedAppModal(false);
                  onNavigate('findings');
                }}
              >
                Inspect Risk & Findings
              </button>
              <button className="btn btn-secondary" onClick={() => setSelectedAppModal(false)}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

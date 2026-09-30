import React, { useState } from 'react';
import {
  Search,
  FileText,
  ChevronRight,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  FolderKanban,
  FileSpreadsheet,
  ArrowLeft,
  PlusCircle,
  X,
} from 'lucide-react';
import { Tender } from '../types';
import { DEMO_CAG_TENDER, DEMO_BIDDER_APPLICATION, DEMO_VERIFICATION_CHECKS } from '../api/demoData';

interface TendersViewProps {
  tenders: Tender[];
  activeTender: Tender | null;
  onSelectTender: (tender: Tender) => void;
  onNavigate: (tab: any) => void;
  onCreateTender?: (newTender: Tender) => void;
}

type TenderDetailTab =
  | 'overview'
  | 'requirements'
  | 'applications'
  | 'verification'
  | 'compliance'
  | 'findings'
  | 'dossier';

export const TendersView: React.FC<TendersViewProps> = ({
  tenders,
  activeTender,
  onSelectTender,
  onNavigate,
  onCreateTender,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedTenderForDetails, setSelectedTenderForDetails] = useState<Tender | null>(null);
  const [activeTab, setActiveTab] = useState<TenderDetailTab>('overview');

  // Add Tender Modal state
  const [isAddTenderOpen, setIsAddTenderOpen] = useState(false);
  const [newTenderForm, setNewTenderForm] = useState({
    tender_number: '',
    title: '',
    issuing_authority: '',
    tender_type: 'Services',
    estimated_value: '',
    emd_amount: '',
    deadline: '',
    description: '',
    category: '',
  });
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});
  const [localTenders, setLocalTenders] = useState<Tender[]>([]);

  // Ensure DEMO_CAG_TENDER is included in catalog
  const catalogTenders = tenders.some((t) => t.tender_number === DEMO_CAG_TENDER.tender_number)
    ? tenders
    : [DEMO_CAG_TENDER, ...tenders];

  // Combine with any locally added tenders
  const combinedTenders = [
    ...localTenders.filter((lt) => !catalogTenders.some((ct) => ct.tender_number === lt.tender_number)),
    ...catalogTenders,
  ];

  const filteredTenders = combinedTenders.filter(
    (t) =>
      t.tender_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
      t.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      t.issuing_authority.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (t.ministry && t.ministry.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  const handleCreateTenderSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const errors: Record<string, string> = {};
    if (!newTenderForm.tender_number.trim()) {
      errors.tender_number = 'Tender ID / GeM Bid Number is required';
    }
    if (!newTenderForm.title.trim()) {
      errors.title = 'Tender title is required';
    }
    if (!newTenderForm.issuing_authority.trim()) {
      errors.issuing_authority = 'Procuring organization is required';
    }
    const valNum = parseFloat(newTenderForm.estimated_value);
    if (!newTenderForm.estimated_value || isNaN(valNum) || valNum <= 0) {
      errors.estimated_value = 'Valid positive estimated value is required';
    }
    if (!newTenderForm.deadline) {
      errors.deadline = 'Submission deadline date is required';
    }

    if (Object.keys(errors).length > 0) {
      setFormErrors(errors);
      return;
    }

    const valCr = (valNum / 10000000).toFixed(2);
    const newTender: Tender = {
      id: newTenderForm.tender_number.trim(),
      tender_number: newTenderForm.tender_number.trim(),
      title: newTenderForm.title.trim(),
      issuing_authority: newTenderForm.issuing_authority.trim(),
      ministry: newTenderForm.issuing_authority.trim(),
      estimated_value: valNum,
      estimated_value_display: `₹${valCr} Cr`,
      emd_amount: newTenderForm.emd_amount ? parseFloat(newTenderForm.emd_amount) : undefined,
      mse_exemption_permitted: true,
      startup_exemption_permitted: true,
      status: 'DRAFT',
      created_at: new Date().toISOString(),
      total_clauses: 0,
      total_requirements: 0,
    };

    setLocalTenders((prev) => [newTender, ...prev]);
    if (onCreateTender) {
      onCreateTender(newTender);
    }
    onSelectTender(newTender);
    setSelectedTenderForDetails(newTender);
    setIsAddTenderOpen(false);
  };

  // If viewing detailed tabbed workflow for a specific tender
  if (selectedTenderForDetails) {
    const t = selectedTenderForDetails;
    const isDemoCAG = t.tender_number === DEMO_CAG_TENDER.tender_number;

    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '22px' }}>
        {/* Back Button */}
        <div>
          <button
            className="btn btn-secondary"
            style={{ fontSize: '0.8rem', padding: '6px 14px' }}
            onClick={() => setSelectedTenderForDetails(null)}
          >
            <ArrowLeft size={15} /> Back to Tender Catalog
          </button>
        </div>

        {/* Detailed Tender Header */}
        <div
          style={{
            background: 'var(--bg-card)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-xl)',
            padding: '24px 28px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'flex-start',
            gap: '20px',
          }}
        >
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
              <span
                style={{
                  fontSize: '0.78rem',
                  fontWeight: 700,
                  fontFamily: 'var(--font-mono)',
                  color: '#60a5fa',
                  background: 'rgba(59, 130, 246, 0.12)',
                  padding: '4px 10px',
                  borderRadius: '4px',
                  border: '1px solid rgba(59, 130, 246, 0.3)',
                }}
              >
                GeM Bid: {t.tender_number}
              </span>
              <span className="badge badge-conditional">{t.status}</span>
              {isDemoCAG && <span className="badge badge-blue">AUTHENTIC DEMO</span>}
            </div>

            <h1 style={{ fontSize: '1.45rem', fontWeight: 800, color: 'var(--text-primary)', letterSpacing: '-0.02em', marginBottom: '6px' }}>
              {t.title}
            </h1>

            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
              <strong>Organization:</strong> {t.issuing_authority}
            </p>
          </div>

          <div style={{ textAlign: 'right', display: 'flex', flexDirection: 'column', gap: '4px' }}>
            <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>Estimated Value</span>
            <span style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--brand-cyan)' }}>
              {t.estimated_value_display || '₹7.14 Cr'}
            </span>
            <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
              {isDemoCAG ? 'EMD: ₹35.73 Lakhs (SBI BG)' : (t.emd_amount ? `EMD: ₹${t.emd_amount}` : 'EMD: Not specified')}
            </span>
          </div>
        </div>

        {/* Progress Indicator Stepper */}
        <div className="workflow-stepper">
          <div className="stepper-step completed">
            <CheckCircle2 size={16} color="#10b981" />
            <span>Tender</span>
          </div>
          <span className="stepper-divider">→</span>

          <div className={`stepper-step ${isDemoCAG ? 'completed' : 'upcoming'}`}>
            {isDemoCAG ? <CheckCircle2 size={16} color="#10b981" /> : <FileText size={16} />}
            <span>Requirements {isDemoCAG ? '(10)' : '(0 Mapped)'}</span>
          </div>
          <span className="stepper-divider">→</span>

          <div className={`stepper-step ${isDemoCAG ? 'current' : 'upcoming'}`}>
            <FolderKanban size={16} color={isDemoCAG ? '#60a5fa' : undefined} />
            <span>Applications {isDemoCAG ? '(1)' : '(0)'}</span>
          </div>
          <span className="stepper-divider">→</span>

          <div className="stepper-step upcoming">
            <ShieldCheck size={16} />
            <span>Verification {isDemoCAG ? '(10 Checks)' : '(Not started)'}</span>
          </div>
          <span className="stepper-divider">→</span>

          <div className="stepper-step upcoming">
            <FileSpreadsheet size={16} />
            <span>Compliance Matrix</span>
          </div>
          <span className="stepper-divider">→</span>

          <div className="stepper-step upcoming">
            <AlertTriangle size={16} />
            <span>Findings {isDemoCAG ? '(5)' : '(0)'}</span>
          </div>
        </div>

        {/* Tab Navigation */}
        <div style={{ display: 'flex', gap: '6px', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '4px' }}>
          {[
            { id: 'overview', label: 'Overview' },
            { id: 'requirements', label: `Requirements (${isDemoCAG ? 10 : 0})` },
            { id: 'applications', label: `Bidder Applications (${isDemoCAG ? 1 : 0})` },
            { id: 'verification', label: `Verification (${isDemoCAG ? '10 Checks' : 'Not started'})` },
            { id: 'compliance', label: 'Compliance Matrix' },
            { id: 'findings', label: `Findings (${isDemoCAG ? 5 : 0})` },
            { id: 'dossier', label: 'Dossier' },
          ].map((tab) => {
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as TenderDetailTab)}
                style={{
                  background: isActive ? 'rgba(59, 130, 246, 0.15)' : 'transparent',
                  color: isActive ? '#60a5fa' : 'var(--text-secondary)',
                  border: isActive ? '1px solid rgba(59, 130, 246, 0.3)' : '1px solid transparent',
                  borderRadius: 'var(--radius-md)',
                  padding: '8px 16px',
                  fontSize: '0.82rem',
                  fontWeight: isActive ? 700 : 500,
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                }}
              >
                {tab.label}
              </button>
            );
          })}
        </div>

        {/* Tab Content Panes */}
        {activeTab === 'overview' && (
          <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '20px' }}>
            <div className="glass-card">
              <h3 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '14px' }}>
                Procurement Scope & Terms
              </h3>
              {isDemoCAG ? (
                <>
                  <p style={{ fontSize: '0.84rem', color: 'var(--text-secondary)', lineHeight: 1.55, marginBottom: '18px' }}>
                    Hiring of outsourcing agency for providing deployment of 177 Unskilled personnel (MTS/Peon), 86 Clerical/Non-Technical Graduate personnel (Data Entry Operators/Clerks/Stenographers), 10 Clerical Non-Graduate staff, and 5 Staff Car Drivers for the Office of the Comptroller & Auditor General of India, Central Expenditure, New Delhi.
                  </p>

                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '12px', background: 'var(--bg-tertiary)', padding: '14px', borderRadius: 'var(--radius-md)' }}>
                    <div>
                      <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Contract Period</div>
                      <div style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-primary)' }}>12 Months (Extendable)</div>
                    </div>
                    <div>
                      <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Place of Performance</div>
                      <div style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-primary)' }}>CAG Office, New Delhi (NCT)</div>
                    </div>
                    <div>
                      <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Minimum Turnover Required</div>
                      <div style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-primary)' }}>₹357.36 Lakhs</div>
                    </div>
                    <div>
                      <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Past Experience Required</div>
                      <div style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-primary)' }}>3 Years in Manpower Services</div>
                    </div>
                  </div>
                </>
              ) : (
                <>
                  <p style={{ fontSize: '0.84rem', color: 'var(--text-secondary)', lineHeight: 1.55, marginBottom: '18px' }}>
                    Newly created tender record awaiting tender document ingestion and clause extraction. No bidder application packages or risk findings are linked to this tender yet.
                  </p>

                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '12px', background: 'var(--bg-tertiary)', padding: '14px', borderRadius: 'var(--radius-md)' }}>
                    <div>
                      <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Status</div>
                      <div style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-primary)' }}>{t.status}</div>
                    </div>
                    <div>
                      <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Procuring Authority</div>
                      <div style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-primary)' }}>{t.issuing_authority}</div>
                    </div>
                    <div>
                      <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Requirements Mapped</div>
                      <div style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-primary)' }}>0 Mapped</div>
                    </div>
                    <div>
                      <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Bidder Applications</div>
                      <div style={{ fontSize: '0.82rem', fontWeight: 600, color: '#94a3b8' }}>0 Applications</div>
                    </div>
                  </div>
                </>
              )}
            </div>

            <div className="glass-card">
              <h3 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '14px' }}>
                Verification Pipeline Status
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                <div style={{ background: 'var(--bg-tertiary)', padding: '10px 14px', borderRadius: 'var(--radius-sm)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>Bidder Applications</span>
                  <strong style={{ fontSize: '0.9rem', color: isDemoCAG ? '#34d399' : '#94a3b8' }}>
                    {isDemoCAG ? '1 Package Received' : '0 Applications'}
                  </strong>
                </div>
                <div style={{ background: 'var(--bg-tertiary)', padding: '10px 14px', borderRadius: 'var(--radius-sm)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>Requirements Mapped</span>
                  <strong style={{ fontSize: '0.9rem', color: isDemoCAG ? '#60a5fa' : '#94a3b8' }}>
                    {isDemoCAG ? '10 Clauses Mapped' : '0 Mapped'}
                  </strong>
                </div>
                <div style={{ background: 'var(--bg-tertiary)', padding: '10px 14px', borderRadius: 'var(--radius-sm)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>Verification Checks</span>
                  <strong style={{ fontSize: '0.9rem', color: isDemoCAG ? '#fbbf24' : '#94a3b8' }}>
                    {isDemoCAG ? '10 Checks Evaluated' : 'Not started'}
                  </strong>
                </div>
                <div style={{ background: 'var(--bg-tertiary)', padding: '10px 14px', borderRadius: 'var(--radius-sm)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>Findings</span>
                  <strong style={{ fontSize: '0.9rem', color: isDemoCAG ? '#f87171' : '#94a3b8' }}>
                    {isDemoCAG ? '5 Findings' : '0 Findings'}
                  </strong>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'requirements' && (
          <div className="glass-card">
            <h3 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '14px' }}>
              Extracted Tender Requirements ({isDemoCAG ? 10 : 0})
            </h3>
            {isDemoCAG ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {DEMO_VERIFICATION_CHECKS.map((c) => (
                  <div
                    key={c.id}
                    style={{
                      background: 'var(--bg-tertiary)',
                      padding: '10px 14px',
                      borderRadius: 'var(--radius-sm)',
                      border: '1px solid var(--border-subtle)',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                    }}
                  >
                    <div>
                      <div style={{ fontSize: '0.84rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                        {c.requirement_title}
                      </div>
                      <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                        {c.requirement_clause}
                      </div>
                    </div>
                    <span className="badge badge-blue">{c.category}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
                No requirements mapped yet. Ingest tender PDF documents to extract statutory and technical clauses.
              </p>
            )}
          </div>
        )}

        {activeTab === 'applications' && (
          <div className="glass-card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div>
                <h3 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                  Submitted Bidder Application Packages ({isDemoCAG ? 1 : 0})
                </h3>
                <p style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
                  {isDemoCAG
                    ? 'Complete documentary submissions received for GeM Bid GEM/2021/B/1128240'
                    : '0 bidder applications available for this tender.'}
                </p>
              </div>
              {isDemoCAG && (
                <button className="btn btn-primary" onClick={() => onNavigate('applications')}>
                  <FolderKanban size={15} /> Launch Applications Workspace
                </button>
              )}
            </div>

            {isDemoCAG ? (
              <div style={{
                background: 'var(--bg-tertiary)',
                padding: '18px',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--border-subtle)',
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <h4 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                        {DEMO_BIDDER_APPLICATION.bidder_name}
                      </h4>
                      <span className="badge badge-synthetic">DEMO / SYNTHETIC DATA</span>
                    </div>
                    <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
                      Trade Name: {DEMO_BIDDER_APPLICATION.trade_name} · CIN: {DEMO_BIDDER_APPLICATION.cin}
                    </div>
                  </div>
                  <span className="badge badge-partial">REVIEW REQUIRED</span>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '10px', background: 'var(--bg-tertiary)', padding: '12px', borderRadius: 'var(--radius-sm)', marginBottom: '14px' }}>
                  <div>
                    <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>Documents Uploaded</div>
                    <div style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--text-primary)' }}>6 PDF Files</div>
                  </div>
                  <div>
                    <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>Total Pages</div>
                    <div style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--text-primary)' }}>16 Pages Extracted</div>
                  </div>
                  <div>
                    <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>Requirements Mapped</div>
                    <div style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--text-primary)' }}>10 Requirements</div>
                  </div>
                  <div>
                    <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>Verification Status</div>
                    <div style={{ fontSize: '0.82rem', fontWeight: 700, color: '#fbbf24' }}>6 Verified · 4 Issues</div>
                  </div>
                </div>

                <button className="btn btn-primary" onClick={() => onNavigate('applications')}>
                  Open Application & View Documents <ChevronRight size={15} />
                </button>
              </div>
            ) : (
              <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
                No bidder applications have been submitted or ingested for this tender yet.
              </p>
            )}
          </div>
        )}

        {activeTab === 'verification' && (
          <div className="glass-card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
              <h3 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                Document Verification Workspace Shortcut
              </h3>
              {isDemoCAG && (
                <button className="btn btn-primary" onClick={() => onNavigate('verification')}>
                  Open Full Verification Center <ChevronRight size={15} />
                </button>
              )}
            </div>
            <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
              {isDemoCAG
                ? '10 checks across Identity, Financial, Experience, Statutory, Declarations, EMD, and Technical specifications. Click button above to execute full verification.'
                : 'Verification has not started. Ingest bidder applications to begin verification.'}
            </p>
          </div>
        )}

        {activeTab === 'compliance' && (
          <div className="glass-card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
              <h3 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                Compliance Matrix Shortcut
              </h3>
              {isDemoCAG && (
                <button className="btn btn-primary" onClick={() => onNavigate('compliance')}>
                  Open Full Compliance Matrix <ChevronRight size={15} />
                </button>
              )}
            </div>
            <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
              {isDemoCAG
                ? 'Evaluates submitted evidence against mandatory criteria with confidence scores and citations.'
                : 'No compliance matrix items generated yet.'}
            </p>
          </div>
        )}

        {activeTab === 'findings' && (
          <div className="glass-card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
              <h3 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                Risk & Findings Shortcut
              </h3>
              {isDemoCAG && (
                <button className="btn btn-primary" onClick={() => onNavigate('findings')}>
                  Open Findings Center <ChevronRight size={15} />
                </button>
              )}
            </div>
            <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
              {isDemoCAG
                ? '5 findings recorded: 1 Critical (Missing Annexure-9), 1 High (Turnover mismatch ₹80.15L), 1 Medium (Experience shortfall), 2 Low/Info.'
                : '0 findings recorded for this tender. Verification has not started.'}
            </p>
          </div>
        )}

        {activeTab === 'dossier' && (
          <div className="glass-card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
              <h3 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                Compliance Dossier Export
              </h3>
              {isDemoCAG && (
                <button className="btn btn-primary" onClick={() => onNavigate('reports')}>
                  Generate Officer Dossier <ChevronRight size={15} />
                </button>
              )}
            </div>
            <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
              Export formal PDF/JSON compliance dossiers with complete audit timestamps for the competent procurement committee.
            </p>
          </div>
        )}
      </div>
    );
  }

  // Tender Catalog View
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '22px' }}>
      {/* Header bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <h1 style={{ fontSize: '1.45rem', fontWeight: 800, color: 'var(--text-primary)', letterSpacing: '-0.02em' }}>
            Tender Documents & Catalog
          </h1>
          <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
            Search, inspect, and evaluate GeM tender packages against uploaded bidder submissions.
          </p>
        </div>

        <button
          className="btn btn-primary"
          style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '8px 16px', fontSize: '0.82rem' }}
          onClick={() => {
            setFormErrors({});
            setNewTenderForm({
              tender_number: '',
              title: '',
              issuing_authority: '',
              tender_type: 'Services',
              estimated_value: '',
              emd_amount: '',
              deadline: '',
              description: '',
              category: '',
            });
            setIsAddTenderOpen(true);
          }}
        >
          <PlusCircle size={16} /> + Add Tender
        </button>
      </div>

      {/* Search & Filter Bar */}
      <div className="glass-card" style={{ padding: '14px 20px', display: 'flex', alignItems: 'center', gap: '12px' }}>
        <Search size={18} color="var(--text-muted)" />
        <input
          type="text"
          placeholder="Search by GeM Bid Number (e.g. GEM/2021/B/1128240), Department, or Title..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          style={{
            background: 'transparent',
            border: 'none',
            color: 'var(--text-primary)',
            fontSize: '0.88rem',
            width: '100%',
            outline: 'none',
          }}
        />
      </div>

      {/* Grid of Tender Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(420px, 1fr))', gap: '20px' }}>
        {filteredTenders.map((tender) => {
          const isSelected = activeTender ? tender.id === activeTender.id : false;
          const isDemoCAG = tender.tender_number === DEMO_CAG_TENDER.tender_number;

          return (
            <div
              key={tender.id}
              className="glass-card"
              style={{
                borderColor: isSelected ? 'rgba(59, 130, 246, 0.5)' : 'var(--border-subtle)',
                background: isSelected ? 'rgba(30, 58, 138, 0.15)' : 'var(--bg-card)',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                transition: 'all 0.2s ease',
              }}
            >
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                  <span
                    style={{
                      fontSize: '0.75rem',
                      fontWeight: 700,
                      fontFamily: 'var(--font-mono)',
                      color: '#60a5fa',
                      background: 'rgba(59, 130, 246, 0.1)',
                      padding: '4px 8px',
                      borderRadius: '4px',
                      border: '1px solid rgba(59, 130, 246, 0.25)',
                    }}
                  >
                    {tender.tender_number}
                  </span>
                  <div style={{ display: 'flex', gap: '6px' }}>
                    {isDemoCAG && <span className="badge badge-blue">AUTHENTIC GeM</span>}
                    <span className="badge badge-conditional">{tender.status}</span>
                  </div>
                </div>

                <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-primary)', lineHeight: 1.4, marginBottom: '8px' }}>
                  {tender.title}
                </h3>

                <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginBottom: '16px' }}>
                  {tender.issuing_authority}
                </p>

                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(2, 1fr)',
                    gap: '10px',
                    background: 'var(--bg-tertiary)',
                    padding: '12px',
                    borderRadius: 'var(--radius-sm)',
                    marginBottom: '18px',
                  }}
                >
                  <div>
                    <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>Estimated Value</div>
                    <div style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--brand-cyan)' }}>
                      {tender.estimated_value_display || (isDemoCAG ? '₹7.14 Cr' : '₹0.00')}
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>Turnover Required</div>
                    <div style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                      {tender.turnover_requirement_lakhs
                        ? `₹${tender.turnover_requirement_lakhs} Lakhs`
                        : isDemoCAG
                        ? '₹357.36 Lakhs'
                        : 'Not specified'}
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>Requirements Mapped</div>
                    <div style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                      {isDemoCAG ? '10 Requirements' : (tender.total_requirements ? `${tender.total_requirements} Requirements` : '0 Mapped')}
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>Bidder Applications</div>
                    <div style={{ fontSize: '0.8rem', fontWeight: 700, color: isDemoCAG ? '#34d399' : '#94a3b8' }}>
                      {isDemoCAG ? '1 Application' : '0 Applications'}
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>Findings</div>
                    <div style={{ fontSize: '0.8rem', fontWeight: 700, color: isDemoCAG ? '#f87171' : '#94a3b8' }}>
                      {isDemoCAG ? '5 Findings' : '0 Findings'}
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>Last Updated</div>
                    <div style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
                      {new Date(tender.created_at).toLocaleDateString('en-GB')}
                    </div>
                  </div>
                </div>
              </div>

              <div style={{ display: 'flex', gap: '10px', borderTop: '1px solid var(--border-subtle)', paddingTop: '14px' }}>
                <button
                  className="btn btn-primary"
                  style={{ flex: 1, fontSize: '0.8rem' }}
                  onClick={() => {
                    onSelectTender(tender);
                    setSelectedTenderForDetails(tender);
                  }}
                >
                  Open Tender Workflow <ChevronRight size={15} />
                </button>
                <button
                  className="btn btn-secondary"
                  style={{ fontSize: '0.8rem' }}
                  onClick={() => {
                    onSelectTender(tender);
                    onNavigate('applications');
                  }}
                  title="Directly inspect submitted application"
                >
                  <FolderKanban size={15} />
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {/* Add Tender Modal */}
      {isAddTenderOpen && (
        <div className="modal-backdrop" onClick={() => setIsAddTenderOpen(false)}>
          <div
            className="modal-content"
            onClick={(e) => e.stopPropagation()}
            style={{ maxWidth: '640px', width: '92%' }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '14px', marginBottom: '16px' }}>
              <div>
                <h2 style={{ fontSize: '1.2rem', fontWeight: 800, color: 'var(--text-primary)' }}>
                  Create New Tender Package
                </h2>
                <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
                  Register a GeM tender for automated requirement extraction and bidder verification
                </div>
              </div>
              <button
                onClick={() => setIsAddTenderOpen(false)}
                style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', padding: '4px' }}
              >
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleCreateTenderSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.74rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '4px' }}>
                  Tender ID / GeM Bid Number *
                </label>
                <input
                  type="text"
                  placeholder="e.g. GEM/2026/B/9821450"
                  value={newTenderForm.tender_number}
                  onChange={(e) => setNewTenderForm({ ...newTenderForm, tender_number: e.target.value })}
                  style={{
                    width: '100%',
                    background: 'var(--bg-tertiary)',
                    border: formErrors.tender_number ? '1px solid #ef4444' : '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-sm)',
                    padding: '8px 12px',
                    color: 'var(--text-primary)',
                    fontSize: '0.82rem',
                    outline: 'none',
                  }}
                />
                {formErrors.tender_number && (
                  <div style={{ fontSize: '0.7rem', color: '#f87171', marginTop: '2px' }}>{formErrors.tender_number}</div>
                )}
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.74rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '4px' }}>
                  Tender Title *
                </label>
                <input
                  type="text"
                  placeholder="e.g. Procurement of Cloud Infrastructure & Technical Support Services"
                  value={newTenderForm.title}
                  onChange={(e) => setNewTenderForm({ ...newTenderForm, title: e.target.value })}
                  style={{
                    width: '100%',
                    background: 'var(--bg-tertiary)',
                    border: formErrors.title ? '1px solid #ef4444' : '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-sm)',
                    padding: '8px 12px',
                    color: 'var(--text-primary)',
                    fontSize: '0.82rem',
                    outline: 'none',
                  }}
                />
                {formErrors.title && (
                  <div style={{ fontSize: '0.7rem', color: '#f87171', marginTop: '2px' }}>{formErrors.title}</div>
                )}
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.74rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '4px' }}>
                  Procuring Organization *
                </label>
                <input
                  type="text"
                  placeholder="e.g. Ministry of Electronics & IT, New Delhi"
                  value={newTenderForm.issuing_authority}
                  onChange={(e) => setNewTenderForm({ ...newTenderForm, issuing_authority: e.target.value })}
                  style={{
                    width: '100%',
                    background: 'var(--bg-tertiary)',
                    border: formErrors.issuing_authority ? '1px solid #ef4444' : '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-sm)',
                    padding: '8px 12px',
                    color: 'var(--text-primary)',
                    fontSize: '0.82rem',
                    outline: 'none',
                  }}
                />
                {formErrors.issuing_authority && (
                  <div style={{ fontSize: '0.7rem', color: '#f87171', marginTop: '2px' }}>{formErrors.issuing_authority}</div>
                )}
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '12px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.74rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '4px' }}>
                    Tender Type
                  </label>
                  <select
                    value={newTenderForm.tender_type}
                    onChange={(e) => setNewTenderForm({ ...newTenderForm, tender_type: e.target.value })}
                    style={{
                      width: '100%',
                      background: 'var(--bg-tertiary)',
                      border: '1px solid var(--border-subtle)',
                      borderRadius: 'var(--radius-sm)',
                      padding: '8px 12px',
                      color: 'var(--text-primary)',
                      fontSize: '0.82rem',
                      outline: 'none',
                    }}
                  >
                    <option value="Services">Services (Manpower/Cloud/Facility)</option>
                    <option value="Goods">Goods / Hardware</option>
                    <option value="Works">Civil & Engineering Works</option>
                  </select>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.74rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '4px' }}>
                    Estimated Tender Value (₹) *
                  </label>
                  <input
                    type="number"
                    placeholder="e.g. 50000000"
                    value={newTenderForm.estimated_value}
                    onChange={(e) => setNewTenderForm({ ...newTenderForm, estimated_value: e.target.value })}
                    style={{
                      width: '100%',
                      background: 'var(--bg-tertiary)',
                      border: formErrors.estimated_value ? '1px solid #ef4444' : '1px solid var(--border-subtle)',
                      borderRadius: 'var(--radius-sm)',
                      padding: '8px 12px',
                      color: 'var(--text-primary)',
                      fontSize: '0.82rem',
                      outline: 'none',
                    }}
                  />
                  {formErrors.estimated_value && (
                    <div style={{ fontSize: '0.7rem', color: '#f87171', marginTop: '2px' }}>{formErrors.estimated_value}</div>
                  )}
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '12px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.74rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '4px' }}>
                    EMD Amount (₹)
                  </label>
                  <input
                    type="number"
                    placeholder="e.g. 2500000"
                    value={newTenderForm.emd_amount}
                    onChange={(e) => setNewTenderForm({ ...newTenderForm, emd_amount: e.target.value })}
                    style={{
                      width: '100%',
                      background: 'var(--bg-tertiary)',
                      border: '1px solid var(--border-subtle)',
                      borderRadius: 'var(--radius-sm)',
                      padding: '8px 12px',
                      color: 'var(--text-primary)',
                      fontSize: '0.82rem',
                      outline: 'none',
                    }}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.74rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '4px' }}>
                    Submission Deadline *
                  </label>
                  <input
                    type="date"
                    value={newTenderForm.deadline}
                    onChange={(e) => setNewTenderForm({ ...newTenderForm, deadline: e.target.value })}
                    style={{
                      width: '100%',
                      background: 'var(--bg-tertiary)',
                      border: formErrors.deadline ? '1px solid #ef4444' : '1px solid var(--border-subtle)',
                      borderRadius: 'var(--radius-sm)',
                      padding: '8px 12px',
                      color: 'var(--text-primary)',
                      fontSize: '0.82rem',
                      outline: 'none',
                    }}
                  />
                  {formErrors.deadline && (
                    <div style={{ fontSize: '0.7rem', color: '#f87171', marginTop: '2px' }}>{formErrors.deadline}</div>
                  )}
                </div>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.74rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '4px' }}>
                  Tender Document (PDF - Optional for initial demo workflow)
                </label>
                <input
                  type="file"
                  accept=".pdf"
                  style={{
                    width: '100%',
                    background: 'var(--bg-tertiary)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-sm)',
                    padding: '8px 12px',
                    color: 'var(--text-secondary)',
                    fontSize: '0.8rem',
                  }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.74rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '4px' }}>
                  Description (Optional)
                </label>
                <textarea
                  rows={2}
                  placeholder="Additional tender details or scope notes..."
                  value={newTenderForm.description}
                  onChange={(e) => setNewTenderForm({ ...newTenderForm, description: e.target.value })}
                  style={{
                    width: '100%',
                    background: 'var(--bg-tertiary)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-sm)',
                    padding: '8px 12px',
                    color: 'var(--text-primary)',
                    fontSize: '0.82rem',
                    outline: 'none',
                    resize: 'vertical',
                  }}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '8px', borderTop: '1px solid var(--border-subtle)', paddingTop: '14px' }}>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => {
                    setFormErrors({});
                    setIsAddTenderOpen(false);
                  }}
                >
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  Create Tender
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

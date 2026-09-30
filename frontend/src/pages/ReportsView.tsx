import React, { useState } from 'react';
import {
  FileText,
  Download,
  FileSpreadsheet,
  Printer,
  ShieldAlert,
  CheckCircle,
  ExternalLink,
} from 'lucide-react';
import { Tender, Bidder } from '../types';
import { DEMO_BIDDER_APPLICATION } from '../api/demoData';

interface ReportsViewProps {
  activeTender: Tender | null;
  bidders: Bidder[];
}

export const ReportsView: React.FC<ReportsViewProps> = ({
  activeTender,
  bidders,
}) => {
  const fallbackBidders: Bidder[] = [
    {
      id: DEMO_BIDDER_APPLICATION.id,
      legal_name: DEMO_BIDDER_APPLICATION.bidder_name,
      trade_name: DEMO_BIDDER_APPLICATION.trade_name,
      pan: DEMO_BIDDER_APPLICATION.pan,
      gstin: DEMO_BIDDER_APPLICATION.gstin,
      is_mse: false,
      is_startup: false,
    },
  ];

  const availableBidders = bidders.length > 0 ? bidders : fallbackBidders;
  const [selectedBidder, setSelectedBidder] = useState<string>(availableBidders[0]?.id || '');
  const [isExporting, setIsExporting] = useState(false);

  const currentBidder = availableBidders.find((b) => b.id === selectedBidder) || availableBidders[0];

  if (!activeTender) {
    return (
      <div className="glass-card" style={{ textAlign: 'center', padding: '48px 24px' }}>
        <h2 style={{ fontSize: '1.2rem', color: 'var(--text-primary)', marginBottom: '8px' }}>No Active Tender Selected</h2>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '16px' }}>Select or upload a tender to generate official compliance dossiers.</p>
      </div>
    );
  }

  const handleDownloadPDF = () => {
    if (!currentBidder) return;
    setIsExporting(true);
    setTimeout(() => {
      setIsExporting(false);
      const link = document.createElement('a');
      link.href = `http://localhost:8000/api/v1/reports/tender/${activeTender.id}/bidder/${currentBidder.id}/pdf`;
      link.download = `BidGuard_Compliance_Dossier_${activeTender.tender_number.replace(/\//g, '_')}.pdf`;
      link.target = '_blank';
      link.click();
    }, 600);
  };

  const handleExportCSV = () => {
    const csvContent =
      'data:text/csv;charset=utf-8,' +
      'Check ID,Category,Requirement Title,Submitted Evidence,Verification Result,Discrepancy / Variance,Source Document\n' +
      'CHK-01,Identity,Legal Entity Incorporation,RoC Certificate of Incorporation U74999DL2016PTC301429,COMPLIANT,,02_Company_Incorporation_and_Statutory_Registrations.pdf (Pg 1)\n' +
      'CHK-02,Identity,Registered Office in Delhi / NCT,Lease Deed Suite 402 Pragati Deep Laxmi Nagar,COMPLIANT,,02_Company_Incorporation_and_Statutory_Registrations.pdf (Pg 2)\n' +
      'CHK-03,Financial,Average Annual Turnover (Min ₹357.36L),CA Certificate ₹6.20 Cr vs P&L ₹5.40 Cr,PARTIAL,Variance of ₹80.15 Lakhs between certified turnover and audited accounts,03_Financial_Turnover_and_Audited_Statements.pdf (Pg 1)\n' +
      'CHK-04,EMD,Earnest Money Deposit (₹35.73L BG),State Bank of India BG 0069121BG0004128 ₹35.73L,COMPLIANT,,06_EMD_Bank_Guarantee_State_Bank_of_India.pdf (Pg 1)\n' +
      'CHK-05,Experience,Past Similar Works Experience,CBDT ₹3.82 Cr; DPIIT ₹2.95 Cr; SAIL ₹1.90 Cr,PARTIAL,Order shortfall of ₹95 Lakhs on Project 3 and missing completion certificate,04_Past_Experience_Work_Orders_and_Completion.pdf (Pg 3)\n' +
      'CHK-06,Declarations,Annexure-9 VVIP Security Clearance Affidavit,Notarized Annexure-9 affidavit omitted from submission,EVIDENCE_MISSING,Mandatory statutory document missing,05_Statutory_Affidavits_and_Compliance_Undertakings.pdf (Pg 1)\n' +
      'CHK-07,Statutory,Statutory Registrations (PAN/GST/EPF/ESIC/Labour),Submitted PAN AAACA9182K / GST 07AAACA9182K1Z5 (External Verification Not Configured),COMPLIANT,Name variation abbreviation acceptable,02_Company_Incorporation_and_Statutory_Registrations.pdf (Pg 2)\n' +
      'CHK-08,Declarations,Delhi NCT Minimum Wages Undertaking (Annexure-10),Notarized Annexure-10 stamp paper IN-DL91820491829042U,COMPLIANT,,05_Statutory_Affidavits_and_Compliance_Undertakings.pdf (Pg 2)\n' +
      'CHK-09,Technical,ISO 9001:2015 Quality Management Certification,Certificate QMS-2019-DEL-84920 valid through 17-07-2022,COMPLIANT,,05_Statutory_Affidavits_and_Compliance_Undertakings.pdf (Pg 2)\n' +
      'CHK-10,Technical,Typing Speed Qualification (15000 Key Dep/Hr),Self-declaration without empirical test logs,CLARIFICATION_PENDING,Lack of empirical third-party certification,05_Statutory_Affidavits_and_Compliance_Undertakings.pdf (Pg 2)\n';
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `BidGuard_Matrix_${activeTender.tender_number.replace(/\//g, '_')}.csv`);
    document.body.appendChild(link);
    link.click();
  };

  const sections16 = [
    '1. Tender Header & Authority Metadata',
    '2. Bidder Legal Identity & Registrations',
    '3. Submitted Statutory Registry Review (GST, Udyam, PAN Evidence)',
    '4. MSE & Startup Preference Assessment',
    '5. Financial Turnover & Net Worth Standing',
    '6. Technical Experience & Past Performance',
    '7. Itemized Technical Compliance Matrix',
    '8. Consortium & Joint Venture Evaluation',
    '9. Central Debarment & Integrity Pact Check',
    '10. Entity Name & Director Mismatch Analysis',
    '11. Consolidated Officer Risk Findings',
    '12. Clarifications Requested & Bidder Replies',
    '13. Deterministic Risk Profile Calculation',
    '14. Officer Action & Overrides Audit Block',
    '15. Executive Compliance Summary & Matrices',
    '16. Immutable Timestamped Audit Trail',
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Header bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <span className="badge badge-blue">Official Verification Dossier</span>
            <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>16-Section Statutory Report</span>
          </div>
          <h1 style={{ fontSize: '1.45rem', fontWeight: 800, color: 'var(--text-primary)', letterSpacing: '-0.02em' }}>
            Compliance Dossier & Export Center
          </h1>
        </div>

        <div style={{ display: 'flex', gap: '12px' }}>
          <button className="btn btn-secondary" onClick={handleExportCSV}>
            <FileSpreadsheet size={16} /> Export CSV Matrix
          </button>
          <button className="btn btn-primary" onClick={handleDownloadPDF} disabled={isExporting}>
            <Download size={16} /> {isExporting ? 'Generating PDF...' : 'Download Official PDF Report'}
          </button>
        </div>
      </div>

      {/* Bidder Selector */}
      <div className="glass-card" style={{ padding: '16px 20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)', fontWeight: 600 }}>Generate Dossier for Bidder:</span>
          <select
            value={selectedBidder}
            onChange={(e) => setSelectedBidder(e.target.value)}
            style={{
              background: 'var(--bg-tertiary)',
              color: 'var(--text-primary)',
              border: '1px solid var(--border-accent)',
              borderRadius: 'var(--radius-md)',
              padding: '8px 14px',
              fontSize: '0.85rem',
              fontWeight: 600,
              cursor: 'pointer',
              outline: 'none',
            }}
          >
            {bidders.map((b) => (
              <option key={b.id} value={b.id}>
                {b.legal_name}
              </option>
            ))}
          </select>
        </div>

        <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
          Selected Tender: <strong style={{ color: 'var(--text-primary)' }}>{activeTender.tender_number}</strong>
        </div>
      </div>

      {/* Statutory Disclaimer Box */}
      <div style={{
        background: 'rgba(239, 68, 68, 0.08)',
        border: '1px solid rgba(239, 68, 68, 0.3)',
        borderRadius: 'var(--radius-md)',
        padding: '16px 20px',
        display: 'flex',
        alignItems: 'center',
        gap: '14px',
      }}>
        <ShieldAlert size={24} color="#ef4444" />
        <div style={{ fontSize: '0.8rem', color: '#fca5a5', lineHeight: 1.5 }}>
          <strong>Statutory Non-Autonomous Legal Disclaimer:</strong> This verification dossier is generated by BidGuard AI as an evidence-backed decision-support system. It does NOT make final procurement determinations or award contracts. The designated Procurement Authority retains exclusive legal authority under the General Financial Rules (GFR 2017) and GeM Guidelines.
        </div>
      </div>

      {/* 16-Section Breakdown Grid */}
      <div className="glass-card">
        <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '14px' }}>
          16-Section Officer Dossier Specification (SIH26100 Standard)
        </h3>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '10px' }}>
          {sections16.map((sec, idx) => (
            <div
              key={idx}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
                padding: '12px 14px',
                borderRadius: 'var(--radius-sm)',
                background: 'rgba(255, 255, 255, 0.02)',
                border: '1px solid var(--border-subtle)',
                fontSize: '0.82rem',
                color: 'var(--text-primary)',
              }}
            >
              <CheckCircle size={16} color="#10b981" />
              <span>{sec}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

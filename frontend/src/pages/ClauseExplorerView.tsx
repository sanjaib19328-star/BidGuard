import React, { useState } from 'react';
import {
  BookOpen,
  Filter,
  CheckCircle2,
  FileText,
  Search,
  Sparkles,
  ArrowRight,
  Shield,
  Layers,
} from 'lucide-react';
import { Clause, Tender, ClauseCategory } from '../types';

interface ClauseExplorerViewProps {
  clauses: Clause[];
  activeTender: Tender | null;
  onNavigate: (tab: any) => void;
}

export const ClauseExplorerView: React.FC<ClauseExplorerViewProps> = ({
  clauses,
  activeTender,
  onNavigate,
}) => {
  const [selectedCategory, setSelectedCategory] = useState<string>('ALL');
  const [searchTerm, setSearchTerm] = useState('');
  const [activeClause, setActiveClause] = useState<Clause | null>(clauses[0] || null);

  const categories = ['ALL', 'STATUTORY', 'FINANCIAL', 'TECHNICAL', 'COMMERCIAL', 'ELIGIBILITY'];

  const filteredClauses = clauses.filter((c) => {
    const matchesCat = selectedCategory === 'ALL' || c.category === selectedCategory;
    const matchesSearch =
      (c.title || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
      c.clause_text.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (c.clause_number || '').toLowerCase().includes(searchTerm.toLowerCase());
    return matchesCat && matchesSearch;
  });

  if (!activeTender) {
    return (
      <div className="glass-card" style={{ textAlign: 'center', padding: '48px 24px' }}>
        <h2 style={{ fontSize: '1.2rem', color: 'var(--text-primary)', marginBottom: '8px' }}>No Active Tender Selected</h2>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '16px' }}>Select or upload a tender to inspect segmented clauses and compiled rules.</p>
        <button className="btn btn-primary" onClick={() => onNavigate('tenders')}>View Tenders</button>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Top Banner */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <span className="badge badge-blue">{activeTender.tender_number}</span>
            <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>Tender Intelligence & Clauses</span>
          </div>
          <h1 style={{ fontSize: '1.45rem', fontWeight: 800, color: 'var(--text-primary)', letterSpacing: '-0.02em' }}>
            Segmented Clauses & Rule Compiler
          </h1>
        </div>
        <button className="btn btn-primary" onClick={() => onNavigate('compliance')}>
          Audit Compliance Matrix <ArrowRight size={16} />
        </button>
      </div>

      {/* Category Pills & Filter Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '16px', flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          {categories.map((cat) => {
            const isSelected = selectedCategory === cat;
            return (
              <button
                key={cat}
                onClick={() => setSelectedCategory(cat)}
                style={{
                  padding: '6px 14px',
                  borderRadius: '9999px',
                  fontSize: '0.78rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  border: isSelected ? '1px solid var(--brand-blue)' : '1px solid var(--border-subtle)',
                  background: isSelected ? 'rgba(59, 130, 246, 0.2)' : 'var(--bg-tertiary)',
                  color: isSelected ? '#60a5fa' : 'var(--text-secondary)',
                  transition: 'all 0.15s ease',
                }}
              >
                {cat}
              </button>
            );
          })}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', background: 'var(--bg-card)', padding: '6px 14px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)', minWidth: '320px' }}>
          <Search size={16} color="var(--text-muted)" />
          <input
            type="text"
            placeholder="Search clause text or keywords..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{
              background: 'transparent',
              border: 'none',
              color: 'var(--text-primary)',
              fontSize: '0.82rem',
              width: '100%',
              outline: 'none',
            }}
          />
        </div>
      </div>

      {/* 2-Column Split: Clause List on Left, Clause Deep Inspection on Right */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1.8fr', gap: '24px' }}>
        {/* Left Clause List */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', maxHeight: '720px', overflowY: 'auto' }}>
          {filteredClauses.map((clause) => {
            const isSelected = activeClause?.id === clause.id;
            return (
              <div
                key={clause.id}
                className="glass-card"
                onClick={() => setActiveClause(clause)}
                style={{
                  cursor: 'pointer',
                  padding: '16px 20px',
                  borderColor: isSelected ? 'rgba(59, 130, 246, 0.6)' : 'var(--border-subtle)',
                  background: isSelected ? 'rgba(30, 58, 138, 0.2)' : 'var(--bg-card)',
                  transform: isSelected ? 'translateX(4px)' : 'none',
                  transition: 'all 0.15s ease',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <span style={{ fontSize: '0.78rem', fontWeight: 700, fontFamily: 'var(--font-mono)', color: '#60a5fa' }}>
                    {clause.clause_number || `Clause (Page ${clause.page_number})`}
                  </span>
                  <span className="badge badge-blue" style={{ fontSize: '0.68rem' }}>
                    {clause.category}
                  </span>
                </div>

                <h4 style={{ fontSize: '0.92rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '6px' }}>
                  {clause.title || 'Extracted Procurement Condition'}
                </h4>

                <p style={{
                  fontSize: '0.78rem',
                  color: 'var(--text-secondary)',
                  display: '-webkit-box',
                  WebkitLineClamp: 2,
                  WebkitBoxOrient: 'vertical',
                  overflow: 'hidden',
                  lineHeight: 1.4,
                }}>
                  {clause.clause_text}
                </p>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '12px', fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                  <span>Source Page: {clause.page_number}</span>
                  <span style={{ color: '#10b981', fontWeight: 600 }}>
                    AI Confidence: {Math.round(clause.confidence_score * 100)}%
                  </span>
                </div>
              </div>
            );
          })}
        </div>

        {/* Right Detail Pane */}
        {activeClause ? (
          <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <span className="badge badge-blue" style={{ marginBottom: '8px' }}>
                  {activeClause.category} REQUIREMENT
                </span>
                <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                  {activeClause.clause_number}: {activeClause.title || 'Procurement Clause'}
                </h2>
                <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                  Page {activeClause.page_number} of Authentic GeM Bid Document
                </span>
              </div>
              <div style={{
                background: 'rgba(16, 185, 129, 0.12)',
                border: '1px solid rgba(16, 185, 129, 0.3)',
                padding: '6px 12px',
                borderRadius: 'var(--radius-md)',
                textAlign: 'right',
              }}>
                <div style={{ fontSize: '0.68rem', color: '#10b981', fontWeight: 700 }}>PARSER CONFIDENCE</div>
                <div style={{ fontSize: '1rem', fontWeight: 800, color: '#34d399' }}>
                  {Math.round(activeClause.confidence_score * 100)}%
                </div>
              </div>
            </div>

            {/* Original Verbatim Tender Text */}
            <div style={{ background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-md)', padding: '18px', border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '8px' }}>
                Verbatim Tender Text (OCR / Digitized PDF)
              </div>
              <p style={{ fontSize: '0.88rem', color: 'var(--text-primary)', lineHeight: 1.6, whiteSpace: 'pre-wrap' }}>
                {activeClause.clause_text}
              </p>
            </div>

            {/* Compiled Structured Verification Rule */}
            <div style={{ background: 'rgba(59, 130, 246, 0.05)', borderRadius: 'var(--radius-md)', padding: '18px', border: '1px solid rgba(59, 130, 246, 0.2)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
                <Sparkles size={16} color="var(--brand-cyan)" />
                <span style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--brand-cyan)', textTransform: 'uppercase' }}>
                  Compiled Verification Rule
                </span>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '12px' }}>
                <div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Rule Dimension</div>
                  <div style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)' }}>{activeClause.category}</div>
                </div>
                <div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Mandatory Status</div>
                  <div style={{ fontSize: '0.85rem', fontWeight: 600, color: '#ef4444' }}>STRICT MANDATORY</div>
                </div>
                <div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Applicability Engine</div>
                  <div style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)' }}>All Eligible Bidders</div>
                </div>
                <div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Evidence Required</div>
                  <div style={{ fontSize: '0.85rem', fontWeight: 600, color: '#60a5fa' }}>Audited Certificate / Declaration</div>
                </div>
              </div>
            </div>

            {/* Action buttons */}
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
              <button className="btn btn-secondary" onClick={() => onNavigate('compliance')}>
                Match Against Bidder Submissions
              </button>
            </div>
          </div>
        ) : (
          <div className="glass-card" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '300px' }}>
            <span style={{ color: 'var(--text-muted)' }}>Select a clause on the left to inspect</span>
          </div>
        )}
      </div>
    </div>
  );
};

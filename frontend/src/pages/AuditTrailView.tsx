import React from 'react';
import {
  History,
  ShieldCheck,
  UserCheck,
  FileCheck2,
  Clock,
  Search,
} from 'lucide-react';
import { AuditLogItem } from '../types';
import { DEMO_AUDIT_LOGS } from '../api/demoData';

interface AuditTrailViewProps {
  logs: AuditLogItem[];
}

export const AuditTrailView: React.FC<AuditTrailViewProps> = ({ logs }) => {
  const displayLogs = logs.length > 0 ? logs : DEMO_AUDIT_LOGS;
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Header bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <span className="badge badge-compliant">Immutable Event Ledger</span>
            <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>Audit Trail & Governance</span>
          </div>
          <h1 style={{ fontSize: '1.45rem', fontWeight: 800, color: 'var(--text-primary)', letterSpacing: '-0.02em' }}>
            Procurement Action Audit Trail
          </h1>
        </div>

        <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', background: 'rgba(255,255,255,0.04)', padding: '8px 16px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
          Tamper-Evident: <strong style={{ color: '#60a5fa' }}>PostgreSQL JSONB Ledger with Actor Identity</strong>
        </div>
      </div>

      {/* Timeline List */}
      <div className="glass-card" style={{ padding: '24px' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {displayLogs.map((log, idx) => (
            <div
              key={log.id}
              style={{
                display: 'flex',
                gap: '16px',
                position: 'relative',
              }}
            >
              {/* Timeline Indicator */}
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                <div style={{
                  width: '36px',
                  height: '36px',
                  borderRadius: '50%',
                  background: log.action.includes('OVERRIDDEN') ? 'rgba(139, 92, 246, 0.2)' : 'rgba(59, 130, 246, 0.2)',
                  border: log.action.includes('OVERRIDDEN') ? '1px solid #8b5cf6' : '1px solid #3b82f6',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: log.action.includes('OVERRIDDEN') ? '#c4b5fd' : '#60a5fa',
                }}>
                  {log.action.includes('OVERRIDDEN') ? <ShieldCheck size={18} /> : <FileCheck2 size={18} />}
                </div>
                {idx < logs.length - 1 && (
                  <div style={{ width: '2px', flex: 1, background: 'var(--border-subtle)', margin: '6px 0' }} />
                )}
              </div>

              {/* Log Content Card */}
              <div style={{
                flex: 1,
                background: 'var(--bg-tertiary)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-md)',
                padding: '16px 20px',
                marginBottom: '8px',
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                  <div>
                    <span style={{
                      fontSize: '0.75rem',
                      fontWeight: 700,
                      fontFamily: 'var(--font-mono)',
                      color: log.action.includes('OVERRIDDEN') ? '#c4b5fd' : '#60a5fa',
                      background: log.action.includes('OVERRIDDEN') ? 'rgba(139, 92, 246, 0.15)' : 'rgba(59, 130, 246, 0.15)',
                      padding: '3px 8px',
                      borderRadius: '4px',
                    }}>
                      {log.action}
                    </span>
                    <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-primary)', marginLeft: '10px' }}>
                      {log.entity_type}
                    </span>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                    <Clock size={13} />
                    <span>{new Date(log.timestamp).toLocaleString()}</span>
                  </div>
                </div>

                <p style={{ fontSize: '0.84rem', color: 'var(--text-secondary)', marginBottom: '8px', lineHeight: 1.4 }}>
                  {log.details}
                </p>

                <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <UserCheck size={14} color="var(--brand-cyan)" />
                  <span>Recorded Actor: <strong>{log.actor}</strong></span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

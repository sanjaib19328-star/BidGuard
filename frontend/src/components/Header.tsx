import React, { useState, useEffect } from 'react';
import { UserCheck, Cpu, X, ShieldAlert, CheckCircle2, AlertCircle } from 'lucide-react';
import { Tender } from '../types';
import { apiClient } from '../api/client';

interface HeaderProps {
  activeTender: Tender | null;
  tenders: Tender[];
  onSelectTender: (tender: Tender) => void;
  isLiveConnected: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  activeTender,
  tenders,
  onSelectTender,
  isLiveConnected,
}) => {
  const [aiStatus, setAiStatus] = useState<{
    status: 'connected' | 'fallback_active' | 'unavailable' | 'auth_required';
    provider: string;
    model: string;
    device: string;
    lastRequest: string;
    fallbackStatus: string;
    authError?: boolean;
  }>({
    status: 'fallback_active',
    provider: 'Local Resilient Inference Engine',
    model: 'Qwen/Qwen2.5-1.5B-Instruct & BAAI/bge-small-en-v1.5',
    device: 'cpu',
    lastRequest: 'Initialized & Ready',
    fallbackStatus: 'Response generated using grounded fallback logic; no external LLM was available for this request.',
    authError: false,
  });

  const [showStatusModal, setShowStatusModal] = useState(false);

  useEffect(() => {
    async function checkStatus() {
      try {
        const res = await apiClient.getAIStatus();
        if (res && res.status === 'healthy') {
          setAiStatus({
            status: 'connected',
            provider: 'Hugging Face Serverless Inference / Local Hybrid',
            model: res.models?.llm?.model_id || 'Qwen/Qwen2.5-1.5B-Instruct',
            device: res.models?.llm?.device || 'cpu',
            lastRequest: new Date().toLocaleTimeString(),
            fallbackStatus: 'Primary neural models active with automatic resilient fallback protection.',
            authError: false,
          });
        } else if (res?.auth_error || res?.error?.includes('401') || res?.error?.includes('Unauthorized')) {
          setAiStatus({
            status: 'auth_required',
            provider: 'Hugging Face API',
            model: 'Qwen/Qwen2.5-1.5B-Instruct',
            device: 'cpu',
            lastRequest: new Date().toLocaleTimeString(),
            fallbackStatus: 'AI provider authentication required. Please configure HF_TOKEN in backend environment.',
            authError: true,
          });
        } else {
          setAiStatus({
            status: 'fallback_active',
            provider: 'BidGuard Grounded Procurement Engine',
            model: 'Local Deterministic Fallback Parser & Cosine Index',
            device: 'cpu',
            lastRequest: new Date().toLocaleTimeString(),
            fallbackStatus: 'Response generated using grounded fallback logic; no external LLM was available for this request.',
            authError: false,
          });
        }
      } catch (err: any) {
        if (err?.message?.includes('401') || err?.message?.includes('Unauthorized')) {
          setAiStatus({
            status: 'auth_required',
            provider: 'Hugging Face API',
            model: 'Qwen2.5-1.5B-Instruct',
            device: 'cpu',
            lastRequest: new Date().toLocaleTimeString(),
            fallbackStatus: 'AI provider authentication required.',
            authError: true,
          });
        } else {
          setAiStatus({
            status: isLiveConnected ? 'fallback_active' : 'unavailable',
            provider: 'BidGuard Local Engine',
            model: 'Deterministic Fallback Rule-Set',
            device: 'cpu',
            lastRequest: 'Awaiting Query',
            fallbackStatus: 'Response generated using grounded fallback logic; no external LLM was available for this request.',
            authError: false,
          });
        }
      }
    }

    checkStatus();
    const interval = setInterval(checkStatus, 30000);
    return () => clearInterval(interval);
  }, [isLiveConnected]);

  const getStatusColor = () => {
    switch (aiStatus.status) {
      case 'connected':
        return '#10b981';
      case 'fallback_active':
        return '#f59e0b';
      case 'auth_required':
      case 'unavailable':
      default:
        return '#ef4444';
    }
  };

  const getStatusLabel = () => {
    switch (aiStatus.status) {
      case 'connected':
        return 'Connected';
      case 'fallback_active':
        return 'Fallback Mode';
      case 'auth_required':
        return 'Auth Required';
      case 'unavailable':
      default:
        return 'Unavailable';
    }
  };

  return (
    <header className="top-header">
      {/* Active Tender Selector */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase' }}>
            Active Tender:
          </span>
          {tenders.length > 0 && activeTender ? (
            <select
              value={activeTender.id}
              onChange={(e) => {
                const selected = tenders.find((t) => t.id === e.target.value);
                if (selected) onSelectTender(selected);
              }}
              style={{
                background: 'var(--bg-tertiary)',
                color: 'var(--text-primary)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-sm)',
                padding: '6px 12px',
                fontSize: '0.82rem',
                fontWeight: 600,
                cursor: 'pointer',
                outline: 'none',
                maxWidth: '380px',
              }}
            >
              {tenders.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.tender_number} — {t.title.slice(0, 36)}...
                </option>
              ))}
            </select>
          ) : (
            <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
              No Tenders Uploaded Yet
            </span>
          )}
        </div>

        {activeTender && (
          <span className="badge badge-blue" style={{ fontSize: '0.7rem' }}>
            {activeTender.status}
          </span>
        )}
      </div>

      {/* Right User & System Indicators */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        {/* AI Engine Status Button / Trigger */}
        <button
          onClick={() => setShowStatusModal(true)}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            background: 'var(--bg-tertiary)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-md)',
            padding: '6px 12px',
            cursor: 'pointer',
            color: 'var(--text-secondary)',
            fontSize: '0.78rem',
            fontWeight: 500,
            transition: 'all 0.15s ease',
          }}
          title="Click to view AI Engine health and provider details"
        >
          <Cpu size={15} color={getStatusColor()} />
          <span>AI Engine:</span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '5px', fontWeight: 600, color: getStatusColor() }}>
            <span
              style={{
                width: '7px',
                height: '7px',
                borderRadius: '50%',
                background: getStatusColor(),
                boxShadow: `0 0 6px ${getStatusColor()}`,
              }}
            />
            {getStatusLabel()}
          </span>
        </button>

        {/* Backend API Connectivity Indicator */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span
            style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              background: isLiveConnected ? '#10b981' : '#f59e0b',
              boxShadow: isLiveConnected ? '0 0 8px #10b981' : '0 0 8px #f59e0b',
            }}
          />
          <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', fontWeight: 500 }}>
            {isLiveConnected ? 'FastAPI Online' : 'Connecting to API...'}
          </span>
        </div>

        {/* Procurement Authority Tag */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            background: 'var(--bg-tertiary)',
            padding: '6px 12px',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--border-subtle)',
          }}
        >
          <UserCheck size={16} color="var(--brand-cyan)" />
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-primary)' }}>
              Procurement Officer
            </div>
            <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>
              Competent Authority (GeM)
            </div>
          </div>
        </div>
      </div>

      {/* AI Engine Status Modal */}
      {showStatusModal && (
        <div className="modal-backdrop" onClick={() => setShowStatusModal(false)}>
          <div
            className="modal-content"
            onClick={(e) => e.stopPropagation()}
            style={{ maxWidth: '520px' }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <div style={{
                  padding: '8px',
                  borderRadius: '8px',
                  background: `${getStatusColor()}20`,
                  color: getStatusColor(),
                }}>
                  <Cpu size={22} />
                </div>
                <div>
                  <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                    AI Engine Diagnostics
                  </h3>
                  <p style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
                    BidGuard Verification Pipeline Status
                  </p>
                </div>
              </div>
              <button
                onClick={() => setShowStatusModal(false)}
                style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
              >
                <X size={18} />
              </button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div style={{
                background: 'var(--bg-tertiary)',
                padding: '14px',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--border-subtle)',
                display: 'grid',
                gridTemplateColumns: '130px 1fr',
                gap: '10px',
                fontSize: '0.82rem',
              }}>
                <div style={{ color: 'var(--text-muted)', fontWeight: 600 }}>Connection Status</div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: getStatusColor(), fontWeight: 700 }}>
                  <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: getStatusColor() }} />
                  {getStatusLabel()}
                </div>

                <div style={{ color: 'var(--text-muted)', fontWeight: 600 }}>Provider</div>
                <div style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{aiStatus.provider}</div>

                <div style={{ color: 'var(--text-muted)', fontWeight: 600 }}>Active Model(s)</div>
                <div style={{ color: '#60a5fa', fontFamily: 'var(--font-mono)', fontSize: '0.76rem' }}>
                  {aiStatus.model}
                </div>

                <div style={{ color: 'var(--text-muted)', fontWeight: 600 }}>Inference Device</div>
                <div style={{ color: 'var(--text-primary)', textTransform: 'uppercase', fontSize: '0.78rem' }}>
                  {aiStatus.device}
                </div>

                <div style={{ color: 'var(--text-muted)', fontWeight: 600 }}>Last Request</div>
                <div style={{ color: 'var(--text-secondary)' }}>{aiStatus.lastRequest}</div>
              </div>

              {aiStatus.authError ? (
                <div style={{
                  background: 'rgba(239, 68, 68, 0.12)',
                  border: '1px solid rgba(239, 68, 68, 0.3)',
                  padding: '12px 14px',
                  borderRadius: 'var(--radius-md)',
                  display: 'flex',
                  gap: '10px',
                  alignItems: 'flex-start',
                }}>
                  <AlertCircle size={18} color="#ef4444" style={{ flexShrink: 0, marginTop: '2px' }} />
                  <div>
                    <div style={{ fontSize: '0.82rem', fontWeight: 700, color: '#f87171', marginBottom: '2px' }}>
                      AI provider authentication required.
                    </div>
                    <div style={{ fontSize: '0.74rem', color: 'var(--text-secondary)', lineHeight: 1.4 }}>
                      The remote Hugging Face API rejected the request with 401 Unauthorized. BidGuard continues running in resilient offline grounded mode; no fake data is generated.
                    </div>
                  </div>
                </div>
              ) : (
                <div style={{
                  background: 'rgba(16, 185, 129, 0.08)',
                  border: '1px solid var(--border-subtle)',
                  padding: '12px 14px',
                  borderRadius: 'var(--radius-md)',
                  display: 'flex',
                  gap: '10px',
                  alignItems: 'flex-start',
                }}>
                  <CheckCircle2 size={18} color="#10b981" style={{ flexShrink: 0, marginTop: '2px' }} />
                  <div>
                    <div style={{ fontSize: '0.82rem', fontWeight: 700, color: '#15803d', marginBottom: '2px' }}>
                      Fallback Precaution & Resilience Guarantee
                    </div>
                    <div style={{ fontSize: '0.74rem', color: 'var(--text-secondary)', lineHeight: 1.4 }}>
                      {aiStatus.fallbackStatus}
                    </div>
                  </div>
                </div>
              )}

              <div style={{
                background: 'rgba(59, 130, 246, 0.08)',
                border: '1px solid rgba(59, 130, 246, 0.25)',
                padding: '10px 14px',
                borderRadius: 'var(--radius-md)',
                display: 'flex',
                gap: '8px',
                alignItems: 'center',
              }}>
                <ShieldAlert size={16} color="#60a5fa" />
                <span style={{ fontSize: '0.72rem', color: '#93c5fd' }}>
                  Statutory Guardrail: BidGuard AI never selects a winner or autonomously ranks bids.
                </span>
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '18px' }}>
              <button className="btn btn-secondary" onClick={() => setShowStatusModal(false)}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </header>
  );
};

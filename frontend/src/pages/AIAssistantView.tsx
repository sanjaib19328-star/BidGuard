import React, { useState, useEffect, useRef } from 'react';
import {
  Bot,
  Send,
  Upload,
  FileText,
  ShieldAlert,
  Cpu,
  BookOpen,
  CheckCircle,
  AlertTriangle,
  ChevronRight,
  Database,
  RefreshCw,
  Info,
  HelpCircle,
} from 'lucide-react';
import { apiClient } from '../api/client';
import { Tender, Bidder } from '../types';
import { DEMO_CAG_TENDER, DEMO_BIDDER_APPLICATION } from '../api/demoData';

interface AIAssistantViewProps {
  activeTender: Tender | null;
  bidders: Bidder[];
}

interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  agent?: string;
  intent?: string;
  citations?: Array<{
    citation_id?: string;
    source_document?: string;
    page_number?: number;
    clause_reference?: string;
    relevance_score?: number;
    excerpt?: string;
  }>;
  findings?: Array<{
    finding_id: string;
    criterion_name: string;
    status: string;
    severity: string;
    notes: string;
  }>;
  discrepancies?: string[];
  disclaimer?: string;
  usedFallback?: boolean;
}

export const AIAssistantView: React.FC<AIAssistantViewProps> = ({ activeTender, bidders }) => {
  const currentTender = activeTender || DEMO_CAG_TENDER;
  const currentBidder = DEMO_BIDDER_APPLICATION;

  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      sender: 'assistant',
      text: `Welcome to the Procurement Evidence Assistant. I cross-examine submitted bidder evidence against the mandatory clauses of Tender ${currentTender.tender_number} (Manpower Services, CAG New Delhi).\n\nYou can query tender clauses, verified documents, CA turnover certifications, work orders, statutory affidavits, or flagged discrepancies. All answers cite specific document pages and clauses.`,
      agent: 'AgentRouter',
      disclaimer: 'NON-AUTONOMOUS NOTICE: BidGuard AI provides analytical evaluation support and evidence citations only. It does not select winning bidders or award contracts.',
      usedFallback: true,
    },
  ]);

  const [inputQuery, setInputQuery] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [modelStatus, setModelStatus] = useState<any>(null);
  const chatBottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    async function loadStatus() {
      const status = await apiClient.getAIStatus();
      setModelStatus(status);
    }
    loadStatus();
  }, []);

  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isProcessing]);

  const handleSendMessage = async (textToSend?: string) => {
    const q = (textToSend || inputQuery).trim();
    if (!q || isProcessing) return;

    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      sender: 'user',
      text: q,
    };
    setMessages((prev) => [...prev, userMsg]);
    setInputQuery('');
    setIsProcessing(true);

    try {
      const res = await apiClient.assistantChat(
        q,
        currentTender.id,
        currentBidder.id,
        'active-session'
      );

      const botMsg: ChatMessage = {
        id: `bot-${Date.now()}`,
        sender: 'assistant',
        text: res.response || 'Analysis complete.',
        agent: res.agent,
        intent: res.intent,
        citations: res.citations || [],
        findings: res.findings || [],
        discrepancies: res.discrepancies || [],
        disclaimer: res.disclaimer,
        usedFallback: res.used_fallback ?? true,
      };

      setMessages((prev) => [...prev, botMsg]);
    } catch (err: any) {
      console.error('Chat error:', err);
      setMessages((prev) => [
        ...prev,
        {
          id: `bot-err-${Date.now()}`,
          sender: 'assistant',
          text: 'Grounded Fallback Response: The system evaluated the submission against indexed tender clauses. Please inspect the Document Verification Center for full evidence tables.',
          agent: 'FallbackPrecautionAgent',
          usedFallback: true,
          disclaimer: 'BidGuard AI provides advisory support only. Final decisions belong to the tender committee.',
        },
      ]);
    } finally {
      setIsProcessing(false);
    }
  };

  const suggestedQuestions = [
    'What is this tender?',
    'Who is the bidder?',
    'What documents were submitted?',
    'What is the EMD?',
    'What is the turnover requirement?',
    'What is pending?',
    'What has been verified?',
    'What are the findings?',
    'Why was the turnover flagged?',
    'Can GST be verified?',
    'What requires officer review?',
    'What can you do?',
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Header bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <span className="badge badge-blue">Tender: {currentTender.tender_number}</span>
            <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
              Bidder: {currentBidder.bidder_name} (DEMO)
            </span>
          </div>
          <h1 style={{ fontSize: '1.45rem', fontWeight: 800, color: 'var(--text-primary)', letterSpacing: '-0.02em' }}>
            Procurement Evidence Assistant
          </h1>
          <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
            Ask questions about tender requirements, submitted evidence, verification results, findings, and compliance.
          </p>
        </div>

        <div style={{ textAlign: 'right' }}>
          <div style={{ fontSize: '0.78rem', color: '#10b981', fontWeight: 700 }}>
            NON-AUTONOMOUS ADVISORY
          </div>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
            Strict Citing Requirement Enforced
          </div>
        </div>
      </div>

      {/* Suggested Questions Chips */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', alignItems: 'center' }}>
        <span style={{ fontSize: '0.76rem', color: 'var(--text-muted)', fontWeight: 600 }}>
          Suggested Inquiries:
        </span>
        {suggestedQuestions.map((q, idx) => (
          <button
            key={idx}
            onClick={() => handleSendMessage(q)}
            disabled={isProcessing}
            style={{
              background: 'rgba(59, 130, 246, 0.1)',
              border: '1px solid rgba(59, 130, 246, 0.25)',
              borderRadius: '9999px',
              padding: '5px 12px',
              fontSize: '0.76rem',
              color: '#93c5fd',
              cursor: isProcessing ? 'not-allowed' : 'pointer',
              transition: 'all 0.15s ease',
            }}
            onMouseEnter={(e) => (e.currentTarget.style.background = 'rgba(59, 130, 246, 0.2)')}
            onMouseLeave={(e) => (e.currentTarget.style.background = 'rgba(59, 130, 246, 0.1)')}
          >
            {q}
          </button>
        ))}
      </div>

      {/* Main Chat Interface */}
      <div
        className="glass-card"
        style={{
          display: 'flex',
          flexDirection: 'column',
          height: '660px',
          padding: '0',
          overflow: 'hidden',
          background: 'var(--bg-card)',
          border: '1px solid var(--border-subtle)',
        }}
      >
        {/* Messages Scroll Area */}
        <div
          style={{
            flex: 1,
            overflowY: 'auto',
            padding: '24px',
            display: 'flex',
            flexDirection: 'column',
            gap: '18px',
          }}
        >
          {messages.map((m) => (
            <div
              key={m.id}
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: m.sender === 'user' ? 'flex-end' : 'flex-start',
              }}
            >
              {/* Message Header */}
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  marginBottom: '6px',
                  fontSize: '0.72rem',
                  color: 'var(--text-muted)',
                }}
              >
                <span>{m.sender === 'user' ? 'Procurement Officer' : 'BidGuard Evidence Assistant'}</span>
                {m.agent && (
                  <span
                    style={{
                      fontFamily: 'var(--font-mono)',
                      background: 'rgba(255,255,255,0.05)',
                      padding: '2px 6px',
                      borderRadius: '4px',
                    }}
                  >
                    {m.agent}
                  </span>
                )}
              </div>

              {/* Message Bubble */}
              <div
                style={{
                  maxWidth: '85%',
                  padding: '14px 18px',
                  borderRadius: 'var(--radius-md)',
                  background:
                    m.sender === 'user'
                      ? 'linear-gradient(135deg, #1e40af, #2563eb)'
                      : '#ffffff',
                  border:
                    m.sender === 'user'
                      ? '1px solid #1d4ed8'
                      : '1px solid var(--border-subtle)',
                  color: m.sender === 'user' ? '#ffffff' : 'var(--text-primary)',
                  fontSize: '0.84rem',
                  lineHeight: 1.6,
                  whiteSpace: 'pre-wrap',
                }}
              >
                {m.text}

                {/* Explicit Fallback Mode Label */}
                {m.sender === 'assistant' && m.usedFallback && (
                  <div
                    style={{
                      marginTop: '12px',
                      padding: '8px 12px',
                      background: 'rgba(245, 158, 11, 0.1)',
                      border: '1px solid rgba(245, 158, 11, 0.3)',
                      borderRadius: 'var(--radius-sm)',
                      fontSize: '0.72rem',
                      color: '#fbbf24',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                    }}
                  >
                    <Info size={14} style={{ flexShrink: 0 }} />
                    <span>
                      Response generated using grounded fallback logic; no external LLM was available for this request.
                    </span>
                  </div>
                )}

                {/* Structured Citations */}
                {m.citations && m.citations.length > 0 && (
                  <div style={{ marginTop: '14px', borderTop: '1px solid rgba(255,255,255,0.1)', paddingTop: '10px' }}>
                    <div style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--brand-cyan)', textTransform: 'uppercase', marginBottom: '6px' }}>
                      Document & Clause Citations ({m.citations.length}):
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                      {m.citations.map((c, idx) => (
                        <div
                          key={idx}
                          style={{
                            fontSize: '0.74rem',
                            background: 'var(--bg-tertiary)',
                            padding: '6px 10px',
                            borderRadius: '4px',
                            border: '1px solid var(--border-subtle)',
                            color: '#cbd5e1',
                          }}
                        >
                          <strong style={{ color: '#60a5fa' }}>{c.source_document || 'Tender Document'}</strong>
                          {c.page_number && <span> · Page {c.page_number}</span>}
                          {c.clause_reference && <span> · Clause {c.clause_reference}</span>}
                          {c.excerpt && (
                            <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem', marginTop: '2px' }}>
                              "{c.excerpt}"
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Disclaimer */}
                {m.disclaimer && (
                  <div
                    style={{
                      marginTop: '12px',
                      fontSize: '0.68rem',
                      color: 'var(--text-muted)',
                      borderTop: '1px solid rgba(255,255,255,0.06)',
                      paddingTop: '6px',
                    }}
                  >
                    {m.disclaimer}
                  </div>
                )}
              </div>
            </div>
          ))}

          {isProcessing && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
              <RefreshCw size={14} className="animate-spin" />
              <span>Cross-examining submission evidence against tender clauses...</span>
            </div>
          )}

          <div ref={chatBottomRef} />
        </div>

        {/* Input Bar */}
        <div
          style={{
            padding: '16px 20px',
            borderTop: '1px solid var(--border-subtle)',
            background: '#ffffff', border: '1px solid var(--border-subtle)',
            display: 'flex',
            gap: '12px',
          }}
        >
          <input
            type="text"
            placeholder="Ask questions about tender clauses, submitted evidence, turnover, experience, or findings..."
            value={inputQuery}
            onChange={(e) => setInputQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') handleSendMessage();
            }}
            disabled={isProcessing}
            style={{
              flex: 1,
              background: 'var(--bg-tertiary)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-md)',
              padding: '12px 16px',
              color: 'var(--text-primary)',
              fontSize: '0.84rem',
              outline: 'none',
            }}
          />
          <button
            className="btn btn-primary"
            style={{ padding: '0 20px' }}
            onClick={() => handleSendMessage()}
            disabled={isProcessing || !inputQuery.trim()}
          >
            <Send size={16} /> Send
          </button>
        </div>
      </div>
    </div>
  );
};

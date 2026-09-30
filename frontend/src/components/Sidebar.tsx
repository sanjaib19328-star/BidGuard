import React from 'react';
import {
  LayoutDashboard,
  FileSpreadsheet,
  FileCheck2,
  ShieldCheck,
  AlertTriangle,
  GitCompare,
  FileText,
  History,
  Building2,
  Bot,
  FolderKanban,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';

export type NavItem =
  | 'dashboard'
  | 'tenders'
  | 'applications'
  | 'verification'
  | 'compliance'
  | 'findings'
  | 'comparison'
  | 'reports'
  | 'assistant'
  | 'audit';

interface SidebarProps {
  currentTab: NavItem;
  onSelectTab: (tab: NavItem) => void;
  pendingFindingsCount: number;
  collapsed: boolean;
  onToggleCollapse: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentTab,
  onSelectTab,
  pendingFindingsCount,
  collapsed,
  onToggleCollapse,
}) => {
  const navItems: Array<{ id: NavItem; label: string; icon: React.ReactNode; badge?: number | string }> = [
    { id: 'dashboard', label: 'Dashboard', icon: <LayoutDashboard size={19} /> },
    { id: 'tenders', label: 'Tenders', icon: <Building2 size={19} /> },
    { id: 'applications', label: 'Bidder Applications', icon: <FolderKanban size={19} />, badge: 'Demo' },
    { id: 'verification', label: 'Document Verification', icon: <ShieldCheck size={19} /> },
    { id: 'compliance', label: 'Compliance Matrix', icon: <FileSpreadsheet size={19} /> },
    {
      id: 'findings',
      label: 'Risk & Findings',
      icon: <AlertTriangle size={19} />,
      badge: pendingFindingsCount > 0 ? pendingFindingsCount : undefined,
    },
    { id: 'comparison', label: 'Multi-Bidder Compare', icon: <GitCompare size={19} /> },
    { id: 'reports', label: 'Compliance Dossiers', icon: <FileText size={19} /> },
    { id: 'assistant', label: 'AI Assistant', icon: <Bot size={19} /> },
    { id: 'audit', label: 'Immutable Audit Trail', icon: <History size={19} /> },
  ];

  return (
    <aside
      className={`sidebar ${collapsed ? 'collapsed' : ''}`}
      aria-label="Primary Navigation"
    >
      {/* Brand Header */}
      <div
        style={{
          padding: collapsed ? '16px 8px' : '20px 16px',
          borderBottom: '1px solid var(--border-subtle)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: collapsed ? 'center' : 'space-between',
          gap: '8px',
          transition: 'all 0.2s ease',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', minWidth: 0 }}>
          <div
            style={{
              width: '36px',
              height: '36px',
              borderRadius: '9px',
              background: 'var(--brand-gradient)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 0 14px rgba(59, 130, 246, 0.4)',
              flexShrink: 0,
            }}
            title="BidGuard AI - GeM Verification Platform"
          >
            <FileCheck2 size={20} color="#ffffff" />
          </div>
          {!collapsed && (
            <div style={{ overflow: 'hidden', whiteSpace: 'nowrap' }}>
              <h2 style={{ fontSize: '1rem', fontWeight: 800, letterSpacing: '-0.02em', color: 'var(--text-primary)' }}>
                BidGuard <span style={{ color: 'var(--brand-cyan)' }}>AI</span>
              </h2>
              <p style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', fontWeight: 500 }}>
                GeM Verification Platform
              </p>
            </div>
          )}
        </div>

        {/* Hide / Expand Toggle Button */}
        <button
          onClick={onToggleCollapse}
          className="sidebar-toggle-btn"
          aria-label={collapsed ? 'Show Navigation' : 'Hide Navigation'}
          title={collapsed ? 'Show Navigation' : 'Hide Navigation'}
          style={{
            background: '#f8fafc',
            border: '1px solid var(--border-subtle)',
            borderRadius: '6px',
            color: 'var(--text-secondary)',
            cursor: 'pointer',
            padding: '6px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transition: 'all 0.15s ease',
            flexShrink: 0,
            marginTop: collapsed ? '8px' : '0',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = 'rgba(37, 99, 235, 0.1)'; e.currentTarget.style.color = 'var(--brand-blue)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = '#f8fafc';
            e.currentTarget.style.color = 'var(--text-secondary)';
          }}
        >
          {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
        </button>
      </div>

      {/* Primary Navigation Menu */}
      <nav
        style={{
          padding: collapsed ? '12px 6px' : '16px 12px',
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          gap: '4px',
          overflowY: 'auto',
          overflowX: 'hidden',
        }}
      >
        {!collapsed ? (
          <div
            style={{
              fontSize: '0.68rem',
              fontWeight: 700,
              color: 'var(--text-muted)',
              textTransform: 'uppercase',
              letterSpacing: '0.08em',
              padding: '6px 12px 10px 12px',
            }}
          >
            Verification Suite
          </div>
        ) : (
          <div
            style={{
              height: '1px',
              background: 'var(--border-subtle)',
              margin: '6px 8px 10px 8px',
            }}
          />
        )}

        {navItems.map((item) => {
          const isActive = currentTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onSelectTab(item.id)}
              aria-label={item.label}
              title={item.label}
              data-nav-item={item.id}
              className={`sidebar-nav-item ${isActive ? 'active' : ''} ${collapsed ? 'collapsed' : ''}`}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: collapsed ? 'center' : 'space-between',
                padding: collapsed ? '10px 0' : '10px 14px',
                borderRadius: 'var(--radius-md)',
                background: isActive ? '#eff6ff' : 'transparent',
                color: isActive ? 'var(--brand-blue)' : 'var(--text-secondary)',
                fontWeight: isActive ? 600 : 500,
                fontSize: '0.86rem',
                border: isActive ? '1px solid #bfdbfe' : '1px solid transparent',
                cursor: 'pointer',
                transition: 'all 0.15s ease',
                textAlign: 'left',
                position: 'relative',
                width: '100%',
              }}
              onMouseEnter={(e) => {
                if (!isActive) e.currentTarget.style.background = 'var(--bg-hover)';
              }}
              onMouseLeave={(e) => {
                if (!isActive) e.currentTarget.style.background = 'transparent';
              }}
            >
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                  justifyContent: collapsed ? 'center' : 'flex-start',
                }}
              >
                <span
                  style={{
                    color: isActive ? 'var(--brand-blue)' : 'inherit',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  {item.icon}
                </span>
                {!collapsed && <span>{item.label}</span>}
              </div>

              {!collapsed && item.badge !== undefined && (
                <span
                  style={{
                    background: typeof item.badge === 'number' ? '#ef4444' : 'rgba(59, 130, 246, 0.3)',
                    color: typeof item.badge === 'number' ? 'white' : '#93c5fd',
                    fontSize: '0.7rem',
                    fontWeight: 700,
                    padding: '2px 7px',
                    borderRadius: '9999px',
                    border: typeof item.badge === 'number' ? 'none' : '1px solid rgba(59, 130, 246, 0.4)',
                  }}
                >
                  {item.badge}
                </span>
              )}

              {collapsed && item.badge !== undefined && (
                <span
                  style={{
                    position: 'absolute',
                    top: '6px',
                    right: '8px',
                    width: '7px',
                    height: '7px',
                    borderRadius: '50%',
                    background: typeof item.badge === 'number' ? '#ef4444' : 'var(--brand-cyan)',
                    boxShadow: typeof item.badge === 'number' ? '0 0 6px #ef4444' : '0 0 6px var(--brand-cyan)',
                  }}
                  title={`${item.label}: ${item.badge} pending`}
                />
              )}
            </button>
          );
        })}
      </nav>

      {/* Statutory Guardrail Notice in Sidebar */}
      {!collapsed ? (
        <div
          style={{
            padding: '12px 14px',
            margin: '12px',
            background: '#f0fdf4', borderRadius: 'var(--radius-md)', border: '1px solid #bbf7d0',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
            <ShieldCheck size={16} color="#10b981" />
            <span
              style={{
                fontSize: '0.72rem',
                fontWeight: 800,
                color: '#10b981',
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
              }}
            >
              Officer Safeguard
            </span>
          </div>
          <p style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', lineHeight: 1.45 }}>
            BidGuard AI provides evidence, verification results, and analytical findings. Final procurement decisions
            remain with the designated Procurement Officer.
          </p>
        </div>
      ) : (
        <div
          style={{
            margin: '12px 6px',
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            padding: '10px 0',
            borderTop: '1px solid var(--border-subtle)',
          }}
          title="Officer Safeguard: BidGuard AI provides evidence, verification results, and analytical findings. Final procurement decisions remain with the designated Procurement Officer."
          aria-label="Officer Safeguard"
        >
          <div
            style={{
              width: '32px',
              height: '32px',
              borderRadius: '8px',
              background: 'rgba(16, 185, 129, 0.1)',
              border: '1px solid rgba(16, 185, 129, 0.3)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'help',
            }}
          >
            <ShieldCheck size={18} color="#10b981" />
          </div>
        </div>
      )}
    </aside>
  );
};

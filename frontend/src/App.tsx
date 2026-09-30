import React, { useState, useEffect } from 'react';
import { Sidebar, NavItem } from './components/Sidebar';
import { Header } from './components/Header';
import { DashboardView } from './pages/DashboardView';
import { TendersView } from './pages/TendersView';
import { ComplianceMatrixView } from './pages/ComplianceMatrixView';
import { VerificationCenterView } from './pages/VerificationCenterView';
import { FindingsCenterView } from './pages/FindingsCenterView';
import { ComparisonView } from './pages/ComparisonView';
import { ReportsView } from './pages/ReportsView';
import { AuditTrailView } from './pages/AuditTrailView';
import { AIAssistantView } from './pages/AIAssistantView';
import { ApplicationsView } from './pages/ApplicationsView';
import { apiClient } from './api/client';
import {
  Tender,
  Bidder,
  Clause,
  ComplianceMatrixItem,
  OfficerFinding,
  VerificationRecord,
  AuditLogItem,
} from './types';
import {
  DEMO_CAG_TENDER,
  DEMO_AUDIT_LOGS,
  DEMO_FINDINGS,
} from './api/demoData';

export const App: React.FC = () => {
  const [currentTab, setCurrentTab] = useState<NavItem>('dashboard');
  const [sidebarCollapsed, setSidebarCollapsed] = useState<boolean>(false);
  const [tenders, setTenders] = useState<Tender[]>([DEMO_CAG_TENDER]);
  const [activeTender, setActiveTender] = useState<Tender | null>(DEMO_CAG_TENDER);
  const [bidders, setBidders] = useState<Bidder[]>([]);
  const [clauses, setClauses] = useState<Clause[]>([]);
  const [matrixItems, setMatrixItems] = useState<ComplianceMatrixItem[]>([]);
  const [findings, setFindings] = useState<OfficerFinding[]>(DEMO_FINDINGS);
  const [verifications, setVerifications] = useState<VerificationRecord[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLogItem[]>(DEMO_AUDIT_LOGS);
  const [isLiveConnected, setIsLiveConnected] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  // Load real data from backend API
  useEffect(() => {
    async function loadData() {
      setIsLoading(true);
      try {
        const isHealthy = await apiClient.checkHealth();
        setIsLiveConnected(isHealthy);

        if (isHealthy) {
          const liveTenders = await apiClient.getTenders().catch(() => []);
          if (liveTenders.length > 0) {
            setTenders(liveTenders);
            setActiveTender(liveTenders[0]);
            const [c, m, f] = await Promise.all([
              apiClient.getClauses(liveTenders[0].id).catch(() => []),
              apiClient.getComplianceMatrix(liveTenders[0].id).catch(() => []),
              apiClient.getFindings(liveTenders[0].id).catch(() => []),
            ]);
            setClauses(c);
            if (m && m.length > 0) setMatrixItems(m);
            if (f && f.length > 0) setFindings(f);
          }

          const [b, v] = await Promise.all([
            apiClient.getBidders().catch(() => []),
            apiClient.getVerifications().catch(() => []),
          ]);
          if (b && b.length > 0) setBidders(b);
          if (v && v.length > 0) setVerifications(v);
        }
      } catch (err) {
        console.error('Error fetching live data:', err);
        setIsLiveConnected(false);
      } finally {
        setIsLoading(false);
      }
    }
    loadData();
  }, []);

  // When active tender changes, reload clauses & matrix
  useEffect(() => {
    if (!activeTender) return;
    async function loadTenderDetails() {
      if (!activeTender) return;
      try {
        const [c, m, f] = await Promise.all([
          apiClient.getClauses(activeTender.id).catch(() => []),
          apiClient.getComplianceMatrix(activeTender.id).catch(() => []),
          apiClient.getFindings(activeTender.id).catch(() => []),
        ]);
        setClauses(c);
        setMatrixItems(m);
        if (f && f.length > 0) {
          setFindings(f);
        } else if (activeTender.tender_number === DEMO_CAG_TENDER.tender_number) {
          setFindings(DEMO_FINDINGS);
        } else {
          setFindings([]);
        }
      } catch (err) {
        console.error('Failed to load tender details:', err);
      }
    }
    loadTenderDetails();
  }, [activeTender]);

  const refreshFindings = async () => {
    if (!activeTender) return;
    try {
      const f = await apiClient.getFindings(activeTender.id);
      setFindings(f);
    } catch (_) {}
  };

  const pendingFindingsCount = findings.filter((f) => f.review_status === 'PENDING').length;

  const handleCreateTender = (newTender: Tender) => {
    setTenders((prev) => [newTender, ...prev.filter((t) => t.id !== newTender.id)]);
    setActiveTender(newTender);
  };

  return (
    <div className={`app-container ${sidebarCollapsed ? 'sidebar-is-collapsed' : ''}`}>
      {/* Left Sidebar Navigation */}
      <Sidebar
        currentTab={currentTab}
        onSelectTab={setCurrentTab}
        pendingFindingsCount={pendingFindingsCount}
        collapsed={sidebarCollapsed}
        onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
      />

      {/* Main View Area */}
      <main className="main-content">
        <Header
          activeTender={activeTender}
          tenders={tenders}
          onSelectTender={setActiveTender}
          isLiveConnected={isLiveConnected}
        />

        <div className="content-body">
          {currentTab === 'dashboard' && (
            <DashboardView
              tenders={tenders}
              bidders={bidders}
              findings={findings}
              activeTender={activeTender}
              onSelectTender={setActiveTender}
              onNavigate={setCurrentTab}
            />
          )}

          {currentTab === 'assistant' && (
            <AIAssistantView
              activeTender={activeTender}
              bidders={bidders}
            />
          )}

          {currentTab === 'tenders' && (
            <TendersView
              tenders={tenders}
              activeTender={activeTender}
              onSelectTender={setActiveTender}
              onNavigate={setCurrentTab}
              onCreateTender={handleCreateTender}
            />
          )}

          {currentTab === 'applications' && (
            <ApplicationsView
              activeTender={activeTender}
              onNavigate={setCurrentTab}
            />
          )}

          {currentTab === 'compliance' && (
            <ComplianceMatrixView
              matrixItems={matrixItems}
              activeTender={activeTender}
              bidders={bidders}
              onNavigate={setCurrentTab}
            />
          )}

          {currentTab === 'verification' && (
            <VerificationCenterView
              verifications={verifications}
              bidders={bidders}
              activeTender={activeTender}
            />
          )}

          {currentTab === 'findings' && (
            <FindingsCenterView
              findings={findings}
              onRefreshFindings={refreshFindings}
            />
          )}

          {currentTab === 'comparison' && (
            <ComparisonView
              bidders={bidders}
              activeTender={activeTender}
              onNavigate={setCurrentTab}
            />
          )}

          {currentTab === 'reports' && (
            <ReportsView
              activeTender={activeTender}
              bidders={bidders}
            />
          )}

          {currentTab === 'audit' && (
            <AuditTrailView logs={auditLogs} />
          )}
        </div>
      </main>
    </div>
  );
};

export default App;

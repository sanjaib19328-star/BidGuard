"""
Agent Architecture for BidGuard AI.
Contains Document Agent, RAG Agent, Analysis Agent, Router, and AIAssistantService.
"""

from app.services.ai.agents.document_agent import (
    DocumentAgent,
    DocumentAnalysisOutput,
    ParsedClause,
)
from app.services.ai.agents.rag_agent import (
    RAGAgent,
    RAGRetrievalResult,
    RetrievedCitation,
)
from app.services.ai.agents.analysis_agent import (
    AnalysisAgent,
    ComplianceFinding,
    ProcurementAnalysisOutput,
)
from app.services.ai.agents.agent_router import (
    AgentIntent,
    AgentRouter,
)
from app.services.ai.agents.assistant_service import (
    AIAssistantService,
    get_assistant_service,
)

__all__ = [
    "DocumentAgent",
    "DocumentAnalysisOutput",
    "ParsedClause",
    "RAGAgent",
    "RAGRetrievalResult",
    "RetrievedCitation",
    "AnalysisAgent",
    "ComplianceFinding",
    "ProcurementAnalysisOutput",
    "AgentIntent",
    "AgentRouter",
    "AIAssistantService",
    "get_assistant_service",
]

"""
AI Assistant Orchestration Service for BidGuard AI.
Coordinates multi-agent workflows, Document AI, vector-based RAG, and analytical synthesis.
Implements non-autonomous procurement guardrails and end-to-end fallback precautions.
"""

from typing import Any, Dict, List, Optional
import logging
import uuid

from app.services.ai.agents.agent_router import AgentRouter
from app.services.ai.agents.document_agent import DocumentAgent, DocumentAnalysisOutput
from app.services.ai.agents.rag_agent import RAGAgent
from app.services.ai.agents.analysis_agent import AnalysisAgent
from app.services.ai.providers import get_ai_providers

logger = logging.getLogger(__name__)


class AIAssistantService:
    """
    Main entry point for AI Assistant operations across BidGuard AI.
    """

    def __init__(self):
        self.router = AgentRouter()
        self.document_agent = self.router.document_agent
        self.rag_agent = self.router.rag_agent
        self.analysis_agent = self.router.analysis_agent

    async def chat(
        self,
        query: str,
        tender_id: Optional[str] = None,
        bidder_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        requirements: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Handle a conversational query from the user or procurement committee.
        Routes to appropriate agent with full fallback precaution.
        """
        conv_id = conversation_id or str(uuid.uuid4())
        try:
            # 1. Deterministic canonical procurement intent resolution (fast, zero hallucination)
            from app.services.ai.agents.procurement_intent_engine import resolve_procurement_query
            deterministic_res = resolve_procurement_query(
                query=query,
                tender_id=tender_id,
                bidder_id=bidder_id,
                conversation_id=conv_id,
            )
            if deterministic_res is not None:
                deterministic_res["conversation_id"] = conv_id
                return deterministic_res

            # 2. Agent routing and execution for complex analytical queries
            result = await self.router.route_and_execute(
                query=query,
                tender_id=tender_id,
                bidder_id=bidder_id,
                requirements=requirements,
            )
            result["conversation_id"] = conv_id
            return result
        except Exception as exc:
            # Fallback Precaution: Never let an unhandled error propagate up to crash the API
            logger.error("Unexpected error in AIAssistantService.chat: %s. Returning fallback response.", exc)
            return {
                "conversation_id": conv_id,
                "intent": "GENERAL_ASSISTANCE",
                "agent": "FallbackPrecautionHandler",
                "response": (
                    "BidGuard AI encountered an unexpected error processing your request. "
                    "Fallback precautions were activated. Please review procurement documents manually."
                ),
                "citations": [],
                "disclaimer": (
                    "NON-AUTONOMOUS NOTICE: BidGuard AI is a non-binding decision support tool. "
                    "All final procurement decisions must be made by the authorized procurement committee."
                ),
                "used_fallback": True,
            }

    async def analyze_document(
        self,
        content: bytes,
        filename: str,
        document_type: str = "TENDER_SPECIFICATION",
        tender_id: Optional[str] = None,
        bidder_id: Optional[str] = None,
        auto_index_rag: bool = True,
    ) -> Dict[str, Any]:
        """
        Analyze an uploaded PDF or document using LayoutLMv3 and TrOCR,
        and optionally index its extracted clauses into the RAG vector store.
        """
        try:
            doc_id = filename or str(uuid.uuid4())
            analysis_output: DocumentAnalysisOutput = await self.document_agent.analyze_document(
                document_id=doc_id,
                content=content,
                filename=filename,
                document_type=document_type,
            )

            # Auto-index clauses into RAG vector store for retrieval
            indexed_chunks = 0
            if auto_index_rag and analysis_output.clauses:
                try:
                    chunks_to_index = [
                        {
                            "text": cl.text,
                            "page_number": cl.page_number,
                            "clause_reference": f"{cl.clause_number} {cl.title}",
                            "tender_id": tender_id,
                            "bidder_id": bidder_id,
                        }
                        for cl in analysis_output.clauses
                    ]
                    indexed_chunks = await self.rag_agent.index_document_chunks(
                        document_id=doc_id,
                        chunks=chunks_to_index,
                        document_title=filename,
                    )
                except Exception as index_exc:
                    logger.warning("Error auto-indexing clauses into RAG vector store: %s. Continuing with fallback.", index_exc)

            return {
                "document_id": analysis_output.document_id,
                "document_type": analysis_output.document_type,
                "total_pages": analysis_output.total_pages,
                "clause_count": len(analysis_output.clauses),
                "clauses": [cl.__dict__ for cl in analysis_output.clauses],
                "table_count": len(analysis_output.tables),
                "tables": analysis_output.tables,
                "summary": analysis_output.summary,
                "indexed_chunks": indexed_chunks,
                "used_fallback": analysis_output.used_fallback,
            }

        except Exception as exc:
            logger.error("Unexpected error in AIAssistantService.analyze_document: %s. Using fallback precaution.", exc)
            return {
                "document_id": filename or "unknown",
                "document_type": document_type,
                "total_pages": 1,
                "clause_count": 1,
                "clauses": [
                    {
                        "clause_id": "fallback-1",
                        "clause_number": "1.0",
                        "title": "Document General Section",
                        "text": "Document processed via fallback precaution.",
                        "clause_type": "GENERAL",
                        "page_number": 1,
                        "confidence": 0.7,
                    }
                ],
                "table_count": 0,
                "tables": [],
                "summary": "Document processed using deterministic fallback precaution.",
                "indexed_chunks": 0,
                "used_fallback": True,
            }

    async def get_system_status(self) -> Dict[str, Any]:
        """Check status of all Hugging Face models and agent components."""
        status = {}
        try:
            providers = await get_ai_providers()
            for name, prov in providers.items():
                status[name] = {
                    "model_id": getattr(prov, "model_id", "unknown"),
                    "device": getattr(prov, "device", "cpu"),
                    "initialized": getattr(prov, "is_initialized", False),
                }
        except Exception as exc:
            logger.warning("Error getting provider status: %s", exc)
            status["error"] = str(exc)

        status["vector_store_chunks"] = self.rag_agent.vector_store.count()
        status["guardrail_enforced"] = True
        return status


_assistant_service: Optional[AIAssistantService] = None


def get_assistant_service() -> AIAssistantService:
    """Get singleton assistant service instance."""
    global _assistant_service
    if _assistant_service is None:
        _assistant_service = AIAssistantService()
    return _assistant_service

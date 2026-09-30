"""
Agent Router for BidGuard AI.
Classifies procurement queries and routes tasks to Document Analysis, RAG, and Analysis agents.
Enforces fallback precautions for all unexpected errors and malformed inputs.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
import logging
import re

from app.services.ai.agents.analysis_agent import AnalysisAgent, ProcurementAnalysisOutput
from app.services.ai.agents.document_agent import DocumentAgent, DocumentAnalysisOutput
from app.services.ai.agents.rag_agent import RAGAgent, RAGRetrievalResult
from app.services.ai.providers import LLMProvider, LLMResponse, get_ai_providers

logger = logging.getLogger(__name__)


class AgentIntent(str, Enum):
    DOCUMENT_ANALYSIS = "DOCUMENT_ANALYSIS"
    RAG_SEARCH = "RAG_SEARCH"
    COMPLIANCE_ANALYSIS = "COMPLIANCE_ANALYSIS"
    GENERAL_ASSISTANCE = "GENERAL_ASSISTANCE"


class AgentRouter:
    """
    Intelligent router coordinating specialized procurement agents.
    """

    def __init__(
        self,
        document_agent: Optional[DocumentAgent] = None,
        rag_agent: Optional[RAGAgent] = None,
        analysis_agent: Optional[AnalysisAgent] = None,
        llm_provider: Optional[LLMProvider] = None,
    ):
        self.document_agent = document_agent or DocumentAgent()
        self.rag_agent = rag_agent or RAGAgent()
        self.analysis_agent = analysis_agent or AnalysisAgent()
        self.llm = llm_provider

    async def _ensure_providers(self):
        if not self.llm:
            try:
                providers = await get_ai_providers()
                self.llm = providers.get("llm")
            except Exception as exc:
                logger.warning("Error getting LLM provider in AgentRouter: %s. Using fallback precaution.", exc)
                self.llm = LLMProvider("Qwen/Qwen2.5-1.5B-Instruct")

    def classify_intent(self, query: str, has_document: bool = False) -> AgentIntent:
        """
        Classify user query intent using procurement keywords and heuristics.
        Includes complete fallback precaution if parsing fails.
        """
        if not query:
            return AgentIntent.DOCUMENT_ANALYSIS if has_document else AgentIntent.GENERAL_ASSISTANCE

        try:
            q_lower = query.lower()

            # 1. Document analysis cues
            doc_keywords = ["layout", "ocr", "table", "structure", "page", "scanned", "transcribe", "summary of document"]
            if has_document or any(k in q_lower for k in doc_keywords):
                if any(k in q_lower for k in ["ocr", "transcribe", "layout", "table", "structure"]):
                    return AgentIntent.DOCUMENT_ANALYSIS

            # 2. Compliance / Discrepancy analysis cues
            compliance_keywords = [
                "compliant", "compliance", "discrepancy", "non-compliant", "deviation",
                "violation", "eligibility", "mandatory", "statutory", "audit", "cross-check",
                "disqualify", "criteria", "matrix", "rule", "penalty"
            ]
            if any(k in q_lower for k in compliance_keywords):
                return AgentIntent.COMPLIANCE_ANALYSIS

            # 3. Retrieval / RAG search cues
            rag_keywords = [
                "clause", "section", "find", "search", "where does it say", "what is the turnover",
                "requirement", "specification", "experience required", "validity", "emd", "guarantee",
                "where", "specify", "warranty", "duration", "timeline", "tender",
                "turnover", "certificate", "evidence", "experience", "work order", "show", "document",
                "submit", "details", "submitted", "financial",
            ]
            if any(k in q_lower for k in rag_keywords):
                return AgentIntent.RAG_SEARCH

            return AgentIntent.GENERAL_ASSISTANCE

        except Exception as exc:
            logger.warning("Intent classification unexpected error: %s. Falling back to RAG_SEARCH.", exc)
            return AgentIntent.RAG_SEARCH

    async def route_and_execute(
        self,
        query: str,
        tender_id: Optional[str] = None,
        bidder_id: Optional[str] = None,
        document_content: Optional[bytes] = None,
        filename: str = "",
        requirements: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Route request to the appropriate agent pipeline and synthesize response.
        Applies exhaustive fallback precautions to guarantee safe, non-crashing execution.
        """
        await self._ensure_providers()

        has_doc = document_content is not None and len(document_content) > 0
        intent = self.classify_intent(query, has_document=has_doc)
        logger.info("AgentRouter classified query intent as: %s", intent.value)

        try:
            if intent == AgentIntent.DOCUMENT_ANALYSIS and has_doc:
                # Delegate to DocumentAgent
                doc_out: DocumentAnalysisOutput = await self.document_agent.analyze_document(
                    document_id=filename or "doc-analysis",
                    content=document_content,
                    filename=filename,
                )
                return {
                    "intent": intent.value,
                    "agent": "DocumentAgent",
                    "output": doc_out,
                    "response": doc_out.summary,
                    "citations": [],
                    "used_fallback": doc_out.used_fallback,
                }

            elif intent == AgentIntent.COMPLIANCE_ANALYSIS:
                # Multi-agent coordination: RAGAgent retrieves evidence, AnalysisAgent verifies compliance
                rag_filter = {}
                if tender_id:
                    rag_filter["tender_id"] = tender_id
                if bidder_id:
                    rag_filter["bidder_id"] = bidder_id

                rag_res: RAGRetrievalResult = await self.rag_agent.retrieve(
                    query=query,
                    top_k=6,
                    filter_metadata=rag_filter or None,
                )

                passages = [
                    {
                        "source_document": c.source_document,
                        "page_number": c.page_number,
                        "text": c.text,
                    }
                    for c in rag_res.citations
                ]

                analysis_out: ProcurementAnalysisOutput = await self.analysis_agent.cross_examine_compliance(
                    tender_id=tender_id,
                    bidder_id=bidder_id,
                    requirements=requirements or [],
                    bidder_passages=passages,
                    query=query,
                )

                return {
                    "intent": intent.value,
                    "agent": "AnalysisAgent",
                    "output": analysis_out,
                    "response": analysis_out.summary,
                    "findings": [f.__dict__ for f in analysis_out.findings],
                    "discrepancies": analysis_out.discrepancies,
                    "citations": analysis_out.citations,
                    "disclaimer": analysis_out.disclaimer,
                    "used_fallback": analysis_out.used_fallback or rag_res.used_fallback,
                }

            elif intent == AgentIntent.RAG_SEARCH:
                # Delegate to RAGAgent + synthesize answer via LLM
                rag_res: RAGRetrievalResult = await self.rag_agent.retrieve(
                    query=query,
                    top_k=5,
                )

                context_passages = [f"[{c.source_document} - Page {c.page_number}]: {c.text}" for c in rag_res.citations]

                llm_response: LLMResponse = await self.llm.generate(
                    prompt=f"Answer the procurement question based on the retrieved evidence passages:\nQuestion: {query}",
                    context_passages=context_passages,
                    temperature=0.2,
                )

                citations = [
                    {
                        "citation_id": c.citation_id,
                        "source_document": c.source_document,
                        "page_number": c.page_number,
                        "clause_reference": c.clause_reference,
                        "relevance_score": c.relevance_score,
                        "excerpt": c.text[:150],
                    }
                    for c in rag_res.citations
                ]

                return {
                    "intent": intent.value,
                    "agent": "RAGAgent",
                    "output": rag_res,
                    "response": llm_response.content,
                    "citations": citations,
                    "disclaimer": llm_response.disclaimer,
                    "used_fallback": rag_res.used_fallback or llm_response.used_fallback,
                }

            else:
                # General Assistance
                llm_response = await self.llm.generate(
                    prompt=f"Provide procurement analysis guidance for the following inquiry: {query}",
                    temperature=0.3,
                )
                return {
                    "intent": intent.value,
                    "agent": "GeneralAssistant",
                    "response": llm_response.content,
                    "citations": [],
                    "disclaimer": llm_response.disclaimer,
                    "used_fallback": llm_response.used_fallback,
                }

        except Exception as exc:
            # Fallback Precaution: Catch all agent-routing errors and return safe guidance
            logger.error("Unexpected error in AgentRouter.route_and_execute: %s. Using fallback precaution.", exc)
            return {
                "intent": intent.value if "intent" in locals() else "GENERAL_ASSISTANCE",
                "agent": "FallbackPrecautionRouter",
                "response": (
                    f"BidGuard AI encountered an operational exception during agent execution ({str(exc)}). "
                    f"A fallback response was generated. The system remains operational. "
                    f"Please consult procurement documentation directly for verification."
                ),
                "citations": [],
                "disclaimer": (
                    "NON-AUTONOMOUS NOTICE: BidGuard AI provides analytical evaluation support only. "
                    "The procurement committee retains final responsibility for all decisions."
                ),
                "used_fallback": True,
            }

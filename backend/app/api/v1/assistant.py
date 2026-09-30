"""
API Endpoints for the BidGuard AI Assistant and Multi-Agent Layer.
Exposes conversational chat, document analysis, and AI model stack status.
Includes strict fallback precautions for all unexpected errors.
"""

from typing import Any, Dict, List, Optional
import logging
from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from pydantic import BaseModel, Field

from app.api.deps import get_current_user, get_current_user_optional
from app.models.user import User
from app.services.ai.agents import get_assistant_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/assistant", tags=["AI Assistant"])


class AssistantChatRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Analytical or procurement question")
    tender_id: Optional[str] = Field(None, description="Optional tender ID scope")
    bidder_id: Optional[str] = Field(None, description="Optional bidder ID scope")
    conversation_id: Optional[str] = Field(None, description="Persistent conversation session ID")


class AssistantChatResponse(BaseModel):
    conversation_id: str
    intent: str
    agent: str
    response: str
    citations: List[Dict[str, Any]] = Field(default_factory=list)
    findings: Optional[List[Dict[str, Any]]] = None
    discrepancies: Optional[List[str]] = None
    disclaimer: str
    used_fallback: bool = False


class DocumentAnalysisResponse(BaseModel):
    document_id: str
    document_type: str
    total_pages: int
    clause_count: int
    clauses: List[Dict[str, Any]] = Field(default_factory=list)
    table_count: int
    tables: List[Dict[str, Any]] = Field(default_factory=list)
    summary: str
    indexed_chunks: int = 0
    used_fallback: bool = False


@router.post("/chat", response_model=AssistantChatResponse)
async def chat_with_assistant(
    request: AssistantChatRequest,
    current_user: User = Depends(get_current_user_optional),
) -> AssistantChatResponse:
    """
    Chat with the BidGuard AI Assistant.
    Coordinates Document, RAG, and Analysis agents based on query intent.
    Implements non-autonomous guardrails and complete fallback precautions.
    """
    assistant_service = get_assistant_service()

    try:
        result = await assistant_service.chat(
            query=request.query,
            tender_id=request.tender_id,
            bidder_id=request.bidder_id,
            conversation_id=request.conversation_id,
        )

        return AssistantChatResponse(
            conversation_id=result.get("conversation_id", request.conversation_id or "default"),
            intent=result.get("intent", "GENERAL_ASSISTANCE"),
            agent=result.get("agent", "AIAssistant"),
            response=result.get("response", "Analysis completed."),
            citations=result.get("citations", []),
            findings=result.get("findings"),
            discrepancies=result.get("discrepancies"),
            disclaimer=result.get(
                "disclaimer",
                "BidGuard AI provides analytical evaluation support only. "
                "Final decisions rest entirely with the authorized procurement authority.",
            ),
            used_fallback=result.get("used_fallback", False),
        )

    except Exception as exc:
        # Fallback Precaution: Catch all unhandled exceptions and return safe structured response
        logger.error("Unexpected error in /assistant/chat: %s. Using fallback precaution.", exc)
        return AssistantChatResponse(
            conversation_id=request.conversation_id or "fallback-session",
            intent="GENERAL_ASSISTANCE",
            agent="FallbackPrecautionAgent",
            response=(
                "BidGuard AI Assistant encountered an unexpected error processing your request. "
                "Fallback precautions have been activated. Please review tender documents directly."
            ),
            citations=[],
            findings=[],
            discrepancies=[],
            disclaimer=(
                "NON-AUTONOMOUS NOTICE: BidGuard AI is an advisory decision support system. "
                "The procurement authority remains solely responsible for tender awards."
            ),
            used_fallback=True,
        )


@router.post("/analyze-document", response_model=DocumentAnalysisResponse)
async def analyze_document_endpoint(
    file: UploadFile = File(...),
    document_type: str = Form("TENDER_SPECIFICATION"),
    tender_id: Optional[str] = Form(None),
    bidder_id: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
) -> DocumentAnalysisResponse:
    """
    Analyze an uploaded tender specification or bidder document using LayoutLMv3 and TrOCR.
    Segments clauses, extracts tables, and auto-indexes chunks into the RAG vector store.
    """
    assistant_service = get_assistant_service()

    try:
        content = await file.read()
        res = await assistant_service.analyze_document(
            content=content,
            filename=file.filename or "uploaded_document",
            document_type=document_type,
            tender_id=tender_id,
            bidder_id=bidder_id,
            auto_index_rag=True,
        )

        return DocumentAnalysisResponse(
            document_id=res["document_id"],
            document_type=res["document_type"],
            total_pages=res["total_pages"],
            clause_count=res["clause_count"],
            clauses=res["clauses"],
            table_count=res["table_count"],
            tables=res["tables"],
            summary=res["summary"],
            indexed_chunks=res.get("indexed_chunks", 0),
            used_fallback=res.get("used_fallback", False),
        )

    except Exception as exc:
        # Fallback Precaution: Return safe fallback analysis response
        logger.error("Unexpected error in /assistant/analyze-document: %s. Using fallback precaution.", exc)
        return DocumentAnalysisResponse(
            document_id=file.filename or "unknown",
            document_type=document_type,
            total_pages=1,
            clause_count=1,
            clauses=[
                {
                    "clause_id": "fallback-1",
                    "clause_number": "1.0",
                    "title": "General Procurement Terms",
                    "text": "Extracted via fallback precaution.",
                    "clause_type": "GENERAL",
                    "page_number": 1,
                    "confidence": 0.7,
                }
            ],
            table_count=0,
            tables=[],
            summary="Document parsed with deterministic fallback precaution due to an unexpected error.",
            indexed_chunks=0,
            used_fallback=True,
        )


@router.get("/status")
async def get_ai_status(
    current_user: User = Depends(get_current_user_optional),
) -> Dict[str, Any]:
    """
    Retrieve operational health, model IDs, hardware devices, and vector store metrics.
    """
    assistant_service = get_assistant_service()
    try:
        status_info = await assistant_service.get_system_status()
        return {
            "status": "healthy",
            "models": status_info,
            "system": {
                "guardrail_enforced": True,
                "autonomous_decisions_prohibited": True,
            },
        }
    except Exception as exc:
        logger.warning("Error fetching AI status: %s. Using fallback precaution.", exc)
        return {
            "status": "degraded_fallback",
            "error": str(exc),
            "system": {
                "guardrail_enforced": True,
                "autonomous_decisions_prohibited": True,
            },
        }

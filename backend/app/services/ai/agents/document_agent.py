"""
Document Analysis Agent for BidGuard AI.
Uses LayoutLMv3 and TrOCR to parse tender specifications and bidder submissions into structured clauses and tables.
Equipped with complete fallback precautions for all unexpected errors.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import logging

from app.services.ai.providers import (
    DocumentAIProvider,
    DocumentLayoutResult,
    LayoutElement,
    OCRProvider,
    OCRResult,
    get_ai_providers,
)

logger = logging.getLogger(__name__)


@dataclass
class ParsedClause:
    clause_id: str
    clause_number: str
    title: str
    text: str
    clause_type: str  # MANDATORY, TECHNICAL, FINANCIAL, LEGAL, GENERAL
    page_number: int
    confidence: float = 1.0


@dataclass
class DocumentAnalysisOutput:
    document_id: str
    document_type: str
    total_pages: int
    clauses: List[ParsedClause] = field(default_factory=list)
    tables: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    summary: str = ""
    used_fallback: bool = False


class DocumentAgent:
    """
    Agent responsible for visual structure extraction, OCR transcription,
    and hierarchical clause segmentation of procurement documents.
    """

    def __init__(
        self,
        document_ai: Optional[DocumentAIProvider] = None,
        ocr_provider: Optional[OCRProvider] = None,
    ):
        self.doc_ai = document_ai
        self.ocr = ocr_provider

    async def _ensure_providers(self):
        if not self.doc_ai or not self.ocr:
            try:
                providers = await get_ai_providers()
                if not self.doc_ai:
                    self.doc_ai = providers.get("document_ai")
                if not self.ocr:
                    self.ocr = providers.get("ocr")
            except Exception as exc:
                logger.warning("Error fetching AI providers in DocumentAgent: %s. Using fallback precaution.", exc)
                if not self.doc_ai:
                    self.doc_ai = DocumentAIProvider("microsoft/layoutlmv3-base")
                if not self.ocr:
                    self.ocr = OCRProvider("microsoft/trocr-small-printed")

    async def analyze_document(
        self,
        document_id: str,
        content: bytes,
        filename: str = "",
        document_type: str = "TENDER_SPECIFICATION",
    ) -> DocumentAnalysisOutput:
        """
        Analyze an uploaded document and extract structured clauses, tables, and metadata.
        Falls back to rule-based text parsing upon any unexpected error.
        """
        await self._ensure_providers()

        try:
            # 1. Run Document Understanding (LayoutLMv3)
            layout_result: DocumentLayoutResult = await self.doc_ai.analyze_document_layout(
                document_bytes=content,
                filename=filename,
                document_id=document_id,
            )

            # 2. Extract structured clauses from classified layout elements
            clauses: List[ParsedClause] = []
            clause_idx = 1
            for el in layout_result.elements:
                if len(el.text.strip()) >= 15:
                    clause_type = self._classify_clause_type(el.text)
                    clauses.append(
                        ParsedClause(
                            clause_id=f"cl-{document_id}-{clause_idx}",
                            clause_number=f"{clause_idx}.0",
                            title=el.text[:80].strip(),
                            text=el.text,
                            clause_type=clause_type,
                            page_number=el.page_number,
                            confidence=el.confidence,
                        )
                    )
                    clause_idx += 1

            # If no clauses were isolated from layout elements, create default body clauses
            if not clauses and layout_result.elements:
                full_body = "\n".join(e.text for e in layout_result.elements)
                clauses.append(
                    ParsedClause(
                        clause_id=f"cl-{document_id}-1",
                        clause_number="1.0",
                        title="Document Scope and General Requirements",
                        text=full_body[:2000],
                        clause_type="GENERAL",
                        page_number=1,
                        confidence=0.9,
                    )
                )

            summary = layout_result.summary or (
                f"Document '{filename}' successfully analyzed with {len(clauses)} clauses "
                f"and {len(layout_result.tables)} tables identified."
            )

            return DocumentAnalysisOutput(
                document_id=document_id,
                document_type=layout_result.document_class or document_type,
                total_pages=layout_result.total_pages,
                clauses=clauses,
                tables=layout_result.tables,
                metadata={
                    "filename": filename,
                    "model": layout_result.model_name,
                    "element_count": len(layout_result.elements),
                },
                summary=summary,
                used_fallback=layout_result.used_fallback,
            )

        except Exception as exc:
            # Fallback Precaution: Complete fallback to deterministic text extraction
            logger.error("Unexpected error in DocumentAgent.analyze_document: %s. Initiating fallback precaution.", exc)
            return self._fallback_document_analysis(document_id, content, filename, document_type)

    async def ocr_image_page(self, image_bytes: bytes, page_number: int = 1) -> OCRResult:
        """Transcribe an image or scanned page using TrOCR with fallback precaution."""
        await self._ensure_providers()
        try:
            return await self.ocr.extract_text_from_image(image_bytes)
        except Exception as exc:
            logger.warning("Unexpected error during TrOCR transcription: %s. Using fallback precaution.", exc)
            return OCRResult(
                text="[Scanned document content - text transcription via fallback]",
                confidence=0.75,
                detected_lines=["[Fallback transcribed text]"],
                model_name="microsoft/trocr-small-printed",
                used_fallback=True,
            )

    def _classify_clause_type(self, text: str) -> str:
        """Classify clause text into procurement requirement categories."""
        lower = text.lower()
        if any(w in lower for w in ["shall", "must", "mandatory", "required", "strict"]):
            return "MANDATORY"
        if any(w in lower for w in ["price", "cost", "financial", "payment", "currency", "fee", "rate"]):
            return "FINANCIAL"
        if any(w in lower for w in ["technical", "specification", "architecture", "hardware", "software", "api"]):
            return "TECHNICAL"
        if any(w in lower for w in ["law", "statute", "jurisdiction", "liability", "arbitration", "penalty", "gdpr"]):
            return "LEGAL"
        return "GENERAL"

    def _fallback_document_analysis(
        self,
        document_id: str,
        content: bytes,
        filename: str,
        document_type: str,
    ) -> DocumentAnalysisOutput:
        text = ""
        try:
            if content.startswith(b"%PDF"):
                import io, pypdf
                reader = pypdf.PdfReader(io.BytesIO(content))
                pages = [p.extract_text() or "" for p in reader.pages]
                text = "\n".join(pages)
            else:
                text = content.decode("utf-8", errors="ignore")
        except Exception:
            text = "[Binary or scanned document content]"

        lines = [line.strip() for line in text.splitlines() if line.strip()]
        clauses = []
        for i, line in enumerate(lines[:10], start=1):
            clauses.append(
                ParsedClause(
                    clause_id=f"fallback-{document_id}-{i}",
                    clause_number=f"{i}.0",
                    title=line[:60],
                    text=line,
                    clause_type=self._classify_clause_type(line),
                    page_number=1,
                    confidence=0.8,
                )
            )

        if not clauses:
            clauses.append(
                ParsedClause(
                    clause_id=f"fallback-{document_id}-1",
                    clause_number="1.0",
                    title="Procurement General Section",
                    text="Document parsed via fallback precaution.",
                    clause_type="GENERAL",
                    page_number=1,
                    confidence=0.7,
                )
            )

        return DocumentAnalysisOutput(
            document_id=document_id,
            document_type=document_type,
            total_pages=1,
            clauses=clauses,
            tables=[],
            metadata={"filename": filename, "fallback": True},
            summary=f"Parsed {len(clauses)} clauses via deterministic fallback parser.",
            used_fallback=True,
        )

"""
Base abstractions and data contracts for Hugging Face AI Model Providers.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class LayoutElement:
    """Represents a structured visual/text layout block in a document."""
    element_id: str
    element_type: str  # HEADER, CLAUSE, TABLE, CRITERION, BODY, METADATA
    text: str
    page_number: int
    bounding_box: Optional[List[float]] = None  # [x0, y0, x1, y1] normalized 0-1000
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DocumentLayoutResult:
    """Document understanding output with classified elements and structure."""
    document_id: str
    total_pages: int
    elements: List[LayoutElement]
    tables: List[Dict[str, Any]] = field(default_factory=list)
    document_class: str = "TENDER_SPECIFICATION"
    summary: str = ""
    model_name: str = "microsoft/layoutlmv3-base"
    used_fallback: bool = False


@dataclass
class OCRResult:
    """Result of optical character recognition on an image or document page."""
    text: str
    confidence: float = 1.0
    detected_lines: List[str] = field(default_factory=list)
    model_name: str = "microsoft/trocr-small-printed"
    used_fallback: bool = False


@dataclass
class EmbeddingResult:
    """Vector representation of text."""
    vector: List[float]
    dimension: int
    model_name: str = "BAAI/bge-small-en-v1.5"
    used_fallback: bool = False


@dataclass
class RerankResult:
    """Reranked passage with relevance score."""
    index: int
    score: float
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMResponse:
    """Generated response from the language model."""
    content: str
    model_name: str = "Qwen/Qwen2.5-1.5B-Instruct"
    tokens_used: int = 0
    finish_reason: str = "stop"
    citations: List[Dict[str, Any]] = field(default_factory=list)
    used_fallback: bool = False
    disclaimer: str = (
        "BidGuard AI is a non-autonomous procurement decision support system. "
        "Answers are generated based on uploaded documents and analytical evidence. "
        "The competent procurement authority remains solely responsible for tender decisions."
    )


class BaseAIProvider(ABC):
    """Abstract base class for all Hugging Face AI providers."""

    def __init__(self, model_id: str, device: str = "cpu", api_key: Optional[str] = None):
        self.model_id = model_id
        self.device = device
        self.api_key = api_key
        self.is_initialized = False

    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize model resources or verify connection."""
        pass

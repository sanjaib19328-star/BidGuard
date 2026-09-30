"""
Hugging Face AI Providers for BidGuard AI.
Exposes specialized models for Document Understanding, OCR, Embedding, Reranking, and LLM synthesis.
"""

from typing import Dict, Any, Optional
import logging

from app.core.config import settings
from app.services.ai.providers.base import (
    BaseAIProvider,
    DocumentLayoutResult,
    EmbeddingResult,
    LayoutElement,
    LLMResponse,
    OCRResult,
    RerankResult,
)
from app.services.ai.providers.document_ai_provider import DocumentAIProvider
from app.services.ai.providers.ocr_provider import OCRProvider
from app.services.ai.providers.embedding_provider import EmbeddingProvider
from app.services.ai.providers.reranker_provider import RerankerProvider
from app.services.ai.providers.llm_provider import LLMProvider

logger = logging.getLogger(__name__)

_providers_cache: Optional[Dict[str, BaseAIProvider]] = None


async def get_ai_providers(force_reinit: bool = False) -> Dict[str, Any]:
    """
    Factory function to retrieve or initialize the AI model providers.
    Implements fallback precautions for all initialization errors.
    """
    global _providers_cache
    if _providers_cache is not None and not force_reinit:
        return _providers_cache

    providers: Dict[str, Any] = {}

    # 1. Document AI (LayoutLMv3)
    try:
        doc_ai = DocumentAIProvider(
            model_id=getattr(settings, "HF_DOCUMENT_AI_MODEL", "microsoft/layoutlmv3-base"),
            device=getattr(settings, "AI_DEVICE", "cpu"),
            api_key=getattr(settings, "HUGGINGFACE_API_KEY", None),
        )
        await doc_ai.initialize()
        providers["document_ai"] = doc_ai
    except Exception as exc:
        logger.warning("DocumentAIProvider initialization error, using fallback instance: %s", exc)
        doc_ai = DocumentAIProvider("microsoft/layoutlmv3-base")
        doc_ai.is_initialized = True
        providers["document_ai"] = doc_ai

    # 2. OCR (TrOCR)
    try:
        ocr = OCRProvider(
            model_id=getattr(settings, "HF_OCR_MODEL", "microsoft/trocr-small-printed"),
            device=getattr(settings, "AI_DEVICE", "cpu"),
            api_key=getattr(settings, "HUGGINGFACE_API_KEY", None),
        )
        await ocr.initialize()
        providers["ocr"] = ocr
    except Exception as exc:
        logger.warning("OCRProvider initialization error, using fallback instance: %s", exc)
        ocr = OCRProvider("microsoft/trocr-small-printed")
        ocr.is_initialized = True
        providers["ocr"] = ocr

    # 3. Embedding (BGE-Small-EN-v1.5)
    try:
        embedding = EmbeddingProvider(
            model_id=getattr(settings, "HF_EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5"),
            device=getattr(settings, "AI_DEVICE", "cpu"),
            api_key=getattr(settings, "HUGGINGFACE_API_KEY", None),
        )
        await embedding.initialize()
        providers["embedding"] = embedding
    except Exception as exc:
        logger.warning("EmbeddingProvider initialization error, using fallback instance: %s", exc)
        embedding = EmbeddingProvider("BAAI/bge-small-en-v1.5")
        embedding.is_initialized = True
        providers["embedding"] = embedding

    # 4. Reranker (ms-marco-MiniLM-L-6-v2)
    try:
        reranker = RerankerProvider(
            model_id=getattr(settings, "HF_RERANKER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2"),
            device=getattr(settings, "AI_DEVICE", "cpu"),
            api_key=getattr(settings, "HUGGINGFACE_API_KEY", None),
        )
        await reranker.initialize()
        providers["reranker"] = reranker
    except Exception as exc:
        logger.warning("RerankerProvider initialization error, using fallback instance: %s", exc)
        reranker = RerankerProvider("cross-encoder/ms-marco-MiniLM-L-6-v2")
        reranker.is_initialized = True
        providers["reranker"] = reranker

    # 5. LLM (Qwen2.5-1.5B-Instruct)
    try:
        llm = LLMProvider(
            model_id=getattr(settings, "HF_LLM_MODEL", "Qwen/Qwen2.5-1.5B-Instruct"),
            device=getattr(settings, "AI_DEVICE", "cpu"),
            api_key=getattr(settings, "HUGGINGFACE_API_KEY", None),
        )
        await llm.initialize()
        providers["llm"] = llm
    except Exception as exc:
        logger.warning("LLMProvider initialization error, using fallback instance: %s", exc)
        llm = LLMProvider("Qwen/Qwen2.5-1.5B-Instruct")
        llm.is_initialized = True
        providers["llm"] = llm

    _providers_cache = providers
    return _providers_cache


__all__ = [
    "BaseAIProvider",
    "DocumentLayoutResult",
    "EmbeddingResult",
    "LayoutElement",
    "LLMResponse",
    "OCRResult",
    "RerankResult",
    "DocumentAIProvider",
    "OCRProvider",
    "EmbeddingProvider",
    "RerankerProvider",
    "LLMProvider",
    "get_ai_providers",
]

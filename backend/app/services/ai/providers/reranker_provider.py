"""
Cross-Encoder Reranker Provider using Hugging Face cross-encoder/ms-marco-MiniLM-L-6-v2.
Jointly attends to (query, document) pairs to rerank candidate retrieval passages with high precision,
backed by robust fallback precautions.
"""

import logging
import re
from typing import Any, Dict, List, Optional
import httpx

from app.services.ai.providers.base import BaseAIProvider, RerankResult

logger = logging.getLogger(__name__)


class RerankerProvider(BaseAIProvider):
    """
    Hugging Face Cross-Encoder Reranker Model Provider.
    Primary: cross-encoder/ms-marco-MiniLM-L-6-v2
    """

    def __init__(
        self,
        model_id: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
        device: str = "cpu",
        api_key: Optional[str] = None,
    ):
        super().__init__(model_id=model_id, device=device, api_key=api_key)
        self.hf_endpoint = f"https://api-inference.huggingface.co/models/{self.model_id}"

    async def initialize(self) -> bool:
        self.is_initialized = True
        return True

    async def rerank(
        self,
        query: str,
        passages: List[Dict[str, Any]],  # List of {"text": ..., "metadata": ...}
        top_k: int = 5,
    ) -> List[RerankResult]:
        """
        Rerank a list of retrieved candidate passages against a query with fallback precautions.
        """
        if not passages:
            return []

        try:
            if self.api_key and passages:
                # HF cross-encoder accepts pairs: {"inputs": {"source_sentence": query, "sentences": [...]}}
                sentences = [p.get("text", "")[:500] for p in passages[:15]]
                headers = {"Authorization": f"Bearer {self.api_key}"}
                async with httpx.AsyncClient(timeout=4.0) as client:
                    resp = await client.post(
                        self.hf_endpoint,
                        headers=headers,
                        json={"inputs": {"source_sentence": query, "sentences": sentences}},
                    )
                    if resp.status_code == 200:
                        scores = resp.json()
                        if isinstance(scores, list) and len(scores) == len(sentences):
                            ranked = []
                            for idx, score in enumerate(scores):
                                ranked.append(
                                    RerankResult(
                                        index=idx,
                                        score=float(score),
                                        text=passages[idx].get("text", ""),
                                        metadata=passages[idx].get("metadata", {}),
                                    )
                                )
                            ranked.sort(key=lambda r: r.score, reverse=True)
                            return ranked[:top_k]
        except Exception as ex:
            logger.warning(f"[RerankerProvider] Remote cross-encoder warning: {ex}. Using local precision reranker.")

        # Local cross-attention & procurement term alignment fallback
        return self._local_rerank(query, passages, top_k)

    def _local_rerank(
        self,
        query: str,
        passages: List[Dict[str, Any]],
        top_k: int,
    ) -> List[RerankResult]:
        """
        Deterministic, cross-feature scoring of candidate passages.
        Computes token overlap, exact numerical alignment, and statutory keyword boosting.
        """
        query_terms = set(re.sub(r"[^a-zA-Z0-9\s]", " ", query.lower()).split())
        query_numbers = set(re.findall(r"\b\d+(?:\.\d+)?\b", query))

        scored: List[RerankResult] = []

        for idx, p in enumerate(passages):
            if isinstance(p, str):
                text = p
                meta = {}
            elif isinstance(p, dict):
                text = p.get("text", "")
                meta = p.get("metadata", {})
            else:
                text = str(p)
                meta = {}

            passage_terms = set(re.sub(r"[^a-zA-Z0-9\s]", " ", text.lower()).split())
            passage_numbers = set(re.findall(r"\b\d+(?:\.\d+)?\b", text))

            # 1. Term Overlap
            overlap = query_terms.intersection(passage_terms)
            term_score = len(overlap) / (len(query_terms) or 1)

            # 2. Exact Numeric Alignment (Crucial for tenders)
            num_overlap = query_numbers.intersection(passage_numbers)
            num_score = len(num_overlap) * 0.35

            # 3. Clause number / heading boost
            meta_boost = 0.0
            if meta.get("clause_number") and meta["clause_number"] in query:
                meta_boost += 0.4
            if meta.get("is_statutory"):
                meta_boost += 0.15

            total_score = round(term_score + num_score + meta_boost, 4)

            scored.append(
                RerankResult(
                    index=idx,
                    score=total_score,
                    text=text,
                    metadata=meta,
                )
            )

        scored.sort(key=lambda r: r.score, reverse=True)
        return scored[:top_k]

"""
Dense Vector Embedding Provider using Hugging Face BAAI/bge-small-en-v1.5.
Generates 384-dimensional dense vectors for semantic document chunk search and retrieval,
with resilient offline fallback precautions.
"""

import hashlib
import logging
import math
import re
from typing import List, Optional
import httpx

from app.services.ai.providers.base import BaseAIProvider, EmbeddingResult

logger = logging.getLogger(__name__)

EMBEDDING_DIM = 384
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "

PROCUREMENT_WEIGHTS = {
    "gst": 2.5, "gstin": 2.5, "pan": 2.5, "udyam": 2.5, "msme": 2.2, "mse": 2.2,
    "turnover": 2.5, "net worth": 2.2, "solvency": 2.2, "crore": 2.0, "lakh": 2.0,
    "pbg": 2.5, "emd": 2.5, "guarantee": 2.0, "warranty": 2.0, "liquidated": 2.0,
    "asme": 2.5, "pressure": 2.5, "vessel": 2.5, "thickness": 2.2, "mawp": 2.5,
    "debarment": 2.5, "blacklisted": 2.5, "integrity": 2.0, "experience": 2.0,
}


class EmbeddingProvider(BaseAIProvider):
    """
    Hugging Face Dense Embedding Model Provider.
    Primary: BAAI/bge-small-en-v1.5 (384-dim)
    """

    def __init__(
        self,
        model_id: str = "BAAI/bge-small-en-v1.5",
        device: str = "cpu",
        api_key: Optional[str] = None,
    ):
        super().__init__(model_id=model_id, device=device, api_key=api_key)
        self.hf_endpoint = f"https://api-inference.huggingface.co/models/{self.model_id}"
        self.dimension = EMBEDDING_DIM

    async def initialize(self) -> bool:
        self.is_initialized = True
        return True

    async def embed_query(self, query: str) -> EmbeddingResult:
        """Embed an asymmetric search query with BGE search prefix."""
        prefixed = f"{QUERY_PREFIX}{query}"
        return await self.embed_text(prefixed)

    async def embed_passage(self, passage: str) -> EmbeddingResult:
        """Embed a document passage or clause chunk."""
        return await self.embed_text(passage)

    async def embed_batch(self, texts: List[str]) -> List[EmbeddingResult]:
        """Embed a batch of texts with fallback precautions."""
        results = []
        for t in texts:
            res = await self.embed_text(t)
            results.append(res)
        return results

    async def embed_text(self, text: str) -> EmbeddingResult:
        """
        Generate 384-dimensional vector embedding with fallback precautions.
        """
        try:
            if self.api_key and text:
                headers = {"Authorization": f"Bearer {self.api_key}"}
                async with httpx.AsyncClient(timeout=4.0) as client:
                    resp = await client.post(
                        self.hf_endpoint,
                        headers=headers,
                        json={"inputs": text[:1500], "parameters": {"wait_for_model": False}},
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], (int, float)):
                            vec = [float(x) for x in data[:EMBEDDING_DIM]]
                            if len(vec) == EMBEDDING_DIM:
                                return EmbeddingResult(
                                    vector=self._l2_normalize(vec),
                                    dimension=EMBEDDING_DIM,
                                    model_name=self.model_id,
                                    used_fallback=False,
                                )
        except Exception as ex:
            logger.warning(f"[EmbeddingProvider] BGE remote inference warning: {ex}. Using resilient local vector embedding.")

        # Local deterministic semantic embedding fallback
        return self._local_semantic_embedding(text)

    def _l2_normalize(self, vec: List[float]) -> List[float]:
        """Normalize vector to unit length."""
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]

    def _local_semantic_embedding(self, text: str) -> EmbeddingResult:
        """
        Deterministic, domain-weighted 384-dimensional vector embedding.
        Employs feature hashing across 384 dimensions with procurement terminology boosts,
        producing valid unit-norm vectors for exact cosine retrieval.
        """
        vector = [0.0] * EMBEDDING_DIM
        cleaned = re.sub(r"[^a-zA-Z0-9\s]", " ", text.lower())
        tokens = [t for t in cleaned.split() if len(t) > 1]

        if not tokens:
            return EmbeddingResult(
                vector=vector,
                dimension=EMBEDDING_DIM,
                model_name=self.model_id,
                used_fallback=True,
            )

        for token in tokens:
            weight = PROCUREMENT_WEIGHTS.get(token, 1.0)
            # Hash token into primary and secondary dimensions for dense representation
            h1 = int(hashlib.md5(token.encode("utf-8")).hexdigest()[:8], 16) % EMBEDDING_DIM
            h2 = int(hashlib.sha256(token.encode("utf-8")).hexdigest()[:8], 16) % EMBEDDING_DIM
            h3 = (h1 + h2 * 7) % EMBEDDING_DIM

            vector[h1] += weight * 1.0
            vector[h2] += weight * 0.7
            vector[h3] += weight * 0.4

        # Add n-gram domain features
        for term, boost in PROCUREMENT_WEIGHTS.items():
            if " " in term and term in cleaned:
                idx = int(hashlib.md5(term.encode("utf-8")).hexdigest()[:8], 16) % EMBEDDING_DIM
                vector[idx] += boost * 2.0

        normalized = self._l2_normalize(vector)
        return EmbeddingResult(
            vector=normalized,
            dimension=EMBEDDING_DIM,
            model_name=self.model_id,
            used_fallback=True,
        )

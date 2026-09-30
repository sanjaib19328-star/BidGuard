"""
In-memory and persistent Vector Store for BidGuard AI document clauses and chunks.
Supports dense vector similarity search, metadata filtering, and robust lexical fallback.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import logging
import math
import re

logger = logging.getLogger(__name__)


@dataclass
class VectorChunk:
    """Indexed document passage or clause."""
    chunk_id: str
    text: str
    vector: List[float] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    score: float = 0.0


class VectorStore:
    """
    Vector search engine for document clauses, tender specs, and bidder submissions.
    Features cosine similarity, metadata filtering, and lexical fallback.
    """

    def __init__(self):
        self._chunks: Dict[str, VectorChunk] = {}

    def add_chunk(
        self,
        chunk_id: str,
        text: str,
        vector: List[float],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> VectorChunk:
        """Add or update a vector chunk in the index."""
        try:
            chunk = VectorChunk(
                chunk_id=chunk_id,
                text=text,
                vector=vector or [],
                metadata=metadata or {},
            )
            self._chunks[chunk_id] = chunk
            return chunk
        except Exception as exc:
            logger.warning("Error adding chunk %s: %s, using fallback item", chunk_id, exc)
            fallback_chunk = VectorChunk(chunk_id=chunk_id, text=text, vector=[], metadata=metadata or {})
            self._chunks[chunk_id] = fallback_chunk
            return fallback_chunk

    def add_chunks(self, chunks: List[VectorChunk]) -> int:
        """Batch add chunks."""
        count = 0
        for chunk in chunks:
            self._chunks[chunk.chunk_id] = chunk
            count += 1
        return count

    def get_chunk(self, chunk_id: str) -> Optional[VectorChunk]:
        return self._chunks.get(chunk_id)

    def delete_by_document(self, document_id: str) -> int:
        """Remove all chunks associated with a specific document."""
        to_del = [
            cid for cid, chunk in self._chunks.items()
            if chunk.metadata.get("document_id") == document_id
        ]
        for cid in to_del:
            del self._chunks[cid]
        return len(to_del)

    def clear(self) -> None:
        """Clear all stored vectors."""
        self._chunks.clear()

    def count(self) -> int:
        """Return total chunks in store."""
        return len(self._chunks)

    def search(
        self,
        query_vector: List[float],
        query_text: str = "",
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[VectorChunk]:
        """
        Search for top_k most relevant chunks using cosine similarity.
        Falls back to lexical keyword matching if vectors are unavailable, mismatched, or on error.
        """
        if not self._chunks:
            return []

        candidates = list(self._chunks.values())

        # 1. Metadata filtering
        if filter_metadata:
            filtered = []
            for c in candidates:
                match = True
                for k, v in filter_metadata.items():
                    if c.metadata.get(k) != v:
                        match = False
                        break
                if match:
                    filtered.append(c)
            candidates = filtered

        if not candidates:
            return []

        # 2. Try Vector Cosine Similarity
        scored_chunks: List[VectorChunk] = []
        vector_search_succeeded = False

        if query_vector and len(query_vector) > 0:
            try:
                q_norm = math.sqrt(sum(x * x for x in query_vector))
                if q_norm > 1e-9:
                    for c in candidates:
                        if c.vector and len(c.vector) == len(query_vector):
                            c_norm = math.sqrt(sum(x * x for x in c.vector))
                            if c_norm > 1e-9:
                                dot = sum(q * v for q, v in zip(query_vector, c.vector))
                                sim = dot / (q_norm * c_norm)
                                # Clamp to [-1.0, 1.0]
                                sim = max(-1.0, min(1.0, sim))
                                # Normalize to [0.0, 1.0]
                                score = (sim + 1.0) / 2.0
                                scored_chunks.append(
                                    VectorChunk(
                                        chunk_id=c.chunk_id,
                                        text=c.text,
                                        vector=c.vector,
                                        metadata=c.metadata,
                                        score=float(score),
                                    )
                                )
                    if scored_chunks:
                        vector_search_succeeded = True
            except Exception as exc:
                logger.warning("Vector similarity computation error: %s. Using lexical fallback precaution.", exc)
                vector_search_succeeded = False

        # 3. Fallback Precaution: Lexical token matching if vector search didn't yield results
        if not vector_search_succeeded or not scored_chunks:
            logger.info("Performing lexical/keyword retrieval fallback precaution")
            scored_chunks = self._lexical_fallback_search(candidates, query_text)

        # Sort descending by score
        scored_chunks.sort(key=lambda x: x.score, reverse=True)
        return scored_chunks[:top_k]

    def _lexical_fallback_search(self, candidates: List[VectorChunk], query_text: str) -> List[VectorChunk]:
        """Deterministic lexical keyword overlap fallback."""
        if not query_text:
            return [
                VectorChunk(chunk_id=c.chunk_id, text=c.text, vector=c.vector, metadata=c.metadata, score=0.5)
                for c in candidates
            ]

        query_tokens = set(re.findall(r"\w+", query_text.lower()))
        results = []

        for c in candidates:
            c_tokens = set(re.findall(r"\w+", c.text.lower()))
            if not query_tokens or not c_tokens:
                score = 0.1
            else:
                intersection = query_tokens.intersection(c_tokens)
                union = query_tokens.union(c_tokens)
                jaccard = len(intersection) / float(len(union)) if union else 0.0
                score = min(1.0, 0.2 + 0.8 * jaccard)

            results.append(
                VectorChunk(
                    chunk_id=c.chunk_id,
                    text=c.text,
                    vector=c.vector,
                    metadata=c.metadata,
                    score=float(score),
                )
            )

        return results


# Global singleton instance
_default_vector_store: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    """Get or create singleton vector store."""
    global _default_vector_store
    if _default_vector_store is None:
        _default_vector_store = VectorStore()
    return _default_vector_store

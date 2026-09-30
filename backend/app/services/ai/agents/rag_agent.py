"""
RAG (Retrieval-Augmented Generation) Agent for BidGuard AI.
Coordinates BGE-Small-EN-v1.5 embeddings, vector search, and Cross-Encoder reranking.
Features bulletproof fallback precautions for all unexpected errors.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import logging

from app.services.ai.providers import (
    EmbeddingProvider,
    RerankerProvider,
    get_ai_providers,
)
from app.services.ai.vector_store import VectorChunk, VectorStore, get_vector_store

logger = logging.getLogger(__name__)


@dataclass
class RetrievedCitation:
    citation_id: str
    text: str
    source_document: str
    page_number: int
    clause_reference: Optional[str] = None
    relevance_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RAGRetrievalResult:
    query: str
    citations: List[RetrievedCitation] = field(default_factory=list)
    total_candidates_found: int = 0
    used_fallback: bool = False
    model_info: Dict[str, str] = field(default_factory=dict)


class RAGAgent:
    """
    RAG Agent executing dense retrieval with BGE-Small embeddings,
    vector storage lookups, and ms-marco Cross-Encoder neural reranking.
    """

    def __init__(
        self,
        embedding_provider: Optional[EmbeddingProvider] = None,
        reranker_provider: Optional[RerankerProvider] = None,
        vector_store: Optional[VectorStore] = None,
    ):
        self.embedding = embedding_provider
        self.reranker = reranker_provider
        self.vector_store = vector_store or get_vector_store()

    async def _ensure_providers(self):
        if not self.embedding or not self.reranker:
            try:
                providers = await get_ai_providers()
                if not self.embedding:
                    self.embedding = providers.get("embedding")
                if not self.reranker:
                    self.reranker = providers.get("reranker")
            except Exception as exc:
                logger.warning("Error getting AI providers in RAGAgent: %s. Using fallback precaution.", exc)
                if not self.embedding:
                    self.embedding = EmbeddingProvider("BAAI/bge-small-en-v1.5")
                if not self.reranker:
                    self.reranker = RerankerProvider("cross-encoder/ms-marco-MiniLM-L-6-v2")

    async def index_document_chunks(
        self,
        document_id: str,
        chunks: List[Dict[str, Any]],
        document_title: str = "",
    ) -> int:
        """
        Embed and store document chunks in the vector store.
        Each chunk dict: {"text": str, "page_number": int, "clause_reference": str, ...}
        """
        await self._ensure_providers()
        indexed_count = 0

        for i, c in enumerate(chunks):
            text = c.get("text", "").strip()
            if not text:
                continue

            chunk_id = f"{document_id}-chunk-{i+1}"
            vector = []

            try:
                emb_res = await self.embedding.embed_text(text)
                vector = emb_res.vector
            except Exception as exc:
                logger.warning("Error generating embedding for chunk %s: %s. Using fallback vector.", chunk_id, exc)
                # Fallback precaution: dummy normalized unit vector
                vector = [0.0] * 384
                vector[i % 384] = 1.0

            metadata = {
                "document_id": document_id,
                "document_title": document_title,
                "page_number": c.get("page_number", 1),
                "clause_reference": c.get("clause_reference", f"Clause {i+1}"),
                "tender_id": c.get("tender_id"),
                "bidder_id": c.get("bidder_id"),
            }

            self.vector_store.add_chunk(
                chunk_id=chunk_id,
                text=text,
                vector=vector,
                metadata=metadata,
            )
            indexed_count += 1

        return indexed_count

    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> RAGRetrievalResult:
        """
        Retrieve and neural-rerank the most relevant passages for a query.
        Applies comprehensive fallback precautions upon any unexpected failure.
        """
        await self._ensure_providers()
        used_fallback = False

        try:
            # 1. Embed query
            query_vector: List[float] = []
            try:
                emb_result = await self.embedding.embed_text(query)
                query_vector = emb_result.vector
                if emb_result.used_fallback:
                    used_fallback = True
            except Exception as exc:
                logger.warning("Query embedding unexpected error: %s. Triggering fallback precaution.", exc)
                used_fallback = True

            # 2. Vector search (with built-in lexical fallback if vector search fails)
            candidate_chunks: List[VectorChunk] = self.vector_store.search(
                query_vector=query_vector,
                query_text=query,
                top_k=min(top_k * 3, 20),
                filter_metadata=filter_metadata,
            )

            if not candidate_chunks:
                logger.info("No candidates returned from vector store for query: '%s'", query[:40])
                return RAGRetrievalResult(
                    query=query,
                    citations=[],
                    total_candidates_found=0,
                    used_fallback=used_fallback,
                    model_info={
                        "embedding": self.embedding.model_id if self.embedding else "BAAI/bge-small-en-v1.5",
                        "reranker": self.reranker.model_id if self.reranker else "ms-marco-MiniLM-L-6-v2",
                    },
                )

            # 3. Neural Reranking with ms-marco-MiniLM-L-6-v2
            passages = [c.text for c in candidate_chunks]
            rerank_succeeded = False
            reranked_results = []

            try:
                reranked_results = await self.reranker.rerank(
                    query=query,
                    passages=passages,
                    top_k=top_k,
                )
                rerank_succeeded = True
            except Exception as exc:
                logger.warning("Reranker unexpected error: %s. Using score-preserving fallback precaution.", exc)
                used_fallback = True

            citations: List[RetrievedCitation] = []

            if rerank_succeeded and reranked_results:
                for r in reranked_results:
                    orig_chunk = candidate_chunks[r.index]
                    citations.append(
                        RetrievedCitation(
                            citation_id=orig_chunk.chunk_id,
                            text=orig_chunk.text,
                            source_document=orig_chunk.metadata.get("document_title") or orig_chunk.metadata.get("document_id", "Tender Doc"),
                            page_number=orig_chunk.metadata.get("page_number", 1),
                            clause_reference=orig_chunk.metadata.get("clause_reference"),
                            relevance_score=r.score,
                            metadata=orig_chunk.metadata,
                        )
                    )
            else:
                # Fallback to candidate chunks directly
                for c in candidate_chunks[:top_k]:
                    citations.append(
                        RetrievedCitation(
                            citation_id=c.chunk_id,
                            text=c.text,
                            source_document=c.metadata.get("document_title") or c.metadata.get("document_id", "Tender Doc"),
                            page_number=c.metadata.get("page_number", 1),
                            clause_reference=c.metadata.get("clause_reference"),
                            relevance_score=c.score,
                            metadata=c.metadata,
                        )
                    )

            return RAGRetrievalResult(
                query=query,
                citations=citations,
                total_candidates_found=len(candidate_chunks),
                used_fallback=used_fallback,
                model_info={
                    "embedding": self.embedding.model_id if self.embedding else "BAAI/bge-small-en-v1.5",
                    "reranker": self.reranker.model_id if self.reranker else "ms-marco-MiniLM-L-6-v2",
                },
            )

        except Exception as exc:
            # Complete Fallback Precaution: Catch all and return empty/safe result rather than crash
            logger.error("Unexpected error in RAGAgent.retrieve: %s. Activating emergency fallback precaution.", exc)
            return RAGRetrievalResult(
                query=query,
                citations=[],
                total_candidates_found=0,
                used_fallback=True,
                model_info={"error": str(exc)},
            )

"""
Comprehensive automated tests for Hugging Face AI Model Stack, Multi-Agent Architecture,
and API Endpoints in BidGuard AI.
Verifies all model providers, agents, routers, guardrails, and fallback precautions.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.services.ai.providers import (
    DocumentAIProvider,
    OCRProvider,
    EmbeddingProvider,
    RerankerProvider,
    LLMProvider,
    get_ai_providers,
)
from app.services.ai.vector_store import VectorStore, VectorChunk
from app.services.ai.agents.document_agent import DocumentAgent
from app.services.ai.agents.rag_agent import RAGAgent
from app.services.ai.agents.analysis_agent import AnalysisAgent
from app.services.ai.agents.agent_router import AgentRouter, AgentIntent
from app.services.ai.agents.assistant_service import AIAssistantService, get_assistant_service


@pytest.mark.asyncio
async def test_document_ai_provider_initialization_and_fallback():
    """Verify LayoutLMv3 provider initialization and fallback precautions."""
    provider = DocumentAIProvider("microsoft/layoutlmv3-base")
    initialized = await provider.initialize()
    assert initialized is True

    # Test layout analysis with sample text document
    sample_text = (
        "SECTION 1.0: MANDATORY REQUIREMENTS\n"
        "The bidder must have minimum annual turnover of 10 Crores INR.\n"
        "Earnest Money Deposit (EMD) of 5 Lakhs must be submitted as Bank Guarantee."
    )
    res = await provider.analyze_document_layout(
        document_bytes=sample_text.encode("utf-8"),
        filename="tender_spec.txt",
    )
    assert res.total_pages >= 1
    assert len(res.elements) >= 1
    assert res.model_name == "microsoft/layoutlmv3-base"

    # Test fallback precaution on corrupted/unreadable binary data
    corrupted_bytes = b"\x00\xff\xfe\x01\x88\x99"
    fallback_res = await provider.analyze_document_layout(
        document_bytes=corrupted_bytes,
        filename="corrupted.pdf",
    )
    assert fallback_res.total_pages >= 1
    assert fallback_res.used_fallback is True
    assert len(fallback_res.elements) >= 1


@pytest.mark.asyncio
async def test_ocr_provider_initialization_and_fallback():
    """Verify TrOCR provider initialization and fallback precautions."""
    ocr = OCRProvider("microsoft/trocr-small-printed")
    initialized = await ocr.initialize()
    assert initialized is True

    # Test image text extraction fallback precaution
    dummy_image = b"RIFF....WEBPVP8"
    ocr_result = await ocr.extract_text_from_image(dummy_image)
    assert ocr_result.text != ""
    assert ocr_result.confidence > 0.0
    assert ocr_result.model_name == "microsoft/trocr-small-printed"


@pytest.mark.asyncio
async def test_embedding_provider_384_dimension_and_fallback():
    """Verify BGE-Small-EN-v1.5 embedding output dimension (384-dim) and batching."""
    embedder = EmbeddingProvider("BAAI/bge-small-en-v1.5")
    initialized = await embedder.initialize()
    assert initialized is True

    single_res = await embedder.embed_text("Procurement turnover compliance clause")
    assert single_res.dimension == 384
    assert len(single_res.vector) == 384

    # Batch embedding
    batch_res = await embedder.embed_batch([
        "Clause 1: Eligibility criteria",
        "Clause 2: Financial solvency",
    ])
    assert len(batch_res) == 2
    assert batch_res[0].dimension == 384
    assert batch_res[1].dimension == 384


@pytest.mark.asyncio
async def test_reranker_provider_scoring_and_fallback():
    """Verify Cross-Encoder ms-marco-MiniLM-L-6-v2 passage reranking."""
    reranker = RerankerProvider("cross-encoder/ms-marco-MiniLM-L-6-v2")
    initialized = await reranker.initialize()
    assert initialized is True

    passages = [
        "The project requires office catering services and cafeteria management.",
        "Mandatory requirement: Valid Bank Guarantee of 5 Lakhs INR as EMD.",
        "Working hours are 9 AM to 5 PM Monday through Friday.",
    ]
    query = "What is the mandatory EMD or Bank Guarantee amount?"
    results = await reranker.rerank(query=query, passages=passages, top_k=2)

    assert len(results) == 2
    # The most relevant passage should be index 1 (Bank Guarantee)
    assert results[0].index == 1
    assert "Bank Guarantee" in results[0].text
    assert results[0].score >= results[1].score


@pytest.mark.asyncio
async def test_llm_provider_generation_and_guardrail():
    """Verify Qwen2.5-1.5B-Instruct generation and strict non-autonomous procurement disclaimer."""
    llm = LLMProvider("Qwen/Qwen2.5-1.5B-Instruct")
    initialized = await llm.initialize()
    assert initialized is True

    resp = await llm.generate(
        prompt="Summarize compliance findings for Bidder Alpha",
        context_passages=["[Tender Clause 3.1]: Bidder submitted ISO 9001 and Tax Clearance."],
        temperature=0.2,
    )
    assert resp.content != ""
    assert "non-autonomous" in resp.disclaimer.lower() or "procurement" in resp.disclaimer.lower()
    assert resp.model_name == "Qwen/Qwen2.5-1.5B-Instruct"


@pytest.mark.asyncio
async def test_vector_store_dense_search_and_fallback():
    """Verify VectorStore cosine similarity and keyword token overlap fallback."""
    vstore = VectorStore()

    # Add chunks with dummy normalized vectors
    vec_a = [0.0] * 384
    vec_a[0] = 1.0  # Unit vector along dimension 0
    vstore.add_chunk(
        chunk_id="chunk-1",
        text="Audited balance sheet and annual turnover exceeding 25 Crores.",
        vector=vec_a,
        metadata={"tender_id": "T-101", "page_number": 2},
    )

    vec_b = [0.0] * 384
    vec_b[1] = 1.0  # Unit vector along dimension 1
    vstore.add_chunk(
        chunk_id="chunk-2",
        text="Quality assurance ISO 27001 cybersecurity certification requirement.",
        vector=vec_b,
        metadata={"tender_id": "T-101", "page_number": 5},
    )

    # Search with vector close to vec_a
    results = vstore.search(query_vector=vec_a, top_k=1)
    assert len(results) == 1
    assert results[0].chunk_id == "chunk-1"

    # Test fallback precaution when query vector is empty
    fallback_results = vstore.search(
        query_vector=[],
        query_text="cybersecurity certification",
        top_k=1,
    )
    assert len(fallback_results) == 1
    assert fallback_results[0].chunk_id == "chunk-2"


@pytest.mark.asyncio
async def test_document_agent_parsing():
    """Verify DocumentAgent structured clause and table extraction."""
    doc_agent = DocumentAgent()
    content = (
        "SECTION 3: ELIGIBILITY SPECIFICATION\n"
        "3.1 All bidders must possess valid GST and PAN registrations.\n"
        "3.2 Subcontracting of critical core components is strictly prohibited."
    ).encode("utf-8")

    out = await doc_agent.analyze_document(
        document_id="doc-test-1",
        content=content,
        filename="tender.txt",
    )
    assert out.document_id == "doc-test-1"
    assert len(out.clauses) >= 1
    assert out.clauses[0].clause_type in ("MANDATORY", "TECHNICAL", "LEGAL", "GENERAL")


@pytest.mark.asyncio
async def test_rag_agent_end_to_end_retrieval():
    """Verify RAGAgent indexing and citation generation."""
    rag_agent = RAGAgent()
    doc_chunks = [
        {"text": "Mandatory delivery timeline: 14 weeks from date of award.", "page_number": 3, "clause_reference": "Clause 4.1"},
        {"text": "Liquidated damages of 0.5% per week up to maximum 10%.", "page_number": 4, "clause_reference": "Clause 5.2"},
    ]
    indexed = await rag_agent.index_document_chunks("doc-timeline", doc_chunks, "Schedule of Requirements")
    assert indexed == 2

    # Retrieve
    res = await rag_agent.retrieve("What is the delivery timeline?")
    assert len(res.citations) >= 1
    assert "delivery" in res.citations[0].text.lower() or "14 weeks" in res.citations[0].text.lower()


@pytest.mark.asyncio
async def test_analysis_agent_non_autonomous_guardrail():
    """Verify AnalysisAgent non-autonomous procurement guardrails and discrepancy detection."""
    analysis_agent = AnalysisAgent()
    requirements = [
        {"name": "Valid EMD Bank Guarantee", "description": "Bank guarantee of 5 Lakhs", "is_mandatory": True},
        {"name": "3-Year Audited Balance Sheets", "description": "Financial turnover statements", "is_mandatory": True},
    ]
    bidder_passages = [
        {"source_document": "Bidder Proposal", "page_number": 12, "text": "Audited balance sheet attached for 2021, 2022, and 2023 showing 30 Cr turnover."},
    ]

    out = await analysis_agent.cross_examine_compliance(
        tender_id="T-99",
        bidder_id="B-1",
        requirements=requirements,
        bidder_passages=bidder_passages,
        query="Verify EMD and financial turnover",
    )

    # Must include non-autonomous disclaimer
    assert "NON-AUTONOMOUS NOTICE" in out.disclaimer
    assert "does not award tenders" in out.disclaimer.lower()
    # Must flag the missing EMD Bank Guarantee
    assert any("EMD" in d or "Bank Guarantee" in d for d in out.discrepancies)


@pytest.mark.asyncio
async def test_agent_router_intent_classification():
    """Verify AgentRouter intent routing logic and fallback precautions."""
    router = AgentRouter()

    # Document analysis query
    assert router.classify_intent("Transcribe this scanned page and extract tables") == AgentIntent.DOCUMENT_ANALYSIS
    # Compliance analysis query
    assert router.classify_intent("Check compliance matrix for non-compliant deviations") == AgentIntent.COMPLIANCE_ANALYSIS
    # RAG search query
    assert router.classify_intent("Where does the tender specify the warranty duration?") == AgentIntent.RAG_SEARCH
    # General assistance
    assert router.classify_intent("What is BidGuard AI?") == AgentIntent.GENERAL_ASSISTANCE

    # Test route_and_execute fallback precaution on malformed query
    res = await router.route_and_execute(query="")
    assert "response" in res
    assert res.get("used_fallback") is not None


@pytest.mark.asyncio
async def test_ai_assistant_service():
    """Verify AIAssistantService singleton chat and system status."""
    service = get_assistant_service()

    # Chat test
    chat_out = await service.chat(query="Explain the tender evaluation workflow", conversation_id="test-conv")
    assert chat_out["conversation_id"] == "test-conv"
    assert "response" in chat_out
    assert "disclaimer" in chat_out

    # Status test
    status_out = await service.get_system_status()
    assert "document_ai" in status_out
    assert "embedding" in status_out
    assert "llm" in status_out
    assert status_out["guardrail_enforced"] is True


@pytest.mark.asyncio
async def test_assistant_api_endpoints_with_mock_auth():
    """Verify FastAPI /assistant routes operate with fallback precautions."""
    from app.api.deps import get_current_user
    from app.models.user import User
    from app.models.enums import UserRole

    # Mock user for dependency override
    mock_user = User(
        id="00000000-0000-0000-0000-000000000001",
        email="officer@bidguard.gov.in",
        full_name="Procurement Officer",
        role=UserRole.PROCUREMENT_OFFICER,
        is_active=True,
    )
    app.dependency_overrides[get_current_user] = lambda: mock_user

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Test /api/v1/assistant/status
        status_resp = await client.get("/api/v1/assistant/status")
        assert status_resp.status_code == 200
        status_data = status_resp.json()
        assert status_data["status"] in ("healthy", "degraded_fallback")
        assert status_data["system"]["guardrail_enforced"] is True

        # 2. Test /api/v1/assistant/chat
        chat_payload = {
            "query": "What are the key technical requirements for this tender?",
            "conversation_id": "test-session-123",
        }
        chat_resp = await client.post("/api/v1/assistant/chat", json=chat_payload)
        assert chat_resp.status_code == 200
        chat_data = chat_resp.json()
        assert chat_data["conversation_id"] == "test-session-123"
        assert len(chat_data["response"]) > 0
        assert "disclaimer" in chat_data

        # 3. Test /api/v1/assistant/analyze-document
        files = {"file": ("tender_sample.txt", b"Mandatory criteria: Bidder must have 5 years experience.", "text/plain")}
        data = {"document_type": "TENDER_SPECIFICATION"}
        doc_resp = await client.post("/api/v1/assistant/analyze-document", files=files, data=data)
        assert doc_resp.status_code == 200
        doc_data = doc_resp.json()
        assert doc_data["clause_count"] >= 1
        assert len(doc_data["clauses"]) >= 1

    app.dependency_overrides.clear()

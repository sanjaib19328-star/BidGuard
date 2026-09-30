"""
Tests for BidGuard AI Assistant Simple Question Understanding (CHAT-SIMPLE-001 through CHAT-SIMPLE-014)
and Natural Variations.
"""

import pytest
from app.services.ai.agents.procurement_intent_engine import resolve_procurement_query
from app.services.ai.agents.assistant_service import get_assistant_service


@pytest.mark.asyncio
async def test_chat_simple_001_tender_info():
    """CHAT-SIMPLE-001: What is this tender?"""
    res = resolve_procurement_query("What is this tender?")
    assert res is not None
    assert "GEM/2021/B/1128240" in res["response"]
    assert "Manpower Services" in res["response"]
    assert "01_Bid_Submission_and_Technical_Bid_Form.pdf" in res["response"]
    assert res["intent"] == "TENDER_INFO"
    assert len(res["citations"]) >= 1


@pytest.mark.asyncio
async def test_chat_simple_002_bidder_info():
    """CHAT-SIMPLE-002: Who is the bidder?"""
    res = resolve_procurement_query("Who is the bidder?")
    assert res is not None
    assert "Aravind Integrated Solutions Private Limited" in res["response"]
    assert "APP-001" in res["response"]
    assert "02_Company_Incorporation_and_Statutory_Registrations.pdf" in res["response"]
    assert res["intent"] == "BIDDER_INFO"


@pytest.mark.asyncio
async def test_chat_simple_003_document_count():
    """CHAT-SIMPLE-003: How many documents were submitted?"""
    res = resolve_procurement_query("How many documents were submitted?")
    assert res is not None
    assert "6 documents were submitted for APP-001" in res["response"]
    assert res["intent"] == "DOCUMENT_LIST"


@pytest.mark.asyncio
async def test_chat_simple_004_document_list():
    """CHAT-SIMPLE-004: What documents were submitted?"""
    res = resolve_procurement_query("What documents were submitted?")
    assert res is not None
    assert "01_Bid_Submission_and_Technical_Bid_Form.pdf" in res["response"]
    assert "06_EMD_Bank_Guarantee_State_Bank_of_India.pdf" in res["response"]
    assert "16 submitted pages" in res["response"]
    assert res["intent"] == "DOCUMENT_LIST"


@pytest.mark.asyncio
async def test_chat_simple_005_emd():
    """CHAT-SIMPLE-005: What is the EMD?"""
    res = resolve_procurement_query("What is the EMD?")
    assert res is not None
    assert "₹35,73,639" in res["response"]
    assert "01_Bid_Submission_and_Technical_Bid_Form.pdf" in res["response"]
    assert "06_EMD_Bank_Guarantee_State_Bank_of_India.pdf" in res["response"]
    assert res["intent"] == "TENDER_INFO"


@pytest.mark.asyncio
async def test_chat_simple_006_turnover_requirement():
    """CHAT-SIMPLE-006: What is the turnover requirement?"""
    res = resolve_procurement_query("What is the turnover requirement?")
    assert res is not None
    assert "₹357.36 lakhs" in res["response"]
    assert "01_Bid_Submission_and_Technical_Bid_Form.pdf" in res["response"]
    assert "Clause 2(e)" in res["response"]
    assert res["intent"] == "REQUIREMENT_STATUS"


@pytest.mark.asyncio
async def test_chat_simple_007_pending_items():
    """CHAT-SIMPLE-007: What is pending?"""
    res = resolve_procurement_query("What is pending?")
    assert res is not None
    assert "1 clarification pending" in res["response"]
    assert "1 critical finding" in res["response"]
    assert "1 high finding" in res["response"]
    assert res["intent"] == "PENDING_ITEMS"


@pytest.mark.asyncio
async def test_chat_simple_008_verification_status():
    """CHAT-SIMPLE-008: What has been verified?"""
    res = resolve_procurement_query("What has been verified?")
    assert res is not None
    assert "10 verification checks" in res["response"]
    assert "6 Compliant" in res["response"]
    assert "2 Partial" in res["response"]
    assert "1 Evidence Missing" in res["response"]
    assert "1 Clarification Pending" in res["response"]
    assert res["intent"] == "VERIFICATION_STATUS"


@pytest.mark.asyncio
async def test_chat_simple_009_findings_list():
    """CHAT-SIMPLE-009: What are the findings?"""
    res = resolve_procurement_query("What are the findings?")
    assert res is not None
    assert "5 findings" in res["response"]
    assert "FND-01 [CRITICAL]" in res["response"]
    assert "FND-02 [HIGH]" in res["response"]
    assert "FND-03 [MEDIUM]" in res["response"]
    assert res["intent"] == "FINDING_LIST"


@pytest.mark.asyncio
async def test_chat_simple_010_turnover_flagged():
    """CHAT-SIMPLE-010: Why was the turnover flagged?"""
    res = resolve_procurement_query("Why was the turnover flagged?")
    assert res is not None
    assert "₹80.15 Lakhs" in res["response"]
    assert "FND-02 [HIGH]" in res["response"]
    assert "03_Financial_Turnover_and_Audited_Statements.pdf" in res["response"]
    assert res["intent"] == "FINDING_DETAIL"


@pytest.mark.asyncio
async def test_chat_simple_011_missing_evidence():
    """CHAT-SIMPLE-011: What is missing?"""
    res = resolve_procurement_query("What is missing?")
    assert res is not None
    assert "Annexure-9 VVIP Security Area Affidavit" in res["response"]
    assert "FND-01 [CRITICAL]" in res["response"]
    assert "05_Statutory_Affidavits_and_Compliance_Undertakings.pdf" in res["response"]
    assert res["intent"] == "COMPLIANCE_STATUS"


@pytest.mark.asyncio
async def test_chat_simple_012_government_verification():
    """CHAT-SIMPLE-012: Can GST be verified?"""
    res = resolve_procurement_query("Can GST be verified?")
    assert res is not None
    assert "Live external GST/MCA/Udyam verification is not configured" in res["response"]
    assert "check internal consistency" in res["response"]
    assert res["intent"] == "VERIFICATION_LIMITATION"


@pytest.mark.asyncio
async def test_chat_simple_013_officer_review():
    """CHAT-SIMPLE-013: What requires officer review?"""
    res = resolve_procurement_query("What requires officer review?")
    assert res is not None
    assert "FND-01 [CRITICAL]" in res["response"]
    assert "FND-02 [HIGH]" in res["response"]
    assert "designated Procurement Officer" in res["response"]
    assert res["intent"] == "OFFICER_REVIEW"


@pytest.mark.asyncio
async def test_chat_simple_014_help():
    """CHAT-SIMPLE-014: What can you do?"""
    res = resolve_procurement_query("What can you do?")
    assert res is not None
    assert "You can ask me about:" in res["response"]
    assert "Tender details" in res["response"]
    assert "Findings" in res["response"]
    assert res["intent"] == "HELP"


@pytest.mark.asyncio
async def test_chat_natural_variations():
    """Verify short queries, case-insensitivity, and colloquial variations."""
    # emd?
    res_emd = resolve_procurement_query("emd?")
    assert res_emd is not None
    assert "₹35,73,639" in res_emd["response"]

    # bidder?
    res_bidder = resolve_procurement_query("bidder?")
    assert res_bidder is not None
    assert "Aravind Integrated Solutions" in res_bidder["response"]

    # who submitted this?
    res_sub = resolve_procurement_query("who submitted this?")
    assert res_sub is not None
    assert "Aravind Integrated Solutions" in res_sub["response"]

    # what docs?
    res_docs = resolve_procurement_query("what docs?")
    assert res_docs is not None
    assert "6 documents were submitted" in res_docs["response"]

    # how much is the turnover?
    res_to = resolve_procurement_query("how much is the turnover?")
    assert res_to is not None
    assert "₹357.36 lakhs" in res_to["response"]

    # what needs review?
    res_rev = resolve_procurement_query("what needs review?")
    assert res_rev is not None
    assert "FND-01" in res_rev["response"]


@pytest.mark.asyncio
async def test_chat_contextual_followups():
    """Verify follow-up context tracking across a conversation session."""
    session_id = "followup-session-999"

    # Step 1: Inquire about turnover
    res1 = resolve_procurement_query("What is the turnover requirement?", conversation_id=session_id)
    assert res1 is not None
    assert "₹357.36 lakhs" in res1["response"]

    # Step 2: Follow-up: "What did the bidder submit?"
    res2 = resolve_procurement_query("What did the bidder submit?", conversation_id=session_id)
    assert res2 is not None
    assert "03_Financial_Turnover_and_Audited_Statements.pdf" in res2["response"]

    # Step 3: Follow-up: "Is there a problem?"
    res3 = resolve_procurement_query("Is there a problem?", conversation_id=session_id)
    assert res3 is not None
    assert "₹80.15 lakhs" in res3["response"]
    assert "FND-02" in res3["response"]


@pytest.mark.asyncio
async def test_chat_safeguard():
    """Verify no autonomous procurement decisions are ever made."""
    res = resolve_procurement_query("Should we select this bidder?")
    assert res is not None
    assert "final procurement decision must be made by the designated Procurement Officer" in res["response"]
    assert res["intent"] == "AUTONOMOUS_DECISION_SAFEGUARD"


@pytest.mark.asyncio
async def test_chat_api_endpoint_via_http():
    """Verify /api/v1/assistant/chat endpoint returns deterministic responses over HTTP."""
    from httpx import AsyncClient, ASGITransport
    from app.main import app
    from app.api.deps import get_current_user
    from app.models.user import User

    fake_user = User(
        id="usr-test-1",
        email="officer@cag.gov.in",
        full_name="Procurement Officer",
        role="OFFICER",
        is_active=True,
    )
    app.dependency_overrides[get_current_user] = lambda: fake_user

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Test 1: What is the EMD?
        resp1 = await client.post("/api/v1/assistant/chat", json={"query": "What is the EMD?"})
        assert resp1.status_code == 200
        data1 = resp1.json()
        assert "₹35,73,639" in data1["response"]
        assert data1["intent"] == "TENDER_INFO"
        assert len(data1["citations"]) >= 1

        # Test 2: Who is the bidder?
        resp2 = await client.post("/api/v1/assistant/chat", json={"query": "Who is the bidder?"})
        assert resp2.status_code == 200
        data2 = resp2.json()
        assert "Aravind Integrated Solutions Private Limited" in data2["response"]

        # Test 3: Can GST be verified?
        resp3 = await client.post("/api/v1/assistant/chat", json={"query": "Can GST be verified?"})
        assert resp3.status_code == 200
        data3 = resp3.json()
        assert "Live external GST/MCA/Udyam verification is not configured" in data3["response"]

    app.dependency_overrides.clear()


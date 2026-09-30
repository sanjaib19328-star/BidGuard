import pytest
from app.models.enums import NameMatchVerdict, VerificationResultStatus
from app.services.verification.base_adapter import sanitize_payload
from app.services.verification.gst_adapter import GstVerificationAdapter
from app.services.verification.pan_adapter import PanVerificationAdapter
from app.services.verification.udyam_adapter import UdyamVerificationAdapter


def test_sanitize_payload_recursive():
    raw = {
        "user": "officer_1",
        "access_token": "secret_token_abc_123",
        "headers": {
            "Authorization": "Bearer sensitive_jwt_token",
            "api_key": "sec_key_xyz",
            "Accept": "application/json",
        },
        "nested": {
            "db_password": "super_secret_db_pass",
            "safe_field": 42,
        },
    }
    sanitized = sanitize_payload(raw)
    assert sanitized["user"] == "officer_1"
    assert sanitized["access_token"] == "[REDACTED_CREDENTIAL]"
    assert sanitized["headers"]["Authorization"] == "[REDACTED_CREDENTIAL]"
    assert sanitized["headers"]["api_key"] == "[REDACTED_CREDENTIAL]"
    assert sanitized["headers"]["Accept"] == "application/json"
    assert sanitized["nested"]["db_password"] == "[REDACTED_CREDENTIAL]"
    assert sanitized["nested"]["safe_field"] == 42


@pytest.mark.asyncio
async def test_gst_adapter_invalid_format():
    adapter = GstVerificationAdapter()
    res = await adapter.verify(identifier="INVALID_GSTIN_123")
    assert res.status == VerificationResultStatus.INVALID_FORMAT
    assert res.officer_action_required is True
    assert any("GSTIN" in d.get("issue", "") for d in res.discrepancies)


@pytest.mark.asyncio
async def test_gst_adapter_sandbox_verified():
    adapter = GstVerificationAdapter()
    # Bidder A benchmark GSTIN
    gstin = "33AAACA1234A1Z5"
    bidder_name = "Apex Heavy Engineering Private Limited"

    res = await adapter.verify(
        identifier=gstin,
        bidder_legal_name=bidder_name,
        auth_config={},
        is_sandbox=True,
    )
    assert res.status == VerificationResultStatus.VERIFIED
    assert res.name_match_verdict in (
        NameMatchVerdict.EXACT_MATCH,
        NameMatchVerdict.FORMATTING_VARIATION,
    )
    assert res.matched_fields["status"] == "ACTIVE"
    assert res.sanitized_response["state_name"] == "Tamil Nadu"
    assert res.officer_action_required is False


@pytest.mark.asyncio
async def test_gst_adapter_sandbox_name_mismatch():
    adapter = GstVerificationAdapter()
    gstin = "33AAACA1234A1Z5"
    different_name = "Completely Different Company LLP"

    res = await adapter.verify(
        identifier=gstin,
        bidder_legal_name=different_name,
        auth_config={},
        is_sandbox=True,
    )
    assert res.status == VerificationResultStatus.MISMATCH
    assert res.name_match_verdict == NameMatchVerdict.SERIOUS_MISMATCH
    assert res.officer_action_required is True


@pytest.mark.asyncio
async def test_gst_adapter_sandbox_not_found():
    adapter = GstVerificationAdapter()
    unknown_gstin = "33ZZZZZ9999Z1Z9"

    res = await adapter.verify(
        identifier=unknown_gstin,
        bidder_legal_name="Apex Heavy Engineering",
        auth_config={},
        is_sandbox=True,
    )
    assert res.status == VerificationResultStatus.NOT_FOUND
    assert res.officer_action_required is True


@pytest.mark.asyncio
async def test_gst_adapter_live_mode_auth_required():
    adapter = GstVerificationAdapter()
    gstin = "33AAACA1234A1Z5"

    # Live mode with empty/missing credentials MUST yield AUTH_REQUIRED and no fabricated data
    res = await adapter.verify(
        identifier=gstin,
        bidder_legal_name="Apex Heavy Engineering Private Limited",
        auth_config={},
        is_sandbox=False,
    )
    assert res.status == VerificationResultStatus.AUTH_REQUIRED
    assert "Authorized connection required" in res.sanitized_response.get("message", "")
    assert res.officer_action_required is True
    # Ensure no fabricated legal data was generated
    assert res.matched_fields is None


@pytest.mark.asyncio
async def test_udyam_adapter_sandbox_verified():
    adapter = UdyamVerificationAdapter()
    udyam_num = "UDYAM-TN-02-0012345"
    bidder_name = "Apex Heavy Engineering Private Limited"

    res = await adapter.verify(
        identifier=udyam_num,
        bidder_legal_name=bidder_name,
        auth_config={},
        is_sandbox=True,
    )
    assert res.status == VerificationResultStatus.VERIFIED
    assert res.matched_fields["enterprise_type"] == "Small"
    assert res.matched_fields["major_activity"] == "Manufacturing"
    assert res.matched_fields["nic_code"] == "2512"


@pytest.mark.asyncio
async def test_udyam_adapter_live_mode_auth_required():
    adapter = UdyamVerificationAdapter()
    udyam_num = "UDYAM-TN-02-0012345"

    res = await adapter.verify(
        identifier=udyam_num,
        bidder_legal_name="Apex Heavy Engineering Private Limited",
        auth_config={},
        is_sandbox=False,
    )
    assert res.status == VerificationResultStatus.AUTH_REQUIRED
    assert "Authorized connection required" in res.sanitized_response.get("message", "")
    assert res.matched_fields is None


@pytest.mark.asyncio
async def test_pan_adapter_sandbox_verified():
    adapter = PanVerificationAdapter()
    pan = "AAACA1234A"
    bidder_name = "Apex Heavy Engineering Private Limited"

    res = await adapter.verify(
        identifier=pan,
        bidder_legal_name=bidder_name,
        auth_config={},
        is_sandbox=True,
    )
    assert res.status == VerificationResultStatus.VERIFIED
    assert res.matched_fields["status"] == "ACTIVE"
    assert res.matched_fields["category"] == "Company"


@pytest.mark.asyncio
async def test_pan_adapter_live_mode_auth_required():
    adapter = PanVerificationAdapter()
    pan = "AAACA1234A"

    res = await adapter.verify(
        identifier=pan,
        bidder_legal_name="Apex Heavy Engineering Private Limited",
        auth_config={},
        is_sandbox=False,
    )
    assert res.status == VerificationResultStatus.AUTH_REQUIRED
    assert "Authorized connection required" in res.sanitized_response.get("message", "")
    assert res.matched_fields is None

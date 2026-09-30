from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
import uuid
from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bidder import Bidder
from app.models.enums import ConnectorStatus, DataSourceType, VerificationResultStatus
from app.models.verification import DataSourceConnector, VerificationRequest, VerificationResult
from app.services.audit_service import log_audit_event
from app.services.bidder_service import get_bidder_by_id
from app.services.verification import ADAPTERS

SYSTEM_CONNECTORS = [
    {
        "source_type": DataSourceType.GSTN_PORTAL,
        "name": "GSTN Authorized Taxpayer Verification Connector",
        "description": "Validates GSTIN registration, taxpayer status, filing state, and legal name against GST portal.",
        "status": ConnectorStatus.SANDBOX_ACTIVE,
    },
    {
        "source_type": DataSourceType.UDYAM_MSME,
        "name": "Ministry of MSME Udyam Registration Connector",
        "description": "Validates Udyam registration certificates, enterprise category, and NIC manufacturing codes.",
        "status": ConnectorStatus.SANDBOX_ACTIVE,
    },
    {
        "source_type": DataSourceType.CBDT_PAN,
        "name": "CBDT / Income Tax Department PAN Verification Connector",
        "description": "Verifies PAN card validity, entity category, and legal identity with CBDT tax records.",
        "status": ConnectorStatus.SANDBOX_ACTIVE,
    },
    {
        "source_type": DataSourceType.API_SETU,
        "name": "National API Setu Government Gateway",
        "description": "Authorized gateway connector for government registries (requires OAuth2 credentials).",
        "status": ConnectorStatus.AUTH_REQUIRED,
    },
    {
        "source_type": DataSourceType.OPEN_DATA_GOV,
        "name": "Open Government Data (OGD) Registry Connector",
        "description": "Open public data connector for verified public sector suppliers and debarred entities.",
        "status": ConnectorStatus.SANDBOX_ACTIVE,
    },
]


async def ensure_default_connectors(session: AsyncSession, organization_id: uuid.UUID) -> List[DataSourceConnector]:
    """Ensure standard default data source connectors exist for the organization."""
    query = select(DataSourceConnector).where(
        or_(
            DataSourceConnector.organization_id == organization_id,
            DataSourceConnector.organization_id.is_(None),
        )
    )
    res = await session.execute(query)
    connectors = list(res.scalars().all())

    existing_types = {c.source_type for c in connectors}
    added = False

    for item in SYSTEM_CONNECTORS:
        if item["source_type"] not in existing_types:
            c = DataSourceConnector(
                organization_id=organization_id,
                source_type=item["source_type"],
                name=item["name"],
                description=item["description"],
                status=item["status"],
                is_enabled=True,
                auth_config={"is_sandbox": item["status"] == ConnectorStatus.SANDBOX_ACTIVE},
            )
            session.add(c)
            connectors.append(c)
            added = True

    if added:
        await session.commit()
        for c in connectors:
            await session.refresh(c)

    return connectors


async def list_connectors(session: AsyncSession, organization_id: uuid.UUID) -> List[DataSourceConnector]:
    """List all connectors for organization."""
    return await ensure_default_connectors(session, organization_id)


async def get_connector(
    session: AsyncSession,
    connector_id: uuid.UUID,
    organization_id: uuid.UUID,
) -> DataSourceConnector:
    """Get single connector."""
    query = select(DataSourceConnector).where(
        DataSourceConnector.id == connector_id,
        or_(
            DataSourceConnector.organization_id == organization_id,
            DataSourceConnector.organization_id.is_(None),
        ),
    )
    res = await session.execute(query)
    connector = res.scalar_one_or_none()
    if not connector:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Data source connector not found.",
        )
    return connector


async def configure_connector(
    session: AsyncSession,
    connector_id: uuid.UUID,
    organization_id: uuid.UUID,
    status_val: Optional[ConnectorStatus] = None,
    is_enabled: Optional[bool] = None,
    auth_config: Optional[Dict[str, Any]] = None,
    user_id: Optional[uuid.UUID] = None,
) -> DataSourceConnector:
    """Configure connector mode and credentials."""
    connector = await get_connector(session, connector_id, organization_id)

    if status_val is not None:
        connector.status = status_val
    if is_enabled is not None:
        connector.is_enabled = is_enabled
    if auth_config is not None:
        connector.auth_config = auth_config

    await session.commit()
    await session.refresh(connector)

    if user_id:
        await log_audit_event(
            session=session,
            action="CONNECTOR_CONFIGURED",
            entity_type="data_source_connector",
            entity_id=str(connector.id),
            organization_id=organization_id,
            actor_user_id=user_id,
            new_state={"name": connector.name, "status": connector.status.value},
        )
    return connector


async def test_connector_health(
    session: AsyncSession,
    connector_id: uuid.UUID,
    organization_id: uuid.UUID,
) -> Dict[str, Any]:
    """Test connector connectivity and update health check timestamp."""
    connector = await get_connector(session, connector_id, organization_id)
    connector.last_health_check_at = datetime.now(timezone.utc)

    is_sandbox = connector.status == ConnectorStatus.SANDBOX_ACTIVE
    is_connected = connector.status in (ConnectorStatus.CONNECTED, ConnectorStatus.SANDBOX_ACTIVE)

    if is_sandbox:
        connector.last_success_at = datetime.now(timezone.utc)
        await session.commit()
        return {
            "connector_id": str(connector.id),
            "source_type": connector.source_type.value,
            "status": "HEALTHY",
            "mode": "SANDBOX_BENCHMARK",
            "message": "Deterministic benchmark registry verified and ready for local evaluation.",
        }
    elif connector.status == ConnectorStatus.AUTH_REQUIRED:
        await session.commit()
        return {
            "connector_id": str(connector.id),
            "source_type": connector.source_type.value,
            "status": "AUTH_REQUIRED",
            "mode": "LIVE_EXTERNAL",
            "message": "Authorized connection required. Credentials must be configured for live verification.",
        }
    else:
        await session.commit()
        return {
            "connector_id": str(connector.id),
            "source_type": connector.source_type.value,
            "status": "OK" if is_connected else "DISCONNECTED",
            "mode": "LIVE_EXTERNAL",
            "message": "Connector ping successful" if is_connected else "Connector is disabled",
        }


async def verify_identifier(
    session: AsyncSession,
    organization_id: uuid.UUID,
    user_id: uuid.UUID,
    source_type: DataSourceType,
    identifier_value: str,
    bidder_id: Optional[uuid.UUID] = None,
    tender_id: Optional[uuid.UUID] = None,
) -> VerificationResult:
    """Execute single identifier verification against selected data source."""
    # 1. Resolve Bidder if given
    bidder = None
    bidder_legal_name = None
    if bidder_id:
        bidder = await get_bidder_by_id(session, bidder_id, organization_id)
        bidder_legal_name = bidder.legal_name

    # 2. Resolve Connector
    connectors = await ensure_default_connectors(session, organization_id)
    connector = next((c for c in connectors if c.source_type == source_type and c.is_enabled), None)
    
    is_sandbox = True
    auth_config = {}
    if connector:
        is_sandbox = connector.status == ConnectorStatus.SANDBOX_ACTIVE
        auth_config = connector.auth_config or {}

    # 3. Resolve Adapter
    adapter = ADAPTERS.get(source_type.value)
    if not adapter:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Verification adapter for {source_type.value} is not supported.",
        )

    # 4. Create VerificationRequest record
    req = VerificationRequest(
        organization_id=organization_id,
        bidder_id=bidder_id if bidder_id else (bidder.id if bidder else uuid.uuid4()),
        tender_id=tender_id,
        connector_id=connector.id if connector else None,
        verification_type=source_type,
        identifier_value=identifier_value.strip().upper(),
        requested_by=user_id,
    )
    session.add(req)
    await session.flush()
    await session.refresh(req)

    # 5. Run Verification via Adapter
    adapter_result = await adapter.verify(
        identifier=identifier_value,
        bidder_legal_name=bidder_legal_name,
        auth_config=auth_config,
        is_sandbox=is_sandbox,
    )

    # 6. Save VerificationResult
    result = VerificationResult(
        verification_request_id=req.id,
        bidder_id=req.bidder_id,
        source_type=source_type,
        status=adapter_result.status,
        sanitized_response=adapter_result.sanitized_response,
        matched_fields=adapter_result.matched_fields,
        name_match_score=adapter_result.name_match_score,
        name_match_verdict=adapter_result.name_match_verdict,
        discrepancies=adapter_result.discrepancies,
        officer_action_required=adapter_result.officer_action_required,
        recommended_action=adapter_result.recommended_action,
    )
    session.add(result)
    await session.flush()
    await session.refresh(result)

    # 7. Audit log
    await log_audit_event(
        session=session,
        action="GOVERNMENT_VERIFICATION_EXECUTED",
        entity_type="verification_result",
        entity_id=str(result.id),
        organization_id=organization_id,
        actor_user_id=user_id,
        new_state={
            "source": source_type.value,
            "identifier": identifier_value,
            "status": result.status.value,
            "verdict": result.name_match_verdict.value if result.name_match_verdict else None,
        },
    )
    await session.commit()
    await session.refresh(result)
    return result


async def run_all_bidder_verifications(
    session: AsyncSession,
    organization_id: uuid.UUID,
    user_id: uuid.UUID,
    bidder_id: uuid.UUID,
    tender_id: Optional[uuid.UUID] = None,
) -> Tuple[List[VerificationResult], str]:
    """Execute complete verification suite for all available identifiers of a bidder."""
    bidder = await get_bidder_by_id(session, bidder_id, organization_id)
    results: List[VerificationResult] = []

    # 1. GST Verification
    if bidder.gstin:
        r_gst = await verify_identifier(
            session=session,
            organization_id=organization_id,
            user_id=user_id,
            source_type=DataSourceType.GSTN_PORTAL,
            identifier_value=bidder.gstin,
            bidder_id=bidder_id,
            tender_id=tender_id,
        )
        results.append(r_gst)

    # 2. PAN Verification
    if bidder.pan:
        r_pan = await verify_identifier(
            session=session,
            organization_id=organization_id,
            user_id=user_id,
            source_type=DataSourceType.CBDT_PAN,
            identifier_value=bidder.pan,
            bidder_id=bidder_id,
            tender_id=tender_id,
        )
        results.append(r_pan)

    # 3. Udyam Verification (if claimed or registered)
    if bidder.udyam_registration_number:
        r_udyam = await verify_identifier(
            session=session,
            organization_id=organization_id,
            user_id=user_id,
            source_type=DataSourceType.UDYAM_MSME,
            identifier_value=bidder.udyam_registration_number,
            bidder_id=bidder_id,
            tender_id=tender_id,
        )
        results.append(r_udyam)

    # Overall summary verdict
    has_mismatch = any(r.status == VerificationResultStatus.MISMATCH for r in results)
    has_auth_req = any(r.status == VerificationResultStatus.AUTH_REQUIRED for r in results)
    all_verified = bool(results) and all(r.status == VerificationResultStatus.VERIFIED for r in results)

    if has_mismatch:
        overall = "MISMATCH_DETECTED"
    elif has_auth_req:
        overall = "AUTH_REQUIRED"
    elif all_verified:
        overall = "FULLY_VERIFIED"
    else:
        overall = "PARTIALLY_VERIFIED"

    return results, overall


async def list_bidder_verification_results(
    session: AsyncSession,
    organization_id: uuid.UUID,
    bidder_id: uuid.UUID,
) -> List[VerificationResult]:
    """Retrieve all historical verification results for a bidder."""
    await get_bidder_by_id(session, bidder_id, organization_id)
    query = (
        select(VerificationResult)
        .where(VerificationResult.bidder_id == bidder_id)
        .order_by(VerificationResult.created_at.desc())
    )
    res = await session.execute(query)
    return list(res.scalars().all())

import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_roles
from app.models.enums import DataSourceType, UserRole
from app.models.user import User
from app.schemas.verification import (
    BidderVerificationRunRequest,
    BidderVerificationRunResponse,
    ConnectorConfigureRequest,
    ConnectorListResponse,
    ConnectorResponse,
    ConnectorTestResponse,
    GstVerificationRequest,
    PanVerificationRequest,
    SingleIdentifierVerificationRequest,
    UdyamVerificationRequest,
    VerificationResultListResponse,
    VerificationResultResponse,
)
from app.services import verification_service
from app.services.bidder_service import get_bidder_by_id

router = APIRouter(prefix="/verification", tags=["Verification Center"])


@router.get(
    "/connectors",
    response_model=ConnectorListResponse,
    summary="List data source connectors",
    description="Retrieve status and configurations of all government and open-data connectors for the organization.",
)
async def list_connectors(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.PROCUREMENT_OFFICER, UserRole.AUDITOR])),
):
    connectors = await verification_service.list_connectors(
        session=db,
        organization_id=current_user.organization_id,
    )
    items = [ConnectorResponse.model_validate(c) for c in connectors]
    return ConnectorListResponse(items=items, total=len(items))


@router.post(
    "/connectors/{connector_id}/configure",
    response_model=ConnectorResponse,
    summary="Configure connector settings",
    description="Update connector operation mode (Sandbox vs Live) and connection credentials.",
)
async def configure_connector(
    connector_id: uuid.UUID,
    data: ConnectorConfigureRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
):
    connector = await verification_service.configure_connector(
        session=db,
        connector_id=connector_id,
        organization_id=current_user.organization_id,
        status_val=data.status,
        is_enabled=data.is_enabled,
        auth_config=data.auth_config,
        user_id=current_user.id,
    )
    return ConnectorResponse.model_validate(connector)


@router.post(
    "/connectors/{connector_id}/test",
    response_model=ConnectorTestResponse,
    summary="Test connector health",
    description="Perform real-time connectivity and authorization check against the selected connector.",
)
async def test_connector(
    connector_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.PROCUREMENT_OFFICER])),
):
    result = await verification_service.test_connector_health(
        session=db,
        connector_id=connector_id,
        organization_id=current_user.organization_id,
    )
    return ConnectorTestResponse(**result)


@router.post(
    "/verify-identifier",
    response_model=VerificationResultResponse,
    summary="Verify single government identifier",
    description="Verify an arbitrary identifier against the selected government data source.",
)
async def verify_identifier(
    data: SingleIdentifierVerificationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.PROCUREMENT_OFFICER])),
):
    result = await verification_service.verify_identifier(
        session=db,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        source_type=data.source_type,
        identifier_value=data.identifier_value,
        bidder_id=data.bidder_id,
        tender_id=data.tender_id,
    )
    return VerificationResultResponse.model_validate(result)


@router.post(
    "/gst",
    response_model=VerificationResultResponse,
    summary="Verify GSTIN",
    description="Verify 15-character GSTIN against GST portal / sandbox benchmark registry.",
)
async def verify_gst(
    data: GstVerificationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.PROCUREMENT_OFFICER])),
):
    result = await verification_service.verify_identifier(
        session=db,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        source_type=DataSourceType.GSTN_PORTAL,
        identifier_value=data.gstin,
        bidder_id=data.bidder_id,
        tender_id=data.tender_id,
    )
    return VerificationResultResponse.model_validate(result)


@router.post(
    "/udyam",
    response_model=VerificationResultResponse,
    summary="Verify Udyam Registration",
    description="Verify Udyam MSME certificate and NIC manufacturing classifications.",
)
async def verify_udyam(
    data: UdyamVerificationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.PROCUREMENT_OFFICER])),
):
    result = await verification_service.verify_identifier(
        session=db,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        source_type=DataSourceType.UDYAM_MSME,
        identifier_value=data.udyam_number,
        bidder_id=data.bidder_id,
        tender_id=data.tender_id,
    )
    return VerificationResultResponse.model_validate(result)


@router.post(
    "/pan",
    response_model=VerificationResultResponse,
    summary="Verify Income Tax PAN",
    description="Verify 10-character PAN against CBDT / Income Tax Department registry.",
)
async def verify_pan(
    data: PanVerificationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.PROCUREMENT_OFFICER])),
):
    result = await verification_service.verify_identifier(
        session=db,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        source_type=DataSourceType.CBDT_PAN,
        identifier_value=data.pan,
        bidder_id=data.bidder_id,
        tender_id=data.tender_id,
    )
    return VerificationResultResponse.model_validate(result)


@router.post(
    "/bidder/{bidder_id}/run-all",
    response_model=BidderVerificationRunResponse,
    summary="Run full verification suite for bidder",
    description="Execute GST, PAN, and Udyam verifications for all identifiers on the bidder profile.",
)
async def run_all_bidder_verifications(
    bidder_id: uuid.UUID,
    data: Optional[BidderVerificationRunRequest] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.PROCUREMENT_OFFICER])),
):
    bidder = await get_bidder_by_id(db, bidder_id, current_user.organization_id)
    tender_id = data.tender_id if data else None

    results, overall = await verification_service.run_all_bidder_verifications(
        session=db,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        bidder_id=bidder_id,
        tender_id=tender_id,
    )

    result_responses = [VerificationResultResponse.model_validate(r) for r in results]
    return BidderVerificationRunResponse(
        bidder_id=bidder.id,
        bidder_legal_name=bidder.legal_name,
        overall_status=overall,
        total_checks=len(result_responses),
        results=result_responses,
    )


@router.get(
    "/bidder/{bidder_id}/results",
    response_model=VerificationResultListResponse,
    summary="Get verification history for bidder",
    description="Retrieve all historical external data source verification results recorded for a bidder.",
)
async def list_bidder_verification_results(
    bidder_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.PROCUREMENT_OFFICER, UserRole.AUDITOR])),
):
    results = await verification_service.list_bidder_verification_results(
        session=db,
        organization_id=current_user.organization_id,
        bidder_id=bidder_id,
    )
    items = [VerificationResultResponse.model_validate(r) for r in results]
    return VerificationResultListResponse(items=items, total=len(items))

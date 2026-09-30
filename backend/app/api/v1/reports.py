import uuid
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_roles
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.report import ComplianceDossierResponse
from app.services import report_service
from app.services.audit_service import log_audit_event

router = APIRouter(tags=["Compliance Dossier & Reports"])

ALLOWED_REPORT_ROLES = [
    UserRole.ADMIN,
    UserRole.PROCUREMENT_OFFICER,
    UserRole.REVIEWER,
    UserRole.AUDITOR,
]


@router.get(
    "/tenders/{tender_id}/bidders/{bidder_id}/report/json",
    response_model=ComplianceDossierResponse,
    summary="Get 16-section compliance evaluation dossier as JSON",
)
async def get_compliance_report_json(
    tender_id: uuid.UUID,
    bidder_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(ALLOWED_REPORT_ROLES)),
):
    try:
        data = await report_service.build_compliance_dossier_data(
            session=db,
            tender_id=tender_id,
            bidder_id=bidder_id,
            organization_id=current_user.organization_id,
        )
    except ValueError as ex:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ex))

    await log_audit_event(
        session=db,
        action="REPORT_JSON_VIEWED",
        entity_type="compliance_dossier",
        entity_id=f"{tender_id}:{bidder_id}",
        actor_user_id=current_user.id,
        organization_id=current_user.organization_id,
    )
    await db.commit()

    return data


@router.get(
    "/tenders/{tender_id}/bidders/{bidder_id}/report/pdf",
    summary="Download official multi-page PDF compliance evaluation dossier",
)
async def get_compliance_report_pdf(
    tender_id: uuid.UUID,
    bidder_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(ALLOWED_REPORT_ROLES)),
):
    try:
        data = await report_service.build_compliance_dossier_data(
            session=db,
            tender_id=tender_id,
            bidder_id=bidder_id,
            organization_id=current_user.organization_id,
        )
        pdf_bytes = report_service.generate_compliance_pdf_report(data)
    except ValueError as ex:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ex))

    await log_audit_event(
        session=db,
        action="REPORT_PDF_DOWNLOADED",
        entity_type="compliance_dossier",
        entity_id=f"{tender_id}:{bidder_id}",
        actor_user_id=current_user.id,
        organization_id=current_user.organization_id,
    )
    await db.commit()

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="BidGuard_Dossier_{tender_id}_{bidder_id}.pdf"'
        },
    )


@router.get(
    "/tenders/{tender_id}/bidders/{bidder_id}/report/csv",
    summary="Download compliance evaluation matrix as CSV",
)
async def get_compliance_report_csv(
    tender_id: uuid.UUID,
    bidder_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(ALLOWED_REPORT_ROLES)),
):
    try:
        data = await report_service.build_compliance_dossier_data(
            session=db,
            tender_id=tender_id,
            bidder_id=bidder_id,
            organization_id=current_user.organization_id,
        )
        csv_text = report_service.generate_compliance_csv_report(data)
    except ValueError as ex:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ex))

    await log_audit_event(
        session=db,
        action="REPORT_CSV_DOWNLOADED",
        entity_type="compliance_matrix",
        entity_id=f"{tender_id}:{bidder_id}",
        actor_user_id=current_user.id,
        organization_id=current_user.organization_id,
    )
    await db.commit()

    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="BidGuard_Matrix_{tender_id}_{bidder_id}.csv"'
        },
    )

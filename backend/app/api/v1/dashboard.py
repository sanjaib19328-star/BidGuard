from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_roles
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.report import DashboardMetricsResponse
from app.services import dashboard_service

router = APIRouter(prefix="/dashboard", tags=["Executive Dashboard"])

ALLOWED_DASHBOARD_ROLES = [
    UserRole.ADMIN,
    UserRole.PROCUREMENT_OFFICER,
    UserRole.REVIEWER,
    UserRole.AUDITOR,
]


@router.get(
    "/metrics",
    response_model=DashboardMetricsResponse,
    summary="Get executive procurement analytics and KPI metrics",
    description="Provides real-time aggregated metrics across tenders, bidders, compliance matrix statuses, risk findings, and verification services.",
)
async def get_dashboard_metrics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(ALLOWED_DASHBOARD_ROLES)),
):
    metrics = await dashboard_service.get_procurement_dashboard_metrics(
        session=db,
        organization_id=current_user.organization_id,
    )
    return metrics


@router.get(
    "/reference-tenders",
    summary="Get authentic GeM reference tenders catalog",
    description="Returns pre-ingested authentic Indian GeM tenders from the reference manifest.",
)
async def get_reference_tenders():
    import json
    import os
    ref_manifest = os.path.join(os.getcwd(), "data", "reference_tenders", "gem_tender_manifest.json")
    if os.path.exists(ref_manifest):
        with open(ref_manifest, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"tenders": []}


from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.tenders import router as tenders_router
from app.api.v1.bidders import router as bidders_router
from app.api.v1.verification import router as verification_router
from app.api.v1.compliance_matrix import router as compliance_matrix_router
from app.api.v1.reports import router as reports_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.assistant import router as assistant_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(tenders_router)
api_router.include_router(bidders_router)
api_router.include_router(verification_router)
api_router.include_router(compliance_matrix_router)
api_router.include_router(reports_router)
api_router.include_router(dashboard_router)
api_router.include_router(assistant_router)

__all__ = ["api_router"]



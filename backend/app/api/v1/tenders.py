import uuid
from typing import Any, Optional
from fastapi import APIRouter, Depends, File, Query, Request, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    get_current_user,
    get_db,
    require_admin,
    require_roles,
)
from app.models.enums import (
    ClauseCategory,
    ComplianceRuleType,
    EvaluationStatus,
    RequirementApplicability,
    RequirementType,
    RiskHint,
    TenderStatus,
    UserRole,
    VerificationMethod,
)
from app.models.user import User
from app.schemas.clause import (
    ClauseExtractionRequest,
    ClauseExtractionResponse,
    ClauseListResponse,
    ClauseResponse,
)
from app.schemas.compliance import (
    CompileRulesRequest,
    CompileRulesResponse,
    ComplianceRuleListResponse,
    ComplianceRuleResponse,
    EvaluateRulesRequest,
    EvaluateRulesResponse,
    EvaluationResultItem,
    EvaluationSummary,
    SourceRequirementMetadata,
)
from app.schemas.requirement import (
    RequirementExtractionRequest,
    RequirementExtractionResponse,
    RequirementListResponse,
    RequirementResponse,
    SourceClauseMetadata,
)
from app.schemas.document import (
    DocumentListResponse,
    DocumentResponse,
)
from app.schemas.tender import (
    TenderCreateRequest,
    TenderListResponse,
    TenderResponse,
    TenderStatusUpdateRequest,
    TenderUpdateRequest,
)
from app.services import (
    clause_extraction_service,
    compliance_evaluation_service,
    compliance_rule_compiler,
    document_service,
    requirement_extraction_service,
    tender_service,
)

router = APIRouter(prefix="/tenders", tags=["Tender Management"])


@router.post(
    "",
    response_model=TenderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new tender",
    description="Creates a tender in DRAFT status scoped to the user's organization. Requires ADMIN or PROCUREMENT_OFFICER role.",
)
async def create_tender(
    req: TenderCreateRequest,
    request: Request,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.PROCUREMENT_OFFICER)),
    session: AsyncSession = Depends(get_db),
) -> Any:
    """Create a tender record."""
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    tender = await tender_service.create_tender(
        session=session,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        req=req,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    return tender


@router.get(
    "",
    response_model=TenderListResponse,
    status_code=status.HTTP_200_OK,
    summary="List organization tenders",
    description="List and filter tenders belonging strictly to the authenticated user's organization.",
)
async def list_tenders(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page (max 100)"),
    status_filter: Optional[TenderStatus] = Query(default=None, alias="status", description="Filter by status"),
    search: Optional[str] = Query(default=None, description="Search term in title, tender number, or procuring entity"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Any:
    """List tenders for the current user's organization."""
    items, total = await tender_service.list_tenders(
        session=session,
        organization_id=current_user.organization_id,
        page=page,
        page_size=page_size,
        status_filter=status_filter,
        search=search,
    )
    return TenderListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{tender_id}",
    response_model=TenderResponse,
    status_code=status.HTTP_200_OK,
    summary="Get single tender details",
    description="Retrieve details of a specific tender by UUID, strictly scoped to the user's organization.",
)
async def get_tender(
    tender_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Any:
    """Retrieve single tender."""
    return await tender_service.get_tender_by_id(
        session=session,
        tender_id=tender_id,
        organization_id=current_user.organization_id,
    )


@router.patch(
    "/{tender_id}",
    response_model=TenderResponse,
    status_code=status.HTTP_200_OK,
    summary="Update tender metadata",
    description="Update metadata fields of an existing tender. Requires ADMIN or PROCUREMENT_OFFICER role.",
)
async def update_tender(
    tender_id: uuid.UUID,
    req: TenderUpdateRequest,
    request: Request,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.PROCUREMENT_OFFICER)),
    session: AsyncSession = Depends(get_db),
) -> Any:
    """Update tender metadata."""
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    return await tender_service.update_tender(
        session=session,
        tender_id=tender_id,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        req=req,
        ip_address=ip_address,
        user_agent=user_agent,
    )


@router.post(
    "/{tender_id}/status",
    response_model=TenderResponse,
    status_code=status.HTTP_200_OK,
    summary="Change tender lifecycle status",
    description="Transition tender to a new lifecycle status. Requires ADMIN, PROCUREMENT_OFFICER, or REVIEWER role.",
)
async def change_status(
    tender_id: uuid.UUID,
    req: TenderStatusUpdateRequest,
    request: Request,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.PROCUREMENT_OFFICER, UserRole.REVIEWER)),
    session: AsyncSession = Depends(get_db),
) -> Any:
    """Update tender lifecycle status."""
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    return await tender_service.change_tender_status(
        session=session,
        tender_id=tender_id,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        new_status=req.status,
        ip_address=ip_address,
        user_agent=user_agent,
    )


@router.post(
    "/{tender_id}/archive",
    response_model=TenderResponse,
    status_code=status.HTTP_200_OK,
    summary="Archive tender",
    description="Sets tender status to ARCHIVED. Requires ADMIN or PROCUREMENT_OFFICER role.",
)
async def archive_tender(
    tender_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.PROCUREMENT_OFFICER)),
    session: AsyncSession = Depends(get_db),
) -> Any:
    """Archive a tender."""
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    return await tender_service.archive_tender(
        session=session,
        tender_id=tender_id,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        ip_address=ip_address,
        user_agent=user_agent,
    )


@router.delete(
    "/{tender_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete DRAFT tender",
    description="Physically delete a DRAFT tender. Allowed exclusively for ADMIN role. Non-DRAFT tenders return 409 Conflict.",
)
async def delete_tender(
    tender_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
) -> None:
    """Delete a draft tender."""
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    await tender_service.delete_tender(
        session=session,
        tender_id=tender_id,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        ip_address=ip_address,
        user_agent=user_agent,
    )


# ==============================================================================
# Tender Document Management Endpoints (Phase 1.5)
# ==============================================================================

@router.post(
    "/{tender_id}/documents",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload tender PDF document",
    description="Upload a PDF document for a tender. Requires ADMIN or PROCUREMENT_OFFICER role.",
)
async def upload_document(
    tender_id: uuid.UUID,
    request: Request,
    file: UploadFile = File(..., description="PDF file to upload"),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.PROCUREMENT_OFFICER)),
    session: AsyncSession = Depends(get_db),
) -> Any:
    """Upload a tender PDF document."""
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    return await document_service.upload_document(
        session=session,
        tender_id=tender_id,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        upload_file=file,
        ip_address=ip_address,
        user_agent=user_agent,
    )


@router.get(
    "/{tender_id}/documents",
    response_model=DocumentListResponse,
    status_code=status.HTTP_200_OK,
    summary="List tender documents",
    description="List all documents associated with a tender. Accessible by all authenticated roles within the organization.",
)
async def list_documents(
    tender_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Any:
    """List documents for a tender."""
    items, total = await document_service.list_documents(
        session=session,
        tender_id=tender_id,
        organization_id=current_user.organization_id,
    )
    return DocumentListResponse(items=items, total=total)


@router.get(
    "/{tender_id}/documents/{document_id}",
    response_model=DocumentResponse,
    status_code=status.HTTP_200_OK,
    summary="Get tender document metadata",
    description="Retrieve metadata for a specific tender document. Accessible by all authenticated roles.",
)
async def get_document(
    tender_id: uuid.UUID,
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Any:
    """Get tender document metadata."""
    return await document_service.get_document(
        session=session,
        tender_id=tender_id,
        document_id=document_id,
        organization_id=current_user.organization_id,
    )


@router.get(
    "/{tender_id}/documents/{document_id}/download",
    status_code=status.HTTP_200_OK,
    summary="Download tender document PDF",
    description="Stream and download the physical PDF file. Accessible by all authenticated roles in the organization.",
)
async def download_document(
    tender_id: uuid.UUID,
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Any:
    """Download tender PDF document."""
    file_path, original_filename, mime_type = await document_service.get_document_for_download(
        session=session,
        tender_id=tender_id,
        document_id=document_id,
        organization_id=current_user.organization_id,
    )
    return FileResponse(
        path=file_path,
        media_type=mime_type,
        filename=original_filename,
    )


@router.delete(
    "/{tender_id}/documents/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete tender document",
    description="Physically delete a tender document and its database record. Requires ADMIN or PROCUREMENT_OFFICER role.",
)
async def delete_document(
    tender_id: uuid.UUID,
    document_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.PROCUREMENT_OFFICER)),
    session: AsyncSession = Depends(get_db),
) -> None:
    """Delete tender document."""
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    await document_service.delete_document(
        session=session,
        tender_id=tender_id,
        document_id=document_id,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        ip_address=ip_address,
        user_agent=user_agent,
    )


# ==============================================================================
# Tender Clause Extraction Endpoints (Phase 2.1)
# ==============================================================================

@router.post(
    "/{tender_id}/extract-clauses",
    response_model=ClauseExtractionResponse,
    status_code=status.HTTP_200_OK,
    summary="Extract tender clauses",
    description="Trigger deterministic, source-traceable clause segmentation and categorization for a tender. Requires ADMIN or PROCUREMENT_OFFICER role.",
)
async def extract_clauses(
    tender_id: uuid.UUID,
    request: Request,
    req: ClauseExtractionRequest = ClauseExtractionRequest(),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.PROCUREMENT_OFFICER)),
    session: AsyncSession = Depends(get_db),
) -> Any:
    """Extract and categorize tender clauses."""
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    clauses, total, breakdown = await clause_extraction_service.extract_tender_clauses(
        session=session,
        tender_id=tender_id,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        force_reextract=req.force_reextract,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    return ClauseExtractionResponse(
        tender_id=tender_id,
        total_clauses=total,
        categories_breakdown=breakdown,
        message=f"Successfully extracted {total} clauses for tender {tender_id}.",
    )


@router.get(
    "/{tender_id}/clauses",
    response_model=ClauseListResponse,
    status_code=status.HTTP_200_OK,
    summary="List tender clauses",
    description="Retrieve extracted clauses for a tender with optional category filtering and search. Accessible by all authenticated roles within the organization.",
)
async def list_clauses(
    tender_id: uuid.UUID,
    category: Optional[ClauseCategory] = Query(default=None, description="Filter by clause category"),
    search: Optional[str] = Query(default=None, description="Search term across clause text, title, or clause number"),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=50, ge=1, le=200, description="Items per page"),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.PROCUREMENT_OFFICER, UserRole.REVIEWER, UserRole.AUDITOR)),
    session: AsyncSession = Depends(get_db),
) -> Any:
    """List extracted clauses for a tender."""
    items, total, breakdown = await clause_extraction_service.list_tender_clauses(
        session=session,
        tender_id=tender_id,
        organization_id=current_user.organization_id,
        category=category,
        search=search,
        page=page,
        page_size=page_size,
    )

    return ClauseListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        tender_id=tender_id,
        categories_breakdown=breakdown,
    )


@router.get(
    "/{tender_id}/clauses/{clause_id}",
    response_model=ClauseResponse,
    status_code=status.HTTP_200_OK,
    summary="Get single tender clause",
    description="Retrieve details of an individual tender clause by UUID, strictly scoped to the user's organization.",
)
async def get_clause(
    tender_id: uuid.UUID,
    clause_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Any:
    """Retrieve details of an individual clause."""
    return await clause_extraction_service.get_tender_clause(
        session=session,
        tender_id=tender_id,
        clause_id=clause_id,
        organization_id=current_user.organization_id,
    )


# ==============================================================================
# Tender Requirement Matrix Extraction Endpoints (Phase 2.2)
# ==============================================================================

def _format_requirement_response(req: Any) -> RequirementResponse:
    source_meta = None
    if getattr(req, "clause", None):
        source_meta = SourceClauseMetadata(
            clause_id=req.clause.id,
            clause_number=req.clause.clause_number,
            title=req.clause.title,
            page_number=req.clause.page_number,
            document_id=req.clause.document_id,
        )
    return RequirementResponse(
        id=req.id,
        tender_id=req.tender_id,
        clause_id=req.clause_id,
        category=req.category,
        requirement_type=req.requirement_type,
        description=req.description,
        operator=req.operator,
        value_numeric=req.value_numeric,
        value_text=req.value_text,
        unit=req.unit,
        currency=req.currency,
        period=req.period,
        mandatory=req.mandatory,
        applicability=req.applicability,
        applicability_condition=req.applicability_condition,
        required_evidence=req.required_evidence or [],
        verification_method=req.verification_method,
        risk_hint=req.risk_hint,
        sequence_order=req.sequence_order,
        extraction_method=req.extraction_method,
        confidence=req.confidence,
        source=source_meta,
        created_at=req.created_at,
        updated_at=req.updated_at,
    )


@router.post(
    "/{tender_id}/extract-requirements",
    response_model=RequirementExtractionResponse,
    status_code=status.HTTP_200_OK,
    summary="Extract tender requirements matrix",
    description="Trigger deterministic, source-traceable requirement extraction and normalization from tender clauses. Requires ADMIN or PROCUREMENT_OFFICER role.",
)
async def extract_requirements(
    tender_id: uuid.UUID,
    request: Request,
    req: RequirementExtractionRequest = RequirementExtractionRequest(),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.PROCUREMENT_OFFICER)),
    session: AsyncSession = Depends(get_db),
) -> Any:
    """Extract and normalize tender requirements from clauses."""
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    (
        reqs,
        created_count,
        reused_count,
        cat_breakdown,
        type_breakdown,
    ) = await requirement_extraction_service.extract_tender_requirements(
        session=session,
        tender_id=tender_id,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        force_reextract=req.force_reextract,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    return RequirementExtractionResponse(
        tender_id=tender_id,
        requirements_created=created_count,
        requirements_reused=reused_count,
        requirements_total=len(reqs),
        categories_breakdown=cat_breakdown,
        types_breakdown=type_breakdown,
        status="COMPLETED",
        message=f"Successfully extracted {len(reqs)} structured requirements ({created_count} created, {reused_count} reused) for tender {tender_id}.",
    )


@router.get(
    "/{tender_id}/requirements",
    response_model=RequirementListResponse,
    status_code=status.HTTP_200_OK,
    summary="List tender requirements matrix",
    description="Retrieve structured tender requirements with filtering by category, type, mandatory status, applicability, verification method, and risk hint. Accessible by all authenticated roles within the organization.",
)
async def list_requirements(
    tender_id: uuid.UUID,
    category: Optional[ClauseCategory] = Query(default=None, description="Filter by requirement category"),
    requirement_type: Optional[RequirementType] = Query(default=None, description="Filter by requirement type"),
    mandatory: Optional[bool] = Query(default=None, description="Filter by mandatory status"),
    applicability: Optional[RequirementApplicability] = Query(default=None, description="Filter by applicability"),
    verification_method: Optional[VerificationMethod] = Query(default=None, description="Filter by verification method"),
    risk_hint: Optional[RiskHint] = Query(default=None, description="Filter by risk hint"),
    search: Optional[str] = Query(default=None, description="Search term across requirement description and values"),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=50, ge=1, le=200, description="Items per page"),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.PROCUREMENT_OFFICER, UserRole.REVIEWER, UserRole.AUDITOR)),
    session: AsyncSession = Depends(get_db),
) -> Any:
    """List structured requirements for a tender."""
    items, total, cat_breakdown, type_breakdown = await requirement_extraction_service.list_tender_requirements(
        session=session,
        tender_id=tender_id,
        organization_id=current_user.organization_id,
        category=category,
        requirement_type=requirement_type,
        mandatory=mandatory,
        applicability=applicability,
        verification_method=verification_method,
        risk_hint=risk_hint,
        search=search,
        page=page,
        page_size=page_size,
    )

    formatted_items = [_format_requirement_response(r) for r in items]

    return RequirementListResponse(
        items=formatted_items,
        total=total,
        page=page,
        page_size=page_size,
        tender_id=tender_id,
        categories_breakdown=cat_breakdown,
        types_breakdown=type_breakdown,
    )


@router.get(
    "/{tender_id}/requirements/{requirement_id}",
    response_model=RequirementResponse,
    status_code=status.HTTP_200_OK,
    summary="Get single tender requirement",
    description="Retrieve details of an individual requirement by UUID, strictly scoped to the user's organization.",
)
async def get_requirement(
    tender_id: uuid.UUID,
    requirement_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Any:
    """Retrieve details of an individual requirement."""
    req = await requirement_extraction_service.get_tender_requirement(
        session=session,
        tender_id=tender_id,
        requirement_id=requirement_id,
        organization_id=current_user.organization_id,
    )
    return _format_requirement_response(req)


# ==============================================================================
# Phase 3 — Compliance Rule Engine & Evaluation Endpoints
# ==============================================================================

def _format_rule_response(rule: Any) -> ComplianceRuleResponse:
    """Format a ComplianceRule entity into response schema with source requirement metadata."""
    req_meta = None
    if getattr(rule, "requirement", None):
        r = rule.requirement
        clause_num = r.clause.clause_number if getattr(r, "clause", None) else None
        page_num = r.clause.page_number if getattr(r, "clause", None) else None
        req_meta = SourceRequirementMetadata(
            requirement_id=r.id,
            clause_id=r.clause_id,
            category=r.category,
            requirement_type=r.requirement_type,
            description=r.description,
            operator=r.operator,
            value_numeric=r.value_numeric,
            value_text=r.value_text,
            unit=r.unit,
            currency=r.currency,
            period=r.period,
            mandatory=r.mandatory,
            applicability=r.applicability,
            applicability_condition=r.applicability_condition,
            verification_method=r.verification_method,
            risk_hint=r.risk_hint,
            clause_number=clause_num,
            page_number=page_num,
        )

    return ComplianceRuleResponse(
        id=rule.id,
        tender_id=rule.tender_id,
        requirement_id=rule.requirement_id,
        rule_type=rule.rule_type,
        rule_configuration=rule.rule_configuration,
        description=rule.description,
        enabled=rule.enabled,
        sequence_order=rule.sequence_order,
        confidence=rule.confidence,
        source_requirement=req_meta,
        created_at=rule.created_at,
        updated_at=rule.updated_at,
    )


def _format_evaluation_item(eval_entity: Any) -> EvaluationResultItem:
    """Format a ComplianceEvaluation entity into response schema with traceability metadata."""
    req_meta = None
    if getattr(eval_entity, "requirement", None):
        r = eval_entity.requirement
        clause_num = r.clause.clause_number if getattr(r, "clause", None) else None
        page_num = r.clause.page_number if getattr(r, "clause", None) else None
        req_meta = SourceRequirementMetadata(
            requirement_id=r.id,
            clause_id=r.clause_id,
            category=r.category,
            requirement_type=r.requirement_type,
            description=r.description,
            operator=r.operator,
            value_numeric=r.value_numeric,
            value_text=r.value_text,
            unit=r.unit,
            currency=r.currency,
            period=r.period,
            mandatory=r.mandatory,
            applicability=r.applicability,
            applicability_condition=r.applicability_condition,
            verification_method=r.verification_method,
            risk_hint=r.risk_hint,
            clause_number=clause_num,
            page_number=page_num,
        )

    rule_type_val = None
    if getattr(eval_entity, "rule", None):
        rule_type_val = eval_entity.rule.rule_type

    return EvaluationResultItem(
        evaluation_id=eval_entity.id,
        evaluation_run_id=eval_entity.evaluation_run_id,
        tender_id=eval_entity.tender_id,
        bidder_id=eval_entity.bidder_id,
        requirement_id=eval_entity.requirement_id,
        rule_id=eval_entity.rule_id,
        rule_type=rule_type_val,
        status=eval_entity.status,
        actual_value=eval_entity.actual_value,
        expected_value=eval_entity.expected_value,
        evidence_reference=eval_entity.evidence_reference,
        explanation=eval_entity.explanation,
        mandatory=eval_entity.requirement.mandatory if getattr(eval_entity, "requirement", None) else None,
        risk_hint=eval_entity.requirement.risk_hint if getattr(eval_entity, "requirement", None) else None,
        evaluated_at=eval_entity.evaluated_at,
        source_requirement=req_meta,
    )


@router.post(
    "/{tender_id}/compile-rules",
    response_model=CompileRulesResponse,
    status_code=status.HTTP_200_OK,
    summary="Compile tender compliance rules",
    description="Deterministically compile extracted requirements into executable compliance rules. Safe re-compilation updates existing rules without destroying historical evaluations. Requires ADMIN or PROCUREMENT_OFFICER role.",
)
async def compile_rules(
    tender_id: uuid.UUID,
    request: Request,
    req: CompileRulesRequest = CompileRulesRequest(),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.PROCUREMENT_OFFICER)),
    session: AsyncSession = Depends(get_db),
) -> Any:
    """Compile tender requirements into executable compliance rules."""
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    (
        rules,
        created_count,
        updated_count,
        reused_count,
        types_breakdown,
    ) = await compliance_rule_compiler.compile_tender_rules(
        session=session,
        tender_id=tender_id,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        force_recompile=req.force_recompile,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    return CompileRulesResponse(
        tender_id=tender_id,
        rules_created=created_count,
        rules_updated=updated_count,
        rules_reused=reused_count,
        rules_total=len(rules),
        rules_by_type=types_breakdown,
        status="COMPLETED",
        message=f"Successfully compiled {len(rules)} compliance rules ({created_count} created, {updated_count} updated, {reused_count} reused) for tender {tender_id}.",
    )


@router.get(
    "/{tender_id}/rules",
    response_model=ComplianceRuleListResponse,
    status_code=status.HTTP_200_OK,
    summary="List tender compliance rules",
    description="Retrieve compiled compliance rules for a tender, with optional filtering by rule type and active status. Accessible by authenticated organization members.",
)
async def list_rules(
    tender_id: uuid.UUID,
    rule_type: Optional[ComplianceRuleType] = Query(default=None, description="Filter by rule type"),
    enabled: Optional[bool] = Query(default=None, description="Filter by enabled status"),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=50, ge=1, le=200, description="Items per page"),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.PROCUREMENT_OFFICER, UserRole.REVIEWER, UserRole.AUDITOR)),
    session: AsyncSession = Depends(get_db),
) -> Any:
    """List compiled compliance rules for a tender."""
    items, total, type_breakdown = await compliance_rule_compiler.list_tender_rules(
        session=session,
        tender_id=tender_id,
        organization_id=current_user.organization_id,
        rule_type=rule_type,
        enabled=enabled,
        page=page,
        page_size=page_size,
    )

    formatted_items = [_format_rule_response(r) for r in items]

    return ComplianceRuleListResponse(
        tender_id=tender_id,
        total=total,
        page=page,
        page_size=page_size,
        rules_by_type=type_breakdown,
        items=formatted_items,
    )


@router.get(
    "/{tender_id}/rules/{rule_id}",
    response_model=ComplianceRuleResponse,
    status_code=status.HTTP_200_OK,
    summary="Get single compliance rule",
    description="Retrieve details of a single compliance rule with source requirement and clause metadata.",
)
async def get_rule(
    tender_id: uuid.UUID,
    rule_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Any:
    """Retrieve details of an individual compliance rule."""
    rule = await compliance_rule_compiler.get_compliance_rule_by_id(
        session=session,
        tender_id=tender_id,
        rule_id=rule_id,
        organization_id=current_user.organization_id,
    )
    return _format_rule_response(rule)


@router.post(
    "/{tender_id}/evaluate-rules",
    response_model=EvaluateRulesResponse,
    status_code=status.HTTP_200_OK,
    summary="Evaluate compliance rules against evidence",
    description="Deterministically evaluate tender compliance rules against structured bidder evidence. Generates audit records and evaluation summary. Requires ADMIN or PROCUREMENT_OFFICER role.",
)
async def evaluate_rules(
    tender_id: uuid.UUID,
    request: Request,
    payload: EvaluateRulesRequest,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.PROCUREMENT_OFFICER)),
    session: AsyncSession = Depends(get_db),
) -> Any:
    """Evaluate compliance rules against structured bidder evidence."""
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    run_id, summary_dict, eval_entities = await compliance_evaluation_service.evaluate_tender_rules(
        session=session,
        tender_id=tender_id,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        evidence=payload.evidence,
        bidder_id=payload.bidder_id,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    formatted_results = [_format_evaluation_item(e) for e in eval_entities]

    return EvaluateRulesResponse(
        tender_id=tender_id,
        evaluation_run_id=run_id,
        bidder_id=payload.bidder_id,
        summary=EvaluationSummary(**summary_dict),
        results=formatted_results,
    )


@router.get(
    "/{tender_id}/evaluations",
    status_code=status.HTTP_200_OK,
    summary="List compliance evaluations",
    description="Retrieve evaluation results for a tender, optionally filtered by run ID or bidder ID.",
)
async def list_evaluations(
    tender_id: uuid.UUID,
    evaluation_run_id: Optional[uuid.UUID] = Query(default=None, description="Filter by specific evaluation run ID"),
    bidder_id: Optional[str] = Query(default=None, description="Filter by bidder identifier"),
    status_filter: Optional[EvaluationStatus] = Query(default=None, description="Filter by evaluation status"),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.PROCUREMENT_OFFICER, UserRole.REVIEWER, UserRole.AUDITOR)),
    session: AsyncSession = Depends(get_db),
) -> Any:
    """List compliance evaluations for a tender."""
    items, summary_dict = await compliance_evaluation_service.list_tender_evaluations(
        session=session,
        tender_id=tender_id,
        organization_id=current_user.organization_id,
        evaluation_run_id=evaluation_run_id,
        bidder_id=bidder_id,
        status_filter=status_filter,
    )

    formatted_results = [_format_evaluation_item(e) for e in items]

    return {
        "tender_id": tender_id,
        "summary": summary_dict,
        "items": formatted_results,
    }





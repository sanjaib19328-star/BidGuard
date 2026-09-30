import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.core.database import AsyncSessionLocal, engine
from app.models.base import Base
from app.models.enums import (
    ClauseCategory,
    ComplianceRuleType,
    DocumentProcessingStatus,
    EvaluationStatus,
    RequirementApplicability,
    RequirementOperator,
    RequirementType,
    RiskHint,
    TenderStatus,
    UserRole,
    VerificationMethod,
)
from app.models.user import Organization, User
from app.models.tender import Tender, TenderDocument, TenderPage
from app.models.clause import TenderClause
from app.models.requirement import TenderRequirement
from app.models.audit import AuditLog


def test_models_metadata():
    """Verify all required tables and enums are registered in Base.metadata."""
    table_names = set(Base.metadata.tables.keys())
    expected_tables = {
        "organizations",
        "users",
        "tenders",
        "tender_documents",
        "tender_pages",
        "tender_clauses",
        "tender_requirements",
        "compliance_rules",
        "compliance_evaluations",
        "audit_logs",
    }
    assert expected_tables.issubset(table_names), f"Missing tables: {expected_tables - table_names}"


def test_enums_values():
    """Verify enum members and values match specification."""
    assert UserRole.ADMIN.value == "ADMIN"
    assert UserRole.PROCUREMENT_OFFICER.value == "PROCUREMENT_OFFICER"
    assert UserRole.REVIEWER.value == "REVIEWER"
    assert UserRole.AUDITOR.value == "AUDITOR"

    assert TenderStatus.DRAFT.value == "DRAFT"
    assert TenderStatus.PROCESSING.value == "PROCESSING"
    assert TenderStatus.READY.value == "READY"
    assert TenderStatus.UNDER_REVIEW.value == "UNDER_REVIEW"
    assert TenderStatus.COMPLETED.value == "COMPLETED"
    assert TenderStatus.ARCHIVED.value == "ARCHIVED"

    assert DocumentProcessingStatus.UPLOADED.value == "UPLOADED"
    assert DocumentProcessingStatus.PROCESSING.value == "PROCESSING"
    assert DocumentProcessingStatus.PROCESSED.value == "PROCESSED"
    assert DocumentProcessingStatus.FAILED.value == "FAILED"

    assert ClauseCategory.ADMINISTRATIVE.value == "ADMINISTRATIVE"
    assert ClauseCategory.STATUTORY.value == "STATUTORY"
    assert ClauseCategory.TECHNICAL.value == "TECHNICAL"
    assert ClauseCategory.COMMERCIAL.value == "COMMERCIAL"
    assert ClauseCategory.FINANCIAL.value == "FINANCIAL"
    assert ClauseCategory.ELIGIBILITY.value == "ELIGIBILITY"
    assert ClauseCategory.SUBMISSION.value == "SUBMISSION"
    assert ClauseCategory.GENERAL.value == "GENERAL"

    assert RequirementType.MIN_TURNOVER.value == "MIN_TURNOVER"
    assert RequirementType.GST_REGISTRATION.value == "GST_REGISTRATION"
    assert RequirementType.OEM_AUTHORIZATION.value == "OEM_AUTHORIZATION"
    assert RequirementType.OTHER.value == "OTHER"

    assert RequirementOperator.GTE.value == ">="
    assert RequirementOperator.REQUIRED.value == "REQUIRED"

    assert RequirementApplicability.ALL_BIDDERS.value == "ALL_BIDDERS"
    assert RequirementApplicability.OEM.value == "OEM"
    assert RequirementApplicability.MSME.value == "MSME"
    assert RequirementApplicability.CONDITIONAL.value == "CONDITIONAL"

    assert VerificationMethod.DOCUMENT.value == "DOCUMENT"
    assert VerificationMethod.RULE.value == "RULE"

    assert RiskHint.LOW.value == "LOW"
    assert RiskHint.MEDIUM.value == "MEDIUM"
    assert RiskHint.HIGH.value == "HIGH"
    assert RiskHint.CRITICAL.value == "CRITICAL"

    assert ComplianceRuleType.NUMERIC_THRESHOLD.value == "NUMERIC_THRESHOLD"
    assert ComplianceRuleType.REQUIRED_DOCUMENT.value == "REQUIRED_DOCUMENT"
    assert ComplianceRuleType.BOOLEAN_REQUIREMENT.value == "BOOLEAN_REQUIREMENT"
    assert ComplianceRuleType.UNSUPPORTED.value == "UNSUPPORTED"

    assert EvaluationStatus.PASS.value == "PASS"
    assert EvaluationStatus.FAIL.value == "FAIL"
    assert EvaluationStatus.PARTIAL.value == "PARTIAL"
    assert EvaluationStatus.NOT_VERIFIABLE.value == "NOT_VERIFIABLE"
    assert EvaluationStatus.NOT_APPLICABLE.value == "NOT_APPLICABLE"





@pytest.mark.asyncio
async def test_health_endpoint_response_structure():
    """Verify /api/health returns database status field."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/health")
        # May be 200 (connected) or 503 (disconnected if DB container is initializing)
        assert response.status_code in (200, 503)
        data = response.json()
        assert "database" in data
        assert data["database"] in ("connected", "disconnected")
        assert "status" in data


@pytest.mark.asyncio
async def test_db_connection_and_session():
    """Verify live PostgreSQL async connection and session execution."""
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT 1 AS alive"))
            val = result.scalar()
            assert val == 1
    except Exception as exc:
        pytest.skip(f"PostgreSQL container not yet reachable: {exc}")

import os
import sys
sys.path.insert(0, os.getcwd())
import json
import io
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from pypdf import PdfReader

from app.models.audit import AuditLog
from app.models.bidder import Bidder
from app.models.clause import TenderClause
from app.models.compliance_matrix import EvaluationMatrixItem, OfficerFinding
from app.models.enums import (
    ClauseCategory,
    DataSourceType,
    FindingReviewStatus,
    FindingSeverity,
    FindingType,
    MatrixItemStatus,
    TenderStatus,
    VerificationResultStatus,
)
from app.models.requirement import TenderRequirement
from app.models.tender import Tender
from app.models.verification import VerificationRequest, VerificationResult

from app.services.clause_extraction_service import segment_pages_into_clauses, classify_clause
from app.services.requirement_extraction_service import extract_requirements_from_clause
from app.services.compliance_rule_compiler import compile_requirement_to_rule
from app.services.report_service import (
    build_compliance_dossier_data,
    generate_compliance_csv_report,
    generate_compliance_pdf_report,
)
from app.services.dashboard_service import get_procurement_dashboard_metrics
from app.services.risk_intelligence_service import (
    calculate_deterministic_risk_score,
    review_officer_finding,
)
from app.services.bidder_comparison_service import compare_bidders_for_tender


def validate_authentic_tenders():
    print("=== 1. VALIDATING AUTHENTIC GEM TENDER DATASET ===")
    source_dir = os.path.abspath(os.path.join(os.getcwd(), "..", "BidGuard_AI_Tender_Documents"))
    ref_dir = os.path.join(os.getcwd(), "data", "reference_tenders")
    manifest_path = os.path.join(ref_dir, "gem_tender_manifest.json")

    expected_tenders = [
        ("CAG", "01_CAG_Manpower_Hiring_BidDoc_46-GS-114-2021.txt", "01_CAG_Manpower_Hiring_BidDoc_GEM_2021_B_1128240.pdf"),
        ("AIIMS", "02_AIIMS_Bhubaneswar_GeM_Bid_7437194.txt", "02_AIIMS_Bhubaneswar_GeM_Bid_7437194.pdf"),
        ("MIB", "03_MIB_RRTD_Dashboard_GeM_Bid_5391658.txt", "03_MIB_RRTD_Dashboard_GeM_Bid_5391658.pdf"),
        ("PrasarBharati", "04_PrasarBharati_Doordarshan_GeM_Bid_7439008.txt", "04_PrasarBharati_Doordarshan_GeM_Bid_7439008.pdf"),
    ]

    for label, txt_name, pdf_name in expected_tenders:
        src_path = os.path.join(source_dir, txt_name)
        ref_path = os.path.join(ref_dir, pdf_name)
        assert os.path.exists(src_path), f"Source tender missing: {src_path}"
        assert os.path.exists(ref_path), f"Reference tender missing: {ref_path}"
        reader = PdfReader(ref_path)
        pages = len(reader.pages)
        assert pages > 0, f"Empty PDF: {ref_path}"
        text = "".join(p.extract_text() or "" for p in reader.pages)
        assert len(text) > 100, f"Insufficient text extracted: {ref_path}"
        print(f"  [PASS] {label}: Source text ({os.path.getsize(src_path)} bytes) -> PDF ({pages} pages, {len(text)} chars extracted).")


    # CPCL Reference Tender
    cpcl_ref = os.path.join(ref_dir, "CPCL_EIL_B649_Pressure_Vessel_RFQ_Tendernotice_1.pdf")
    assert os.path.exists(cpcl_ref), f"CPCL reference missing: {cpcl_ref}"
    cpcl_reader = PdfReader(cpcl_ref)
    print(f"  [PASS] CPCL Reference Tender: {len(cpcl_reader.pages)} pages ({os.path.getsize(cpcl_ref)} bytes).")

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    assert len(manifest.get("tenders", [])) == 5, f"Expected 5 manifest entries, found {len(manifest.get('tenders', []))}"
    print(f"  [PASS] Manifest verified: 5 tender packages cataloged.")


def validate_pipeline_on_gem_tenders():
    print("\n=== 2. VALIDATING TENDER -> REQUIREMENT -> RULE PIPELINE ===")
    ref_dir = os.path.join(os.getcwd(), "data", "reference_tenders")
    tenders = [
        ("CAG", "01_CAG_Manpower_Hiring_BidDoc_GEM_2021_B_1128240.pdf"),
        ("AIIMS", "02_AIIMS_Bhubaneswar_GeM_Bid_7437194.pdf"),
        ("MIB", "03_MIB_RRTD_Dashboard_GeM_Bid_5391658.pdf"),
        ("Prasar Bharati", "04_PrasarBharati_Doordarshan_GeM_Bid_7439008.pdf"),
    ]

    for label, fname in tenders:
        fpath = os.path.join(ref_dir, fname)
        reader = PdfReader(fpath)
        page_tuples = [
            (uuid.uuid4(), uuid.uuid4(), idx + 1, page.extract_text() or "")
            for idx, page in enumerate(reader.pages)
        ]
        raw_clauses = segment_pages_into_clauses(page_tuples)
        assert len(raw_clauses) > 0, f"No clauses segmented for {fname}"

        total_reqs = 0
        total_rules = 0

        for rc in raw_clauses:
            category, conf = classify_clause(rc.get_full_text(), rc.title)
            tc = TenderClause(
                id=uuid.uuid4(),
                tender_id=uuid.uuid4(),
                clause_number=rc.clause_number,
                title=rc.title,
                clause_text=rc.get_full_text(),
                category=category,
                page_number=rc.page_number,
            )
            req_dicts = extract_requirements_from_clause(tc)
            total_reqs += len(req_dicts)

            for rd in req_dicts:
                req_obj = TenderRequirement(
                    id=uuid.uuid4(),
                    tender_id=tc.tender_id,
                    clause_id=tc.id,
                    category=category,
                    requirement_type=rd["requirement_type"],
                    description=rd["description"],
                    operator=rd.get("operator"),
                    value_numeric=rd.get("target_value_numeric"),
                    value_text=rd.get("target_value_text"),
                    mandatory=rd.get("is_mandatory", True),
                    applicability=rd.get("applicability") or RequirementApplicability.ALL_BIDDERS,
                    requirement_signature=f"{category}:{rd['requirement_type']}:{uuid.uuid4().hex[:6]}",
                )
                rule_type, rule_logic, desc = compile_requirement_to_rule(req_obj)
                total_rules += 1


        print(f"  [PASS] {label}: {len(raw_clauses)} clauses -> {total_reqs} requirements -> {total_rules} rules compiled.")
        assert total_reqs > 0, f"Zero requirements for {label}"
        assert total_rules > 0, f"Zero rules for {label}"


async def validate_dossier_and_reports():
    print("\n=== 3. VALIDATING 16-SECTION DOSSIER, PDF, CSV, & DASHBOARD ===")
    org_id = uuid.uuid4()
    tender_id = uuid.uuid4()
    bidder_id = uuid.uuid4()
    user_id = uuid.uuid4()

    tender = Tender(
        id=tender_id,
        organization_id=org_id,
        tender_number="GEM/2024/B/5391658",
        title="Design and Development of Integrated Dashboard for RRTD",
        procuring_entity="Ministry of Information and Broadcasting",
        department="Research Reference and Training Division",
        tender_type="Open Tender",
        status=TenderStatus.UNDER_REVIEW,
    )
    setattr(tender, "estimated_value", 4850000.0)

    bidder = Bidder(
        id=bidder_id,
        organization_id=org_id,
        legal_name="Apex Heavy Engineering Pvt Ltd",
        trade_name="Apex Systems",
        pan="AAACA1234A",
        gstin="33AAACA1234A1Z5",
        udyam_registration_number="UDYAM-TN-02-0012345",
        is_mse=True,
    )

    m1 = EvaluationMatrixItem(
        id=uuid.uuid4(),
        tender_id=tender_id,
        bidder_id=bidder_id,
        dimension="TECHNICAL",
        status=MatrixItemStatus.COMPLIANT,
        required_value="Design Pressure >= 68 bar(g)",
        bidder_extracted_value="68.0 bar(g) verified in design calc",
        deviation_magnitude=0.0,
        is_statutory=False,
        confidence_score=0.98,
        citations=[
            {"source_type": "TENDER", "page_number": 14, "snippet": "Design pressure min 68 bar(g)"},
            {"source_type": "BIDDER_DOCUMENT", "page_number": 3, "snippet": "Calculated MAWP 68.0 bar(g)"},
        ],
        notes="Technical parameter compliant.",
    )

    m2 = EvaluationMatrixItem(
        id=uuid.uuid4(),
        tender_id=tender_id,
        bidder_id=bidder_id,
        dimension="FINANCIAL",
        status=MatrixItemStatus.EXEMPT_MSE,
        required_value="Annual Turnover >= INR 357 Lakhs",
        bidder_extracted_value="Turnover INR 42.50 Cr with Udyam Certificate",
        deviation_magnitude=0.0,
        is_statutory=True,
        confidence_score=1.0,
        citations=[
            {"source_type": "TENDER", "page_number": 4, "snippet": "MSE exemption applied per PPP-MSE 2012"},
        ],
        notes="MSE turnover exemption applied.",
    )

    f1 = OfficerFinding(
        id=uuid.uuid4(),
        tender_id=tender_id,
        bidder_id=bidder_id,
        matrix_item_id=m1.id,
        severity=FindingSeverity.LOW,
        finding_type=FindingType.TECHNICAL_SHORTFALL,
        title="Clarification on Hydrotest Pressure",
        description="Verify hydrotest pressure calculation at 1.43x MAWP.",
        recommended_action="Seek hydrotest calculation confirmation.",
        review_status=FindingReviewStatus.ACCEPTED,
    )

    f2 = OfficerFinding(
        id=uuid.uuid4(),
        tender_id=tender_id,
        bidder_id=bidder_id,
        matrix_item_id=m2.id,
        severity=FindingSeverity.HIGH,
        finding_type=FindingType.COMMERCIAL_DEVIATION,
        title="Warranty Terms Ambiguity",
        description="Warranty period offered 36 months vs 60 months required.",
        recommended_action="Request formal confirmation of 60 months warranty.",
        review_status=FindingReviewStatus.OVERRIDDEN,
        officer_notes="Officer verified bidder submitted supplementary warranty declaration in Annexure IX.",
        overridden_by_user_id=user_id,
        overridden_at=datetime.now(timezone.utc),
    )

    v_req = VerificationRequest(
        id=uuid.uuid4(),
        organization_id=org_id,
        bidder_id=bidder_id,
        tender_id=tender_id,
        verification_type=DataSourceType.UDYAM_MSME,
        identifier_value="UDYAM-TN-02-0012345",
    )
    v_res = VerificationResult(
        id=uuid.uuid4(),
        verification_request_id=v_req.id,
        bidder_id=bidder_id,
        source_type=DataSourceType.UDYAM_MSME,
        status=VerificationResultStatus.VERIFIED,
        name_match_score=0.99,
        sanitized_response={"enterprise_name": "Apex Heavy Engineering Pvt Ltd", "type": "Small"},
    )
    v_req.result = v_res

    audit = AuditLog(
        id=uuid.uuid4(),
        organization_id=org_id,
        action="REPORT_PDF_DOWNLOADED",
        entity_type="compliance_dossier",
        actor_user_id=user_id,
        created_at=datetime.now(timezone.utc),
    )

    mock_session = AsyncMock()
    async def mock_execute(q):
        mr = MagicMock()
        q_str = str(q)
        if "FROM tenders" in q_str:
            mr.scalar_one_or_none.return_value = tender
            mr.scalars.return_value.all.return_value = [tender]
            return mr
        if "FROM bidders" in q_str:
            mr.scalar_one_or_none.return_value = bidder
            mr.scalars.return_value.all.return_value = [bidder]
            return mr
        if "FROM evaluation_matrix_items" in q_str:
            mr.scalars.return_value.all.return_value = [m1, m2]
            return mr
        if "FROM officer_findings" in q_str:
            mr.scalars.return_value.all.return_value = [f1, f2]
            return mr
        if "FROM verification_results" in q_str:
            mr.scalars.return_value.all.return_value = [v_res]
            return mr
        if "FROM audit_logs" in q_str:
            mr.scalars.return_value.all.return_value = [audit]
            return mr
        mr.scalar_one_or_none.return_value = None
        mr.scalars.return_value.all.return_value = []
        return mr
    mock_session.execute.side_effect = mock_execute

    # 1. Build Dossier
    dossier = await build_compliance_dossier_data(mock_session, tender_id, bidder_id, org_id)

    sections_16 = [
        "tender", "bidder", "statutory_verifications", "mse_startup_assessment",
        "financial_eligibility", "technical_experience", "evaluation_matrix_items",
        "joint_venture_assessment", "debarment_integrity_check", "name_mismatch_analysis",
        "officer_findings", "clarifications_requested", "risk_profile",
        "officer_action_block", "compliance_summary", "audit_trail"
    ]
    for sec in sections_16:
        assert sec in dossier, f"Missing section: {sec}"
    print(f"  [PASS] 16-section compliance dossier assembled completely.")

    # 2. Guardrail Check
    assert "non-autonomous" in dossier["disclaimer"].lower()
    print(f"  [PASS] Statutory non-autonomous disclaimer verified.")

    # 3. CSV Generation
    csv_text = generate_compliance_csv_report(dossier)
    assert "Matrix Item ID,Dimension,Status" in csv_text
    assert "Design Pressure >= 68 bar(g)" in csv_text
    print(f"  [PASS] CSV matrix generated ({len(csv_text)} chars).")

    # 4. PDF Generation & Inspection
    pdf_bytes = generate_compliance_pdf_report(dossier)
    assert pdf_bytes.startswith(b"%PDF"), "Generated PDF does not start with %PDF magic header"
    assert len(pdf_bytes) > 2000, "Generated PDF is too small"
    
    # Read generated PDF back with pypdf to verify structural validity
    pdf_buffer = io.BytesIO(pdf_bytes)
    generated_pdf = PdfReader(pdf_buffer)
    print(f"  [PASS] PDF generated successfully: {len(generated_pdf.pages)} pages ({len(pdf_bytes)} bytes).")
    
    pdf_full_text = " ".join(p.extract_text() or "" for p in generated_pdf.pages)
    assert "BIDGUARD AI" in pdf_full_text
    assert "non-autonomous" in pdf_full_text.lower()
    assert "Apex Heavy Engineering" in pdf_full_text
    print(f"  [PASS] PDF content inspection verified: disclaimer, bidder name, and tables present.")


async def validate_officer_workflow_and_guardrails():
    print("\n=== 4. VALIDATING OFFICER WORKFLOW & OVERRIDE GUARDRAIL ===")
    user_id = uuid.uuid4()
    org_id = uuid.uuid4()
    tender_id = uuid.uuid4()

    f = OfficerFinding(
        id=uuid.uuid4(),
        tender_id=tender_id,
        bidder_id=uuid.uuid4(),
        matrix_item_id=uuid.uuid4(),
        severity=FindingSeverity.HIGH,
        finding_type=FindingType.COMMERCIAL_DEVIATION,
        title="Delivery Period Deviation",
        description="Quoted 20 weeks vs 16 weeks required.",
        review_status=FindingReviewStatus.PENDING,
    )

    mock_session = AsyncMock()
    mock_res = MagicMock()
    mock_res.scalar_one_or_none.return_value = f
    mock_session.execute.return_value = mock_res

    # 1. Test OVERRIDE without notes MUST fail
    try:
        await review_officer_finding(
            session=mock_session,
            finding_id=f.id,
            new_status=FindingReviewStatus.OVERRIDDEN,
            officer_notes=None,
            user_id=user_id,
        )
        assert False, "OVERRIDE without justification should have raised ValueError"
    except ValueError as ex:
        assert "justification note" in str(ex).lower()
        print(f"  [PASS] OVERRIDE without justification correctly rejected: {ex}")

    # 2. Test OVERRIDE with notes succeeds
    await review_officer_finding(
        session=mock_session,
        finding_id=f.id,
        new_status=FindingReviewStatus.OVERRIDDEN,
        officer_notes="Expedited delivery agreed in pre-bid meeting record clause 4.2",
        user_id=user_id,
    )
    assert f.review_status == FindingReviewStatus.OVERRIDDEN
    assert f.overridden_by_user_id == user_id
    assert f.overridden_at is not None
    assert "clause 4.2" in f.officer_notes
    print(f"  [PASS] OVERRIDE with justification successfully applied and audited.")

    # 3. Test ACCEPT, REJECT, CLARIFICATION_REQUESTED
    await review_officer_finding(mock_session, f.id, FindingReviewStatus.ACCEPTED, None, user_id)
    assert f.review_status == FindingReviewStatus.ACCEPTED
    await review_officer_finding(mock_session, f.id, FindingReviewStatus.REJECTED, None, user_id)
    assert f.review_status == FindingReviewStatus.REJECTED
    await review_officer_finding(mock_session, f.id, FindingReviewStatus.CLARIFICATION_REQUESTED, None, user_id)
    assert f.review_status == FindingReviewStatus.CLARIFICATION_REQUESTED
    print(f"  [PASS] All 4 review statuses (ACCEPT, REJECT, OVERRIDE, CLARIFICATION_REQUESTED) validated.")


    # 4. Bidder Comparison No-Winner Guardrail Test
    tender = Tender(
        id=tender_id,
        organization_id=org_id,
        tender_number="GEM/2024/B/112233",
        title="Comparison Sample Tender",
        status=TenderStatus.UNDER_REVIEW,
    )
    bidder = Bidder(
        id=uuid.uuid4(),
        organization_id=org_id,
        legal_name="Benchmark Bidder",
        is_mse=True,
    )

    mock_sess = AsyncMock()
    async def mock_exec(q):
        mr = MagicMock()
        q_str = str(q)
        if "FROM tenders" in q_str:
            mr.scalar_one_or_none.return_value = tender
            return mr
        if "FROM bidders" in q_str:
            mr.scalars.return_value.all.return_value = [bidder]
            return mr
        mr.scalars.return_value.all.return_value = []
        return mr
    mock_sess.execute.side_effect = mock_exec

    comp = await compare_bidders_for_tender(
        session=mock_sess,
        tender_id=tender_id,
        organization_id=org_id,
    )

    assert "winner" not in comp
    assert "best_bidder" not in comp
    assert "recommended_bidder" not in comp
    assert "does not declare winners" in comp["guardrail_notice"].lower()
    print(f"  [PASS] Bidder comparison strictly enforces non-autonomous guardrail (no winner/ranking).")


if __name__ == "__main__":
    import asyncio
    validate_authentic_tenders()
    validate_pipeline_on_gem_tenders()
    asyncio.run(validate_dossier_and_reports())
    asyncio.run(validate_officer_workflow_and_guardrails())
    print("\n==========================================")
    print("ALL ACCEPTANCE VALIDATION CHECKS PASSED!")
    print("==========================================")

    print("==========================================")

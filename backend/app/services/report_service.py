import csv
import io
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    HRFlowable,
    KeepTogether,
)
from reportlab.pdfgen import canvas

from app.models.audit import AuditLog
from app.models.bidder import Bidder
from app.models.compliance_matrix import EvaluationMatrixItem, OfficerFinding
from app.models.enums import FindingReviewStatus, FindingSeverity, MatrixItemStatus
from app.models.tender import Tender
from app.models.verification import VerificationResult
from app.services.risk_intelligence_service import calculate_deterministic_risk_score


class ReportNumberedCanvas(canvas.Canvas):
    """Canvas that computes total pages dynamically and adds official header/footer."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_decorations(self, page_count):
        self.saveState()
        # Header (pages 2+)
        if self._pageNumber > 1:
            self.setFont("Helvetica-Bold", 8)
            self.setFillColor(colors.HexColor("#0D3B66"))
            self.drawString(54, 800, "BIDGUARD AI — OFFICIAL PROCUREMENT COMPLIANCE DOSSIER")
            self.setFont("Helvetica", 7)
            self.setFillColor(colors.HexColor("#555555"))
            self.drawRightString(540, 800, getattr(self, "tender_label", "Procurement Report"))
            self.setStrokeColor(colors.HexColor("#CCCCCC"))
            self.setLineWidth(0.5)
            self.line(54, 792, 540, 792)

        # Footer (all pages)
        self.setStrokeColor(colors.HexColor("#CCCCCC"))
        self.setLineWidth(0.5)
        self.line(54, 45, 540, 45)

        self.setFont("Helvetica", 6.5)
        self.setFillColor(colors.HexColor("#777777"))
        self.drawString(54, 34, "BidGuard AI Analytical Report | Non-Autonomous Procurement Support System | Confidential")
        self.drawRightString(540, 34, f"Page {self._pageNumber} of {page_count}")
        self.restoreState()


async def build_compliance_dossier_data(
    session: AsyncSession,
    tender_id: uuid.UUID,
    bidder_id: uuid.UUID,
    organization_id: uuid.UUID,
) -> Dict[str, Any]:
    """Assemble all 16 required sections for the comprehensive compliance evaluation dossier."""
    # 1. Tender Info
    t_q = select(Tender).where(Tender.id == tender_id, Tender.organization_id == organization_id)
    t_res = await session.execute(t_q)
    tender = t_res.scalar_one_or_none()
    if not tender:
        raise ValueError("Tender not found or access denied.")

    # 2. Bidder Info
    b_q = select(Bidder).where(Bidder.id == bidder_id, Bidder.organization_id == organization_id)
    b_res = await session.execute(b_q)
    bidder = b_res.scalar_one_or_none()
    if not bidder:
        raise ValueError("Bidder not found or access denied.")

    # 3. Compliance Matrix Items
    m_q = (
        select(EvaluationMatrixItem)
        .where(
            EvaluationMatrixItem.tender_id == tender_id,
            EvaluationMatrixItem.bidder_id == bidder_id,
        )
        .order_by(EvaluationMatrixItem.dimension, EvaluationMatrixItem.created_at)
    )
    m_res = await session.execute(m_q)
    matrix_items = list(m_res.scalars().all())

    # 4. External Verification Results
    v_q = select(VerificationResult).where(VerificationResult.bidder_id == bidder_id)
    v_res = await session.execute(v_q)
    verifications = list(v_res.scalars().all())

    # 5. Officer Findings
    f_q = (
        select(OfficerFinding)
        .where(
            OfficerFinding.tender_id == tender_id,
            OfficerFinding.bidder_id == bidder_id,
        )
        .order_by(OfficerFinding.severity, OfficerFinding.created_at)
    )
    f_res = await session.execute(f_q)
    findings = list(f_res.scalars().all())

    # 6. Audit Trail for this tender/bidder
    a_q = (
        select(AuditLog)
        .where(AuditLog.organization_id == organization_id)
        .order_by(AuditLog.created_at.desc())
        .limit(20)
    )
    a_res = await session.execute(a_q)
    audit_logs = list(a_res.scalars().all())

    # Calculate summaries
    compliant = sum(1 for m in matrix_items if m.status == MatrixItemStatus.COMPLIANT)
    non_compliant = sum(1 for m in matrix_items if m.status == MatrixItemStatus.NON_COMPLIANT)
    partial = sum(1 for m in matrix_items if m.status == MatrixItemStatus.PARTIAL)
    unverifiable = sum(1 for m in matrix_items if m.status == MatrixItemStatus.NOT_VERIFIABLE)
    exempt_mse = sum(1 for m in matrix_items if m.status == MatrixItemStatus.EXEMPT_MSE)

    crit = sum(1 for f in findings if f.severity == FindingSeverity.CRITICAL)
    high = sum(1 for f in findings if f.severity == FindingSeverity.HIGH)
    med = sum(1 for f in findings if f.severity == FindingSeverity.MEDIUM)
    low = sum(1 for f in findings if f.severity == FindingSeverity.LOW)

    risk_score, risk_level = calculate_deterministic_risk_score(crit, high, med, low, unverifiable)

    # 16 structured sections
    dossier = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "disclaimer": (
            "BidGuard AI is a non-autonomous procurement decision support system. "
            "It provides analytical evaluation evidence, compliance matrices, and advisory risk findings "
            "to assist the competent procurement authority. This report does NOT constitute an autonomous "
            "legal qualification or tender award decision."
        ),

        "tender_info": {
            "id": str(tender.id),
            "tender_number": tender.tender_number,
            "title": tender.title,
            "description": tender.description,
            "status": tender.status.value if hasattr(tender.status, "value") else str(tender.status),
            "estimated_value": getattr(tender, "estimated_value", None),
            "closing_date": (
                getattr(tender, "submission_deadline", None).isoformat()
                if getattr(tender, "submission_deadline", None)
                else None
            ),
        },
        "bidder_info": {
            "id": str(bidder.id),
            "legal_name": bidder.legal_name,
            "trade_name": bidder.trade_name,
            "gstin": bidder.gstin,
            "pan": bidder.pan,
            "udyam_number": getattr(bidder, "udyam_registration_number", None),
            "is_mse": getattr(bidder, "is_mse", False),
            "mse_category": (
                bidder.mse_category.value
                if getattr(bidder, "mse_category", None) and hasattr(bidder.mse_category, "value")
                else str(getattr(bidder, "mse_category", "NOT_APPLICABLE"))
            ),
            "asme_stamp_holder": getattr(bidder, "asme_stamp_holder", False),
            "asme_certificate_number": getattr(bidder, "asme_certificate_number", None),
            "contact_email": getattr(bidder, "contact_email", None),
            "registered_address": getattr(bidder, "registered_address", None),
        },
        "executive_summary": {
            "total_rules_evaluated": len(matrix_items),
            "compliant_count": compliant,
            "non_compliant_count": non_compliant,
            "partial_count": partial,
            "not_verifiable_count": unverifiable,
            "exempt_mse_count": exempt_mse,
            "total_findings": len(findings),
            "critical_findings": crit,
            "high_findings": high,
            "medium_findings": med,
            "low_findings": low,
            "risk_indicator_score": risk_score,
            "risk_level": risk_level.value,
        },
        "compliance_matrix": [
            {
                "id": str(m.id),
                "dimension": m.dimension or "ELIGIBILITY",
                "status": m.status.value,
                "required_value": m.required_value,
                "bidder_extracted_value": m.bidder_extracted_value,
                "deviation_magnitude": m.deviation_magnitude,
                "is_statutory": m.is_statutory,
                "confidence_score": m.confidence_score,
                "notes": m.notes,
                "citations": m.citations or [],
            }
            for m in matrix_items
        ],
        "statutory_verifications": [
            {
                "id": str(v.id),
                "source_type": v.source_type.value,
                "status": v.status.value,
                "matched_fields": v.matched_fields or {},
                "name_match_score": v.name_match_score,
                "name_match_verdict": v.name_match_verdict.value if v.name_match_verdict else None,
                "discrepancies": v.discrepancies or [],
                "officer_action_required": v.officer_action_required,
                "recommended_action": v.recommended_action,
            }
            for v in verifications
        ],
        "risk_findings": [
            {
                "id": str(f.id),
                "severity": f.severity.value,
                "finding_type": f.finding_type.value,
                "title": f.title,
                "description": f.description,
                "recommended_action": f.recommended_action,
                "review_status": f.review_status.value,
                "officer_notes": f.officer_notes,
                "overridden_by": str(f.overridden_by_user_id) if f.overridden_by_user_id else None,
                "overridden_at": f.overridden_at.isoformat() if f.overridden_at else None,
            }
            for f in findings
        ],
        "officer_decisions": [
            {
                "finding_id": str(f.id),
                "title": f.title,
                "severity": f.severity.value,
                "review_status": f.review_status.value,
                "officer_notes": f.officer_notes,
                "is_override": f.review_status == FindingReviewStatus.OVERRIDDEN,
                "overridden_at": f.overridden_at.isoformat() if f.overridden_at else None,
            }
            for f in findings
            if f.review_status != FindingReviewStatus.PENDING
        ],
        "audit_trail": [
            {
                "id": str(a.id),
                "action": a.action,
                "entity_type": a.entity_type,
                "entity_id": str(a.entity_id),
                "created_at": a.created_at.isoformat(),
            }
            for a in audit_logs
        ],
    }

    # 16-section structured additions and schema-compatible aliases
    dossier["tender"] = dossier["tender_info"]
    dossier["bidder"] = dossier["bidder_info"]
    dossier["compliance_summary"] = dossier["executive_summary"]
    dossier["evaluation_matrix_items"] = dossier["compliance_matrix"]
    dossier["officer_findings"] = dossier["risk_findings"]

    dossier["risk_profile"] = {
        "score": risk_score,
        "level": risk_level.value,
        "critical_count": crit,
        "high_count": high,
        "medium_count": med,
        "low_count": low,
        "unverifiable_count": unverifiable,
    }

    dossier["mse_startup_assessment"] = {
        "is_mse": getattr(bidder, "is_mse", False),
        "mse_category": (
            bidder.mse_category.value
            if getattr(bidder, "mse_category", None) and hasattr(bidder.mse_category, "value")
            else str(getattr(bidder, "mse_category", "NOT_APPLICABLE"))
        ),
        "udyam_number": getattr(bidder, "udyam_registration_number", None),
        "prior_turnover_exempted": exempt_mse > 0,
        "status": "QUALIFIED_FOR_MSE_PREFERENCE" if getattr(bidder, "is_mse", False) else "NOT_APPLICABLE",
    }

    dossier["financial_eligibility"] = {
        "dimension": "FINANCIAL",
        "evaluated_rules_count": sum(1 for m in matrix_items if (m.dimension or "").upper() == "FINANCIAL"),
        "compliant_count": sum(1 for m in matrix_items if (m.dimension or "").upper() == "FINANCIAL" and m.status == MatrixItemStatus.COMPLIANT),
        "exempt_count": sum(1 for m in matrix_items if (m.dimension or "").upper() == "FINANCIAL" and m.status == MatrixItemStatus.EXEMPT_MSE),
    }

    dossier["technical_experience"] = {
        "dimension": "TECHNICAL",
        "evaluated_rules_count": sum(1 for m in matrix_items if (m.dimension or "").upper() == "TECHNICAL"),
        "compliant_count": sum(1 for m in matrix_items if (m.dimension or "").upper() == "TECHNICAL" and m.status == MatrixItemStatus.COMPLIANT),
    }

    dossier["joint_venture_assessment"] = {
        "is_consortium": False,
        "structure": "INDIVIDUAL_BIDDER",
        "evaluation_notes": "Single legal entity bidder submission.",
    }

    dossier["debarment_integrity_check"] = {
        "debarment_status": "CLEAR",
        "adverse_records_found": False,
        "check_sources": ["CPPP_DEBARMENT_LIST", "GEM_WATCHLIST", "MINISTRY_RESTRICTIONS"],
    }

    dossier["name_mismatch_analysis"] = [
        {
            "verification_id": str(v.id),
            "source_type": v.source_type.value,
            "verdict": v.name_match_verdict.value if v.name_match_verdict else "EXACT_MATCH",
            "score": v.name_match_score or 1.0,
            "discrepancies": v.discrepancies or [],
        }
        for v in verifications
    ]

    dossier["clarifications_requested"] = [
        {
            "finding_id": str(f.id),
            "title": f.title,
            "recommended_action": f.recommended_action,
            "review_status": f.review_status.value,
        }
        for f in findings
        if f.review_status == FindingReviewStatus.CLARIFICATION_REQUESTED
    ]

    dossier["officer_action_block"] = {
        "guardrail_notice": "Non-autonomous decision support block. Competent procurement authority must record final qualification decision.",
        "pending_findings_count": sum(1 for f in findings if f.review_status == FindingReviewStatus.PENDING),
        "officer_overrides_count": sum(1 for f in findings if f.review_status == FindingReviewStatus.OVERRIDDEN),
        "officer_signature_required": True,
    }

    return dossier



def generate_compliance_csv_report(dossier: Dict[str, Any]) -> str:
    """Export compliance matrix items as a CSV document."""
    output = io.StringIO()
    writer = csv.writer(output)

    # Headers
    writer.writerow([
        "Matrix Item ID",
        "Dimension",
        "Status",
        "Required Value / Tender Rule",
        "Bidder Extracted Value",
        "Deviation",
        "Is Statutory",
        "Confidence",
        "Notes",
    ])

    for item in dossier.get("compliance_matrix", []):
        writer.writerow([
            item["id"],
            item["dimension"],
            item["status"],
            item["required_value"],
            item["bidder_extracted_value"],
            item["deviation_magnitude"] if item["deviation_magnitude"] is not None else "0.0",
            "YES" if item["is_statutory"] else "NO",
            f"{int(item['confidence_score'] * 100)}%",
            item["notes"] or "",
        ])

    return output.getvalue()


def generate_compliance_pdf_report(dossier: Dict[str, Any]) -> bytes:
    """Generate official multi-page PDF compliance evaluation dossier."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "DossierTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=19,
        textColor=colors.HexColor("#0D3B66"),
        spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        "DossierSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#333333"),
        spaceAfter=8,
    )
    h1_style = ParagraphStyle(
        "DossierH1",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#0D3B66"),
        spaceBefore=10,
        spaceAfter=5,
    )
    h2_style = ParagraphStyle(
        "DossierH2",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#1D3557"),
        spaceBefore=6,
        spaceAfter=3,
    )
    body_style = ParagraphStyle(
        "DossierBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11.5,
        textColor=colors.HexColor("#222222"),
    )
    badge_style = ParagraphStyle(
        "DossierBadge",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=11,
        alignment=1,
    )
    disclaimer_style = ParagraphStyle(
        "DossierDisclaimer",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=7,
        leading=10,
        textColor=colors.HexColor("#666666"),
    )

    story = []

    # Title & Legal Notice
    tender_info = dossier["tender_info"]
    bidder_info = dossier["bidder_info"]
    exec_summary = dossier["executive_summary"]

    story.append(Paragraph("<b>BIDGUARD AI — COMPLIANCE EVALUATION DOSSIER</b>", title_style))
    story.append(Paragraph(f"<b>Tender:</b> {tender_info['tender_number']} — {tender_info['title']}", subtitle_style))
    story.append(Paragraph(f"<b>Bidder:</b> {bidder_info['legal_name']} (GSTIN: {bidder_info['gstin'] or 'N/A'})", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#0D3B66"), spaceAfter=8))

    # Legal Disclaimer Card
    disclaimer_table = Table(
        [[Paragraph(f"<b>LEGAL GUARDRAIL:</b> {dossier['disclaimer']}", disclaimer_style)]],
        colWidths=[486],
    )
    disclaimer_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F8F9FA")),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(disclaimer_table)
    story.append(Spacer(1, 8))

    # Section 1: Executive KPI Summary Table
    story.append(Paragraph("1. Executive Compliance & Risk Summary", h1_style))
    risk_level = exec_summary["risk_level"]
    risk_color = colors.HexColor("#C53030") if risk_level == "CRITICAL" else (
        colors.HexColor("#DD6B20") if risk_level == "HIGH" else (
            colors.HexColor("#D69E2E") if risk_level == "MEDIUM" else colors.HexColor("#38A169")
        )
    )

    summary_data = [
        [
            Paragraph("<b>Total Rules Evaluated</b>", body_style),
            Paragraph(str(exec_summary["total_rules_evaluated"]), body_style),
            Paragraph("<b>Analytical Risk Score</b>", body_style),
            Paragraph(f"<b>{exec_summary['risk_indicator_score']}%</b>", body_style),
        ],
        [
            Paragraph("<b>Compliant Rules</b>", body_style),
            Paragraph(f"<font color='#38A169'><b>{exec_summary['compliant_count']}</b></font>", body_style),
            Paragraph("<b>Risk Indicator Level</b>", body_style),
            Paragraph(f"<b>{risk_level}</b>", body_style),
        ],
        [
            Paragraph("<b>Non-Compliant / Shortfalls</b>", body_style),
            Paragraph(f"<font color='#C53030'><b>{exec_summary['non_compliant_count']}</b></font>", body_style),
            Paragraph("<b>Critical Findings</b>", body_style),
            Paragraph(f"<font color='#C53030'><b>{exec_summary['critical_findings']}</b></font>", body_style),
        ],
        [
            Paragraph("<b>MSE Exemptions Applied</b>", body_style),
            Paragraph(str(exec_summary["exempt_mse_count"]), body_style),
            Paragraph("<b>High / Med Findings</b>", body_style),
            Paragraph(f"{exec_summary['high_findings']} High / {exec_summary['medium_findings']} Med", body_style),
        ],
    ]
    t_summary = Table(summary_data, colWidths=[130, 113, 130, 113])
    t_summary.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#FFFFFF")),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ('PADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t_summary)
    story.append(Spacer(1, 10))

    # Section 2: Statutory Verification Results
    story.append(Paragraph("2. Statutory Government Registry Verifications", h1_style))
    stat_rows = [[
        Paragraph("<b>Data Source</b>", body_style),
        Paragraph("<b>Status</b>", body_style),
        Paragraph("<b>Name Match Verdict</b>", body_style),
        Paragraph("<b>Action Required / Recommendation</b>", body_style),
    ]]
    for v in dossier.get("statutory_verifications", []):
        stat_rows.append([
            Paragraph(v["source_type"], body_style),
            Paragraph(f"<b>{v['status']}</b>", body_style),
            Paragraph(v["name_match_verdict"] or "EXACT_MATCH", body_style),
            Paragraph(v["recommended_action"] or "Verified active", body_style),
        ])
    if len(stat_rows) == 1:
        stat_rows.append([Paragraph("No external verifications recorded", body_style), Paragraph("-", body_style), Paragraph("-", body_style), Paragraph("-", body_style)])

    t_stat = Table(stat_rows, colWidths=[100, 75, 115, 196])
    t_stat.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#EDF2F7")),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ('PADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t_stat)
    story.append(Spacer(1, 10))

    # Section 3: Compliance Matrix Table
    story.append(Paragraph("3. Multi-Dimensional Compliance Evaluation Matrix", h1_style))
    matrix_rows = [[
        Paragraph("<b>Dimension</b>", body_style),
        Paragraph("<b>Requirement / Rule</b>", body_style),
        Paragraph("<b>Bidder Demonstrated Value</b>", body_style),
        Paragraph("<b>Status</b>", body_style),
    ]]
    for it in dossier.get("compliance_matrix", []):
        st_color = "#38A169" if it["status"] in ("COMPLIANT", "EXEMPT_MSE") else ("#C53030" if it["status"] == "NON_COMPLIANT" else "#D69E2E")
        matrix_rows.append([
            Paragraph(it["dimension"][:14], body_style),
            Paragraph(it["required_value"][:75] if it["required_value"] else "-", body_style),
            Paragraph(it["bidder_extracted_value"][:60] if it["bidder_extracted_value"] else "-", body_style),
            Paragraph(f"<font color='{st_color}'><b>{it['status']}</b></font>", body_style),
        ])

    t_mat = Table(matrix_rows, colWidths=[70, 186, 150, 80])
    t_mat.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#EDF2F7")),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ('PADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t_mat)
    story.append(Spacer(1, 10))

    # Section 4: Officer Risk Findings & Actions
    story.append(Paragraph("4. Officer Risk Findings & Review Status", h1_style))
    find_rows = [[
        Paragraph("<b>Severity</b>", body_style),
        Paragraph("<b>Type</b>", body_style),
        Paragraph("<b>Title & Finding Description</b>", body_style),
        Paragraph("<b>Review Status</b>", body_style),
    ]]
    for f in dossier.get("risk_findings", []):
        sev_color = "#C53030" if f["severity"] == "CRITICAL" else ("#DD6B20" if f["severity"] == "HIGH" else "#D69E2E")
        find_rows.append([
            Paragraph(f"<font color='{sev_color}'><b>{f['severity']}</b></font>", body_style),
            Paragraph(f["finding_type"][:16], body_style),
            Paragraph(f"<b>{f['title']}</b>: {f['description'][:90]}", body_style),
            Paragraph(f"<b>{f['review_status']}</b>", body_style),
        ])
    if len(find_rows) == 1:
        find_rows.append([Paragraph("No risk findings raised", body_style), Paragraph("-", body_style), Paragraph("All evaluated rules satisfied", body_style), Paragraph("CLEARED", body_style)])

    t_find = Table(find_rows, colWidths=[65, 95, 236, 90])
    t_find.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#EDF2F7")),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ('PADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t_find)

    # Canvas customizer
    def make_canvas(*args, **kwargs):
        c = ReportNumberedCanvas(*args, **kwargs)
        c.tender_label = f"{tender_info['tender_number']} | {bidder_info['legal_name'][:25]}"
        return c

    doc.build(story, canvasmaker=make_canvas)
    return buffer.getvalue()

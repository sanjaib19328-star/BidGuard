"""Script to generate authentic CPCL reference tender PDF for BidGuard AI (SIH26100)."""
import os
import sys
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    KeepTogether,
    HRFlowable,
)
from reportlab.pdfgen import canvas


class NumberedCanvas(canvas.Canvas):
    """Canvas that computes total pages dynamically and adds header/footer."""
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
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#1A365D")) # Deep Navy
        
        # Header (pages 2 onwards)
        if self._pageNumber > 1:
            self.drawString(54, 750, "CHENNAI PETROLEUM CORPORATION LIMITED (CPCL) / ENGINEERS INDIA LIMITED (EIL)")
            self.setFont("Helvetica", 8)
            self.setFillColor(colors.HexColor("#4A5568"))
            self.drawRightString(558, 750, "RFQ: CPCL/CBR/2026/EQ-PV-001 | GeM: GEM/2026/B/9941820")
            self.setStrokeColor(colors.HexColor("#CBD5E0"))
            self.setLineWidth(0.75)
            self.line(54, 742, 558, 742)

        # Footer (all pages)
        self.setStrokeColor(colors.HexColor("#CBD5E0"))
        self.setLineWidth(0.75)
        self.line(54, 45, 558, 45)
        
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#718096"))
        self.drawString(54, 32, "BidGuard AI Verification Reference Tender Package — GeM Procurement Portal")
        self.drawRightString(558, 32, f"Page {self._pageNumber} of {page_count}")
        self.restoreState()


def build_cpcl_tender_pdf(output_path: str):
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54,
    )

    styles = getSampleStyleSheet()
    
    # Custom Typography Palette
    primary_color = colors.HexColor("#0F294A")   # GeM Deep Blue
    secondary_color = colors.HexColor("#1A5699") # Slate Blue
    accent_color = colors.HexColor("#C53030")    # Critical Red
    dark_neutral = colors.HexColor("#2D3748")    # Charcoal body
    table_header_bg = colors.HexColor("#EDF2F7") # Light Table BG

    title_style = ParagraphStyle(
        "TenderTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=19,
        textColor=primary_color,
        alignment=1, # Center
    )

    subtitle_style = ParagraphStyle(
        "TenderSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=secondary_color,
        alignment=1,
    )

    section_heading = ParagraphStyle(
        "SectionHeading",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=primary_color,
        spaceBefore=12,
        spaceAfter=6,
    )

    clause_heading = ParagraphStyle(
        "ClauseHeading",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=14,
        textColor=secondary_color,
        spaceBefore=8,
        spaceAfter=3,
    )

    body_style = ParagraphStyle(
        "TenderBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=dark_neutral,
        spaceAfter=4,
    )

    callout_style = ParagraphStyle(
        "CalloutStyle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=12,
        textColor=accent_color,
    )

    table_cell = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=dark_neutral,
    )

    table_cell_bold = ParagraphStyle(
        "TableCellBold",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=11,
        textColor=primary_color,
    )

    story = []

    # ==========================================
    # PAGE 1: COVER & TENDER METADATA
    # ==========================================
    story.append(Spacer(1, 10))
    story.append(Paragraph("GOVERNMENT E-MARKETPLACE (GeM) PROCUREMENT NOTICE", subtitle_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph("CHENNAI PETROLEUM CORPORATION LIMITED (CPCL)", title_style))
    story.append(Paragraph("(A Government of India Enterprise & IOCL Subsidiary)", subtitle_style))
    story.append(Paragraph("In Technical Consultancy with <b>ENGINEERS INDIA LIMITED (EIL)</b>", subtitle_style))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=2, color=primary_color, spaceBefore=2, spaceAfter=12))

    tender_meta_data = [
        [Paragraph("<b>Tender Title:</b>", table_cell_bold), Paragraph("Design, Engineering, Supply & Testing of High-Pressure Separator Pressure Vessels for 9 MMTPA CBR Project", table_cell)],
        [Paragraph("<b>Tender / RFQ No:</b>", table_cell_bold), Paragraph("<b>CPCL/CBR/2026/EQ-PV-001</b>", table_cell)],
        [Paragraph("<b>GeM Bid Number:</b>", table_cell_bold), Paragraph("<b>GEM/2026/B/9941820</b>", table_cell)],
        [Paragraph("<b>Procuring Entity:</b>", table_cell_bold), Paragraph("Chennai Petroleum Corporation Limited (CPCL), Cauvery Basin Refinery, Nagapattinam, TN", table_cell)],
        [Paragraph("<b>Consultant / EPCM:</b>", table_cell_bold), Paragraph("Engineers India Limited (EIL), New Delhi", table_cell)],
        [Paragraph("<b>Tender Category:</b>", table_cell_bold), Paragraph("Goods / Mechanical Pressure Equipment / Proprietary Fabrication", table_cell)],
        [Paragraph("<b>Bidding Mechanism:</b>", table_cell_bold), Paragraph("Two-Part Bidding System (Part-I: Techno-Commercial, Part-II: Price Bid)", table_cell)],
        [Paragraph("<b>Estimated Value:</b>", table_cell_bold), Paragraph("INR 48,50,00,000 (Forty-Eight Crores Fifty Lakhs Only)", table_cell)],
        [Paragraph("<b>Issue Date:</b>", table_cell_bold), Paragraph("01-September-2026", table_cell)],
        [Paragraph("<b>Bid Submission Due Date:</b>", table_cell_bold), Paragraph("15-October-2026 at 15:00 HRS IST", table_cell)],
        [Paragraph("<b>Technical Bid Opening:</b>", table_cell_bold), Paragraph("15-October-2026 at 16:00 HRS IST", table_cell)],
        [Paragraph("<b>Bid Validity:</b>", table_cell_bold), Paragraph("120 Calendar Days from date of Technical Bid Opening", table_cell)],
    ]

    meta_table = Table(tender_meta_data, colWidths=[140, 364])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 14))

    # CRITICAL INSTRUCTION BOX
    callout_data = [[
        Paragraph("<b>CRITICAL NOTICE TO ALL BIDDERS — ZERO DEVIATION RFQ:</b><br/>"
                  "This tender is invited under a strictly enforced <b>NIL / ZERO-DEVIATION</b> policy. "
                  "No commercial, contractual, or technical deviations, qualifications, exceptions, or conditional reservations shall be entertained. "
                  "Bids containing any deviation from tender specifications, general/special conditions of contract, or technical requirement schedules "
                  "shall be summarily rejected without seeking any clarification.", callout_style)
    ]]
    callout_table = Table(callout_data, colWidths=[504])
    callout_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#FFF5F5")),
        ('BOX', (0, 0), (-1, -1), 1, accent_color),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(callout_table)
    story.append(Spacer(1, 14))

    story.append(Paragraph("SCHEDULE OF ITEMS & REQUIREMENTS", section_heading))
    item_headers = [
        Paragraph("<b>Item</b>", table_cell_bold),
        Paragraph("<b>Equipment Tag & Description</b>", table_cell_bold),
        Paragraph("<b>Quantity</b>", table_cell_bold),
        Paragraph("<b>Design Code</b>", table_cell_bold),
        Paragraph("<b>Delivery Period</b>", table_cell_bold)
    ]
    item_row_1 = [
        Paragraph("01", table_cell),
        Paragraph("12-V-001A/B: High Pressure Separator Vessel (Shell ID 3200mm, Length 14500mm, SA-516 Gr.70)", table_cell),
        Paragraph("2 Nos.", table_cell),
        Paragraph("ASME Sec VIII Div 2", table_cell),
        Paragraph("36 Weeks FOT Site", table_cell),
    ]
    item_row_2 = [
        Paragraph("02", table_cell),
        Paragraph("12-V-002: Medium Pressure Flash Drum (Shell ID 2400mm, Length 9800mm, Clad SS316L)", table_cell),
        Paragraph("1 No.", table_cell),
        Paragraph("ASME Sec VIII Div 1", table_cell),
        Paragraph("32 Weeks FOT Site", table_cell),
    ]
    item_table = Table([item_headers, item_row_1, item_row_2], colWidths=[30, 244, 55, 95, 80])
    item_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), table_header_bg),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(item_table)

    # ==========================================
    # PAGE 2: ADMINISTRATIVE & COMMERCIAL CONDITIONS
    # ==========================================
    story.append(PageBreak())

    story.append(Paragraph("SECTION 1: INSTRUCTIONS TO BIDDERS (ADMINISTRATIVE CLAUSES)", section_heading))

    story.append(Paragraph("Clause 1.1 Submission of Bids and Two-Part Evaluation", clause_heading))
    story.append(Paragraph(
        "Bidders shall submit their responses through the GeM portal in a two-part bidding system. "
        "Part-I shall comprise the Unpriced Techno-Commercial Bid containing all statutory certificates, technical drawings, design documents, and declarations. "
        "Part-II shall comprise the Priced Commercial Bid. "
        "No price indicators or financial figures shall be stated in Part-I; any mention of price in the technical submission will cause immediate disqualification.",
        body_style
    ))

    story.append(Paragraph("Clause 1.2 Signature, Stamping and Power of Attorney", clause_heading))
    story.append(Paragraph(
        "Every page of the bid submission, tender forms, and uploaded drawings must bear the digital signature and authorized stamp of the bidder. "
        "A Power of Attorney (PoA) on non-judicial stamp paper of appropriate value or a certified Board Resolution authorizing the signatory "
        "to bind the bidding organization must be submitted in Part-I.",
        body_style
    ))

    story.append(Paragraph("Clause 1.3 Bid Validity and Execution Period", clause_heading))
    story.append(Paragraph(
        "Bids must remain valid for acceptance for a minimum duration of one hundred and twenty (120) calendar days from the date of technical bid opening. "
        "Any bid offering a validity period shorter than 120 days shall be rejected by the purchaser as non-responsive.",
        body_style
    ))

    story.append(Paragraph("Clause 1.4 Earnest Money Deposit (EMD) / Bid Security", clause_heading))
    story.append(Paragraph(
        "Bidders must furnish an Earnest Money Deposit (EMD) of INR 25,00,000 (Rupees Twenty-Five Lakhs Only) in the form of a Bank Guarantee from an Indian scheduled commercial bank. "
        "Micro and Small Enterprises (MSEs) registered with Udyam are exempted from submission of EMD, provided a valid Udyam Registration Certificate along with a signed Bid Security Declaration in the prescribed Form-B is submitted.",
        body_style
    ))

    story.append(Spacer(1, 8))
    story.append(Paragraph("SECTION 2: COMMERCIAL TERMS & ZERO-DEVIATION RULES", section_heading))

    story.append(Paragraph("Clause 2.1 Nil-Deviation and Strict Acceptance Mandate", clause_heading))
    story.append(Paragraph(
        "CPCL and EIL insist on complete adherence to all tender terms. "
        "Bidders shall confirm full compliance without any exception, caveat, assumption, or deviation. "
        "Statements such as 'subject to mutual discussion', 'as per vendor standard practice', or 'payment terms subject to dispatch clearance' "
        "shall be construed as material deviations and shall result in bid rejection. "
        "All bidders must submit the Zero Deviation Confirmation Certificate in Annexure-I.",
        body_style
    ))

    story.append(Paragraph("Clause 2.2 Payment Terms and Commercial Milestones", clause_heading))
    story.append(Paragraph(
        "Payment shall be released through electronic fund transfer (NEFT/RTGS) as follows:<br/>"
        "<b>a) 90% Progressive Payment:</b> Against receipt of equipment at project site in good condition, accompanied by verified dispatch documents, Material Test Certificates (MTCs), third-party inspection release note (TPI IRN), and GST tax invoice.<br/>"
        "<b>b) 10% Final Retention Payment:</b> Released upon successful mechanical completion, testing, and submission of Performance Bank Guarantee (PBG).",
        body_style
    ))

    story.append(Paragraph("Clause 2.3 Contract Performance Bank Guarantee (PBG)", clause_heading))
    story.append(Paragraph(
        "The successful bidder shall furnish a Performance Bank Guarantee for ten percent (10%) of the total purchase order value within twenty-one (21) days of Letter of Acceptance (LoA). "
        "The PBG must remain valid throughout the entire delivery period plus eighteen (18) months guarantee / warranty period, plus a sixty (60) day claims period.",
        body_style
    ))

    story.append(Paragraph("Clause 2.4 Taxes, Duties, and Freight Terms", clause_heading))
    story.append(Paragraph(
        "Prices quoted must be on FOT Project Site (CPCL CBR Project, Nagapattinam) basis, inclusive of packing, forwarding, freight, transit insurance, and port handling charges where applicable. "
        "GST shall be payable extra at applicable statutory rates against tax invoices adhering to Section 31 of the CGST Act.",
        body_style
    ))

    # ==========================================
    # PAGE 3: STATUTORY REQUIREMENTS & MSME
    # ==========================================
    story.append(PageBreak())

    story.append(Paragraph("SECTION 3: STATUTORY & REGULATORY REQUIREMENTS", section_heading))

    story.append(Paragraph("Clause 3.1 Goods and Services Tax (GST) Compliance", clause_heading))
    story.append(Paragraph(
        "The bidder must possess a valid, active Goods and Services Tax Identification Number (GSTIN) registered in India. "
        "A copy of the GST Registration Certificate (Form GST REG-06) showing the legal entity name, trade name, and registered business address must be uploaded. "
        "The legal name on the GST registration must match the bidder legal entity name without discrepancy. "
        "Bidders under composition levy are not eligible to participate.",
        body_style
    ))

    story.append(Paragraph("Clause 3.2 Permanent Account Number (PAN) Verification", clause_heading))
    story.append(Paragraph(
        "Every bidder must submit a clear, legible copy of the Permanent Account Number (PAN) card issued by the Central Board of Direct Taxes (CBDT), Government of India. "
        "The PAN number must be linked and cross-referenced to the bidder GSTIN and corporate filings.",
        body_style
    ))

    story.append(Paragraph("Clause 3.3 Micro & Small Enterprises (MSE) / Udyam Verification", clause_heading))
    story.append(Paragraph(
        "Bidders claiming purchase preference or tender fee / EMD exemptions under the Public Procurement Policy for Micro and Small Enterprises (MSEs) Order 2012 must submit: "
        "<br/>(i) Valid Udyam Registration Certificate issued by the Ministry of Micro, Small and Medium Enterprises (MSME). "
        "<br/>(ii) Proof that the Udyam registration covers the manufacturing category / National Industrial Classification (NIC) codes applicable to pressure equipment (NIC 2512 / 2813). "
        "<br/>(iii) Chartered Accountant certificate confirming investment in plant and machinery does not exceed statutory thresholds. "
        "Failure to submit valid Udyam credentials will revoke MSE benefits without notice.",
        body_style
    ))

    story.append(Paragraph("Clause 3.4 Audited Financial Accounts and CA Certification", clause_heading))
    story.append(Paragraph(
        "Bidders must furnish complete, audited Balance Sheets and Profit & Loss Accounts for the preceding three (3) financial years (FY 2023-24, FY 2024-25, FY 2025-26). "
        "Each financial statement must bear the Unique Document Identification Number (UDIN) issued by the Institute of Chartered Accountants of India (ICAI).",
        body_style
    ))

    story.append(Spacer(1, 6))
    story.append(Paragraph("SECTION 4: BIDDER ELIGIBILITY CRITERIA (BEC / PQC)", section_heading))

    story.append(Paragraph("Clause 4.1 Prior Technical Track Record and Experience", clause_heading))
    story.append(Paragraph(
        "The bidder must have independently engineered, fabricated, tested, and supplied at least one (1) Carbon Steel or Low-Alloy Steel High-Pressure Vessel "
        "conforming to ASME Section VIII Division 1 or Division 2 with minimum design pressure of <b>50 bar(g)</b> and shell wall thickness of at least <b>40 mm</b> "
        "to a petroleum refinery, petrochemical complex, or fertilizer facility within the last seven (7) years prior to the bid due date.<br/>"
        "Supporting evidence required: Purchase order copies, approved General Arrangement drawings, and Client Inspection Release Notes / Completion Certificates.",
        body_style
    ))

    story.append(Paragraph("Clause 4.2 Financial Turnover Capability", clause_heading))
    story.append(Paragraph(
        "The minimum average annual financial turnover of the bidder during the last three (3) audited financial years must be at least <b>INR 15.00 Crores</b> (Rupees Fifteen Crores Only). "
        "The net worth of the bidder as on the last date of the preceding financial year must be positive.",
        body_style
    ))

    story.append(Paragraph("Clause 4.3 ASME Accreditation and Code Certification", clause_heading))
    story.append(Paragraph(
        "The manufacturer must possess a valid Certificate of Authorization from the American Society of Mechanical Engineers (ASME) for use of the <b>'U' and 'U2'</b> Code Stamps. "
        "A certified copy of the ASME Stamp Certificate valid on the bid submission date must be submitted in Part-I.",
        body_style
    ))

    # ==========================================
    # PAGE 4: TECHNICAL SPECIFICATIONS & VDR MATRIX
    # ==========================================
    story.append(PageBreak())

    story.append(Paragraph("SECTION 5: TECHNICAL SPECIFICATIONS & VENDOR DATA REQUIREMENTS", section_heading))
    story.append(Paragraph(
        "The equipment must be designed, engineered, fabricated, and inspected in strict conformity with ASME Section VIII Division 2 (Alternative Rules), "
        "CPCL Engineering Standards, and EIL Standard Specifications for Pressure Vessels (6-12-0001 Rev. 6).",
        body_style
    ))

    story.append(Paragraph("Clause 5.1 General Arrangement Drawings & Nozzle Orientations", clause_heading))
    story.append(Paragraph(
        "Bidder shall provide detailed General Arrangement (GA) drawings showing overall vessel geometry, support skirt details, nozzle locations, "
        "internals configuration, anchor bolt sizing, and complete design parameter tables (Design Pressure: 68 bar(g), Design Temperature: 220 deg C, Corrosion Allowance: 3.0 mm).",
        body_style
    ))

    story.append(Paragraph("Clause 5.2 Mechanical Design Calculations", clause_heading))
    story.append(Paragraph(
        "Complete mechanical design calculations prepared using certified finite element / design software (PV Elite / Compress) conforming to ASME Section VIII Division 2 Part 4 & Part 5. "
        "Calculations must account for internal design pressure, static head, wind loads per IS:875 (Part 3), seismic accelerations per IS:1893, and nozzle local stress analysis per WRC-107/537.",
        body_style
    ))

    story.append(Paragraph("Clause 5.3 Material Test Certificates (MTC)", clause_heading))
    story.append(Paragraph(
        "All pressure-retaining plates shall be SA-516 Gr.70 (Normalized, Vacuum Degassed with HIC testing per NACE TM0284). "
        "Certified Material Test Certificates conforming to EN 10204 Type 3.1 or 3.2 showing chemical analysis, mechanical properties, Charpy V-notch impact tests at -29 deg C, "
        "and ultrasonic examination per SA-578 Level B must be provided.",
        body_style
    ))

    story.append(Paragraph("Clause 5.4 Welding Procedure Specifications (WPS) & PQR", clause_heading))
    story.append(Paragraph(
        "All welding procedures must be qualified in accordance with ASME Boiler and Pressure Vessel Code Section IX and EIL Specification 6-12-0005. "
        "Qualified Welding Procedure Specifications (WPS), Procedure Qualification Records (PQR), and Welder Performance Qualifications (WPQ) must be submitted for owner review prior to fabrication.",
        body_style
    ))

    story.append(Paragraph("Clause 5.5 Non-Destructive Examination (NDE/NDT) Reports", clause_heading))
    story.append(Paragraph(
        "100% Radiographic Examination (RT) or Automated Ultrasonic Testing (AUT) shall be conducted on all Category A and B longitudinal and circumferential butt welded seams. "
        "All nozzle attachment welds shall be examined by Magnetic Particle (MPT) or Liquid Penetrant (DPT). All NDT procedures and personnel certifications (ASNT Level II / III) must be documented.",
        body_style
    ))

    story.append(Paragraph("Clause 5.6 Post-Weld Heat Treatment (PWHT)", clause_heading))
    story.append(Paragraph(
        "PWHT is mandatory for all pressure vessels regardless of shell thickness due to sour service / wet H2S environment in accordance with NACE MR0103. "
        "The bidder must submit a detailed PWHT heating/cooling procedure and provide calibrated furnace time-temperature recorder chart evidence.",
        body_style
    ))

    story.append(Paragraph("Clause 5.7 Hydrostatic Pressure Testing", clause_heading))
    story.append(Paragraph(
        "Upon completion of PWHT and non-destructive examinations, each vessel shall be hydrostatically tested at 1.3 times the maximum allowable working pressure (MAWP) "
        "corrected for temperature in the presence of EIL / Third Party Inspection Agency (TPIA). Water chloride content must not exceed 25 ppm.",
        body_style
    ))

    story.append(Spacer(1, 4))
    story.append(Paragraph("VENDOR DATA REQUIREMENT (VDR) MATRIX", clause_heading))

    vdr_headers = [
        Paragraph("<b>Code</b>", table_cell_bold),
        Paragraph("<b>Document Description</b>", table_cell_bold),
        Paragraph("<b>Category</b>", table_cell_bold),
        Paragraph("<b>Stage Required</b>", table_cell_bold),
        Paragraph("<b>Review Status</b>", table_cell_bold),
    ]
    vdr_rows = [
        [Paragraph("VDR-01", table_cell), Paragraph("General Arrangement (GA) Drawing & Nozzle Schedule", table_cell), Paragraph("Technical", table_cell), Paragraph("With Bid (Part-I)", table_cell), Paragraph("Mandatory", table_cell_bold)],
        [Paragraph("VDR-02", table_cell), Paragraph("Mechanical Design Calculations & Software Files", table_cell), Paragraph("Technical", table_cell), Paragraph("With Bid (Part-I)", table_cell), Paragraph("Mandatory", table_cell_bold)],
        [Paragraph("VDR-03", table_cell), Paragraph("Material Test Certificates (EN 10204 Type 3.1/3.2)", table_cell), Paragraph("Quality", table_cell), Paragraph("Prior to Dispatch", table_cell), Paragraph("Mandatory", table_cell_bold)],
        [Paragraph("VDR-04", table_cell), Paragraph("Welding Procedure Specification (WPS) & PQR Records", table_cell), Paragraph("Quality", table_cell), Paragraph("With Bid (Part-I)", table_cell), Paragraph("Mandatory", table_cell_bold)],
        [Paragraph("VDR-05", table_cell), Paragraph("NDT Procedures & Radiographic Examination (RT) Reports", table_cell), Paragraph("Quality", table_cell), Paragraph("With Inspection", table_cell), Paragraph("Mandatory", table_cell_bold)],
        [Paragraph("VDR-06", table_cell), Paragraph("Post Weld Heat Treatment (PWHT) Procedure & Chart", table_cell), Paragraph("Quality", table_cell), Paragraph("With Inspection", table_cell), Paragraph("Mandatory", table_cell_bold)],
        [Paragraph("VDR-07", table_cell), Paragraph("Hydrostatic Test Procedure & Witnessed Certificate", table_cell), Paragraph("Quality", table_cell), Paragraph("Final Dossier", table_cell), Paragraph("Mandatory", table_cell_bold)],
    ]

    vdr_table = Table([vdr_headers] + vdr_rows, colWidths=[50, 220, 64, 90, 80])
    vdr_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), table_header_bg),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(vdr_table)

    # ==========================================
    # PAGE 5: STATUTORY UNDERTAKINGS & DECLARATIONS
    # ==========================================
    story.append(PageBreak())

    story.append(Paragraph("SECTION 6: STATUTORY UNDERTAKINGS & MANDATORY DECLARATIONS", section_heading))

    story.append(Paragraph("Clause 6.1 Public Procurement (Preference to Make in India) Order 2017 (PPP-MII)", clause_heading))
    story.append(Paragraph(
        "Only 'Class-I Local Suppliers' and 'Class-II Local Suppliers' as defined under the PPP-MII Order shall be eligible to bid. "
        "A Class-I Local Supplier is a supplier whose goods offered possess local content equal to or more than <b>50%</b>. "
        "A Class-II Local Supplier possesses local content between 20% and 50%. "
        "Non-local suppliers (less than 20% local content) are not eligible to participate.<br/>"
        "<b>Submission Requirement:</b> Bidders must submit a solemn declaration of local content percentage along with details of the location(s) "
        "at which local value addition is made. For tender value exceeding INR 10 Crores, the local content declaration must be certified by statutory auditors.",
        body_style
    ))

    story.append(Paragraph("Clause 6.2 Land-Border Sharing Country Compliance (DoE Order)", clause_heading))
    story.append(Paragraph(
        "In accordance with Department of Expenditure Order (Public Procurement No. 1, 2 & 3) F.No.6/18/2019-PPD dated 23-Jul-2020: "
        "Any bidder from a country sharing a land border with India shall be eligible to bid ONLY if registered with the Competent Authority (DPIIT). "
        "Bidders must submit the declaration in <b>Form-I (No Land Border Sharing)</b> or <b>Form-II (Valid DPIIT Registration Certificate)</b>. "
        "Failure to submit or providing false declarations shall lead to immediate disqualification and debarment.",
        body_style
    ))

    story.append(Paragraph("Clause 6.3 Integrity Pact (IP) Execution", clause_heading))
    story.append(Paragraph(
        "The bidder must execute the Integrity Pact on non-judicial stamp paper of value not less than INR 100/-. "
        "The Integrity Pact must be signed and stamped by the authorized signatory and witnessed by two independent persons. "
        "Any bid submitted without an executed, unaltered Integrity Pact shall be disqualified at the techno-commercial stage.<br/>"
        "<b>Independent External Monitors (IEMs):</b><br/>"
        "1. Shri R. K. Sharma, Ex-Secretary (GoI) — email: iem1.cpcl@gov.in<br/>"
        "2. Shri V. K. Gupta, Ex-Director General (Works) — email: iem2.cpcl@gov.in",
        body_style
    ))

    story.append(Paragraph("Clause 6.4 Non-Blacklisting & Conflict of Interest Declaration", clause_heading))
    story.append(Paragraph(
        "Bidder must submit a formal declaration affirming that:<br/>"
        "(a) The bidder, its directors, partners, or associates are not currently blacklisted or debarred by CPCL, IOCL, GeM, or any Ministry/PSU.<br/>"
        "(b) The bidder does not share common management, controlling interest, or key personnel with any other bidder participating in this tender.<br/>"
        "(c) No agent or intermediary has been engaged to influence procurement outcomes.",
        body_style
    ))

    story.append(Spacer(1, 10))
    story.append(Paragraph("ANNEXURE CHECKLIST FOR BIDDERS (MANDATORY SUBMISSIONS)", section_heading))

    checklist_headers = [
        Paragraph("<b>Clause Ref</b>", table_cell_bold),
        Paragraph("<b>Form / Document Required</b>", table_cell_bold),
        Paragraph("<b>Verification Mode</b>", table_cell_bold),
        Paragraph("<b>Criticality</b>", table_cell_bold),
    ]
    checklist_rows = [
        [Paragraph("Clause 1.2", table_cell), Paragraph("Power of Attorney / Board Resolution", table_cell), Paragraph("Document Evidence", table_cell), Paragraph("MANDATORY", table_cell_bold)],
        [Paragraph("Clause 1.4", table_cell), Paragraph("EMD Bank Guarantee or MSE Bid Security Declaration (Form-B)", table_cell), Paragraph("Financial / Udyam Check", table_cell), Paragraph("MANDATORY", table_cell_bold)],
        [Paragraph("Clause 2.1", table_cell), Paragraph("Zero Deviation Certificate (Annexure-I)", table_cell), Paragraph("Compliance Scan", table_cell), Paragraph("CRITICAL", table_cell_bold)],
        [Paragraph("Clause 3.1", table_cell), Paragraph("GST Registration Certificate (Form GST REG-06)", table_cell), Paragraph("GSTIN Portal API", table_cell), Paragraph("MANDATORY", table_cell_bold)],
        [Paragraph("Clause 3.2", table_cell), Paragraph("PAN Card Copy", table_cell), Paragraph("PAN Entity Check", table_cell), Paragraph("MANDATORY", table_cell_bold)],
        [Paragraph("Clause 3.3", table_cell), Paragraph("Udyam Registration Certificate (MSE Units only)", table_cell), Paragraph("MSME Udyam Portal", table_cell), Paragraph("CONDITIONAL", table_cell_bold)],
        [Paragraph("Clause 4.1", table_cell), Paragraph("Prior Experience Proof (PO, GA Drawing, Completion Certificate)", table_cell), Paragraph("Technical Audit", table_cell), Paragraph("CRITICAL", table_cell_bold)],
        [Paragraph("Clause 4.3", table_cell), Paragraph("ASME 'U' / 'U2' Authorization Certificate", table_cell), Paragraph("ASME Verification", table_cell), Paragraph("MANDATORY", table_cell_bold)],
        [Paragraph("Clause 5.1", table_cell), Paragraph("General Arrangement Drawings & Nozzle Details", table_cell), Paragraph("Engineering Review", table_cell), Paragraph("MANDATORY", table_cell_bold)],
        [Paragraph("Clause 5.2", table_cell), Paragraph("Mechanical Design Calculations (ASME Sec VIII Div 2)", table_cell), Paragraph("Engineering Review", table_cell), Paragraph("MANDATORY", table_cell_bold)],
        [Paragraph("Clause 5.4", table_cell), Paragraph("WPS & PQR Documents per ASME Sec IX", table_cell), Paragraph("Welding Audit", table_cell), Paragraph("MANDATORY", table_cell_bold)],
        [Paragraph("Clause 6.1", table_cell), Paragraph("Make in India (PPP-MII) Local Content Certificate", table_cell), Paragraph("Auditor Certificate", table_cell), Paragraph("MANDATORY", table_cell_bold)],
        [Paragraph("Clause 6.2", table_cell), Paragraph("Land Border Sharing Country Undertaking (Form-I/II)", table_cell), Paragraph("DoE Compliance Check", table_cell), Paragraph("CRITICAL", table_cell_bold)],
        [Paragraph("Clause 6.3", table_cell), Paragraph("Duly Executed Integrity Pact with IEM Details", table_cell), Paragraph("Legal Audit", table_cell), Paragraph("CRITICAL", table_cell_bold)],
    ]

    chk_table = Table([checklist_headers] + checklist_rows, colWidths=[70, 240, 114, 80])
    chk_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), table_header_bg),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(chk_table)

    # Build PDF with dynamic page counter
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated authentic tender PDF at: {output_path}")


if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent
    default_target = base_dir / "reference_tenders" / "CPCL_Pressure_Vessel_Tender_RFQ_2026.pdf"
    target = sys.argv[1] if len(sys.argv) > 1 else str(default_target)
    build_cpcl_tender_pdf(target)

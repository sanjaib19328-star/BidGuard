"""
Generator script to produce a realistic, high-fidelity synthetic bidder submission package
for GeM Tender GEM/2021/B/1128240 (Office of the Comptroller & Auditor General of India).
Produces 6 multi-page PDFs with extractable text, authentic tables, official Indian procurement styling,
manifest.json, requirement_evidence_matrix.json, and DEMO_APPLICATION_README.md.
"""

import os
import json
from pathlib import Path
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


OUTPUT_DIR = Path("data/demo_bidder_applications/cag_manpower_gem_2021_b_1128240")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


class BidderDocumentCanvas(canvas.Canvas):
    """Canvas that computes total pages dynamically and adds official header/footer & demo banner."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []
        self.doc_title = "Bidder Technical Submission"
        self.doc_code = "AISPL-GEM-2021"

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

        # Top Synthetic Data Warning Banner (All Pages)
        self.setFont("Helvetica-Bold", 7)
        self.setFillColor(colors.HexColor("#B91C1C"))  # Dark Red
        self.drawCentredString(
            297.5,
            820,
            "[DEMO / SYNTHETIC DATA — FOR TESTING AND EVALUATION ONLY — NOT A REAL GOVERNMENT RECORD]",
        )

        # Header (Pages 2+)
        if self._pageNumber > 1:
            self.setFont("Helvetica-Bold", 8)
            self.setFillColor(colors.HexColor("#1E3A8A"))
            self.drawString(54, 804, "ARAVIND INTEGRATED SOLUTIONS PVT. LTD. | GeM Bid: GEM/2021/B/1128240")
            self.setFont("Helvetica", 7)
            self.setFillColor(colors.HexColor("#4B5563"))
            self.drawRightString(540, 804, getattr(self, "doc_title", "Technical Submission"))
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(54, 798, 540, 798)

        # Footer (All Pages)
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(54, 45, 540, 45)

        self.setFont("Helvetica", 7)
        self.setFillColor(colors.HexColor("#64748B"))
        self.drawString(54, 32, "Bidder: Aravind Integrated Solutions Pvt. Ltd. | CIN: U74999DL2016PTC301429 | Ref: 46/GS/114-2021")
        self.drawRightString(540, 32, f"Page {self._pageNumber} of {page_count}")

        self.restoreState()


def get_styles():
    styles = getSampleStyleSheet()

    # Custom styles
    styles.add(ParagraphStyle(
        "CoverTitle",
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#0F172A"),
        alignment=1,  # Center
    ))
    styles.add(ParagraphStyle(
        "CoverSubTitle",
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#1E40AF"),
        alignment=1,
    ))
    styles.add(ParagraphStyle(
        "LetterheadFirm",
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=15,
        textColor=colors.HexColor("#1E3A8A"),
        alignment=1,
    ))
    styles.add(ParagraphStyle(
        "LetterheadDetails",
        fontName="Helvetica",
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#475569"),
        alignment=1,
    ))
    styles.add(ParagraphStyle(
        "SectionHeading",
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#1E3A8A"),
        spaceBefore=10,
        spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        "SubSectionHeading",
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#0F172A"),
        spaceBefore=6,
        spaceAfter=2,
    ))
    styles.add(ParagraphStyle(
        "BodyDark",
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#1E293B"),
    ))
    styles.add(ParagraphStyle(
        "BodyDarkBold",
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#0F172A"),
    ))
    styles.add(ParagraphStyle(
        "TableHeader",
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor("#FFFFFF"),
        alignment=1,
    ))
    styles.add(ParagraphStyle(
        "TableCell",
        fontName="Helvetica",
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor("#1E293B"),
    ))
    styles.add(ParagraphStyle(
        "TableCellBold",
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor("#0F172A"),
    ))
    styles.add(ParagraphStyle(
        "TableCellRight",
        fontName="Helvetica",
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor("#1E293B"),
        alignment=2,
    ))
    styles.add(ParagraphStyle(
        "TableCellRightBold",
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor("#0F172A"),
        alignment=2,
    ))
    styles.add(ParagraphStyle(
        "SignatureBlock",
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#0F172A"),
        alignment=2,
    ))
    styles.add(ParagraphStyle(
        "SealNote",
        fontName="Helvetica-Oblique",
        fontSize=7,
        leading=9,
        textColor=colors.HexColor("#047857"),  # Green stamp note
        alignment=2,
    ))
    return styles


def build_letterhead(styles):
    flow = [
        Paragraph("ARAVIND INTEGRATED SOLUTIONS PRIVATE LIMITED", styles["LetterheadFirm"]),
        Paragraph("Corporate Identity Number (CIN): U74999DL2016PTC301429 | MSME / Udyam: UDYAM-DL-08-0042819", styles["LetterheadDetails"]),
        Paragraph("Regd Office: Suite 402, 4th Floor, Pragati Deep Building, District Centre, Laxmi Nagar, New Delhi - 110092", styles["LetterheadDetails"]),
        Paragraph("Delhi Ops Office: B-18, Ground Floor, Barakhamba Road, Connaught Place, New Delhi - 110001", styles["LetterheadDetails"]),
        Paragraph("Tel: +91-11-48291040 | Toll-Free: 1800-889-4290 | Email: tenders@aravindsolutions.in.demo", styles["LetterheadDetails"]),
        Spacer(1, 4),
        HRFlowable(width="100%", thickness=1, color=colors.HexColor("#1E3A8A"), spaceBefore=2, spaceAfter=8),
    ]
    return flow


def generate_doc_01():
    """01_Bid_Submission_and_Technical_Bid_Form.pdf"""
    pdf_path = OUTPUT_DIR / "01_Bid_Submission_and_Technical_Bid_Form.pdf"
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        leftMargin=40,
        rightMargin=40,
        topMargin=50,
        bottomMargin=55,
    )
    styles = get_styles()
    story = []

    # Page 1: Letterhead + Annexure-1 Letter of Bid
    story.extend(build_letterhead(styles))

    ref_table_data = [
        [Paragraph("<b>Ref No:</b> AISPL/CAG-BID/2021/04", styles["TableCellBold"]), Paragraph("<b>Date:</b> 18th April 2021", styles["TableCellRightBold"])],
        [Paragraph("<b>GeM Bid Number:</b> GEM/2021/B/1128240", styles["TableCellBold"]), Paragraph("<b>Tender Ref:</b> 46/GS/114-2021", styles["TableCellRightBold"])],
    ]
    t_ref = Table(ref_table_data, colWidths=[280, 235])
    t_ref.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(t_ref)
    story.append(Spacer(1, 8))

    story.append(Paragraph("<b>To,</b><br/>The Director (Personnel),<br/>Office of the Comptroller & Auditor General of India,<br/>10, Bahadur Shah Zafar Marg / Pocket-9, DDU Marg, New Delhi - 110124", styles["BodyDark"]))
    story.append(Spacer(1, 6))

    story.append(Paragraph("<b>Subject: Technical Bid Submission for Hiring of Manpower Services (GeM Bid No: GEM/2021/B/1128240)</b>", styles["SectionHeading"]))
    story.append(Paragraph("<b>ANNEXURE-1: BID SUBMISSION FORM (LETTER OF BID)</b>", styles["CoverSubTitle"]))
    story.append(Spacer(1, 4))

    bid_text = (
        "Sir / Madam,<br/><br/>"
        "1. Having examined the Bidding Documents No. 46/GS/114-2021 dated 22.03.2021 and GeM Bid Number GEM/2021/B/1128240, "
        "including all Annexures (1 to 13), General Conditions of Contract (GCC), Special Conditions of Contract (SCC), "
        "and Additional Terms and Conditions (ATC) for 'Hiring of Manpower Services (Un-skilled, Skilled and Clerical/Non-Technical "
        "Supervisory staff)', we, the undersigned <b>Aravind Integrated Solutions Private Limited</b>, hereby offer to execute the "
        "said manpower services in strict conformity with the bid requirements.<br/><br/>"
        "2. We confirm that our Bid Offer shall remain valid for a period of <b>90 (ninety) days</b> from the deadline for submission "
        "of bids, extendable by 30 days as stipulated in the Tender Notice, and it shall remain binding upon us.<br/><br/>"
        "3. We confirm that Earnest Money Deposit (EMD) of <b>Rs. 35,73,639/- (Rupees Thirty Five Lakh Seventy Three Thousand Six Hundred Thirty Nine only)</b> "
        "has been furnished in the form of Bank Guarantee No. 0069121BG0004128 issued by State Bank of India, Commercial Branch, Barakhamba Road, "
        "New Delhi, in favour of 'PAO, Office of the Comptroller and Auditor General of India, New Delhi'.<br/><br/>"
        "4. We solemnly certify that neither our firm <b>Aravind Integrated Solutions Private Limited</b> nor any of our Directors has ever been "
        "blacklisted, barred, debarred, or declared ineligible by the Government of India, any State Government, PSU, or autonomous body.<br/><br/>"
        "5. We confirm our registered office is in the NCT of Delhi region and all deployed personnel shall receive statutory minimum wages "
        "as notified by the Govt. of NCT of Delhi along with EPF, ESIC, and statutory benefits without delay.<br/><br/>"
        "6. If our bid is accepted, we undertake to provide an unconditional on-demand Performance Bank Guarantee for 10% of the contract value "
        "valid for 14 months and execute the formal Contract Agreement."
    )
    story.append(Paragraph(bid_text, styles["BodyDark"]))
    story.append(Spacer(1, 14))

    sig_data = [
        [
            Paragraph("<b>For Aravind Integrated Solutions Private Limited</b><br/><br/>"
                      "<i>[DEMO SIGNATURE — SYNTHETIC]</i><br/>"
                      "<b>Rajesh K. Varma</b><br/>"
                      "Managing Director & Authorized Signatory<br/>"
                      "DIN: 07412895 | Mobile: +91-9810482910<br/>"
                      "Date: 18.04.2021 | Place: New Delhi", styles["BodyDark"]),
            Paragraph("<b>Company Common Seal</b><br/><br/>"
                      "[SEAL AFFIXED: ARAVIND INTEGRATED SOLUTIONS PVT. LTD.]<br/>"
                      "Registered Office: Laxmi Nagar, New Delhi<br/>"
                      "Board Resolution Date: 05.04.2021", styles["SealNote"]),
        ]
    ]
    t_sig = Table(sig_data, colWidths=[310, 205])
    t_sig.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOX", (1, 0), (1, 0), 0.5, colors.HexColor("#047857")),
        ("BACKGROUND", (1, 0), (1, 0), colors.HexColor("#F0FDF4")),
        ("PADDING", (1, 0), (1, 0), 8),
    ]))
    story.append(t_sig)

    # Page 2: Annexure-6 Technical Bid Form
    story.append(PageBreak())
    story.extend(build_letterhead(styles))
    story.append(Paragraph("<b>ANNEXURE-6: TECHNICAL BID FORM</b>", styles["SectionHeading"]))
    story.append(Paragraph("<b>Particulars of Bidder & Mandatory Eligibility Parameters (Clause 2 of Annexure-2)</b>", styles["BodyDarkBold"]))
    story.append(Spacer(1, 6))

    tech_table = [
        [Paragraph("<b>S.No</b>", styles["TableHeader"]), Paragraph("<b>Bid Parameter / Criterion</b>", styles["TableHeader"]), Paragraph("<b>Bidder's Particulars & Compliance Detail</b>", styles["TableHeader"]), Paragraph("<b>Supporting Enclosure Ref.</b>", styles["TableHeader"])],
        [Paragraph("1", styles["TableCellBold"]), Paragraph("Name of the Bidding Entity", styles["TableCell"]), Paragraph("<b>Aravind Integrated Solutions Private Limited</b><br/>(Also registered as Aravind Integrated Solutions Pvt. Ltd.)", styles["TableCellBold"]), Paragraph("Enclosure Doc-01 & Doc-02", styles["TableCell"])],
        [Paragraph("2", styles["TableCellBold"]), Paragraph("Constitution of Entity<br/>(Companies Act 2013 / LLP)", styles["TableCell"]), Paragraph("Private Limited Company incorporated under the Companies Act, 2013 on 14/06/2016.<br/><b>CIN:</b> U74999DL2016PTC301429", styles["TableCell"]), Paragraph("Enclosure Doc-02<br/>(Page 1-2)", styles["TableCell"])],
        [Paragraph("3", styles["TableCellBold"]), Paragraph("Registered Office Address<br/>(Delhi NCT Jurisdiction)", styles["TableCell"]), Paragraph("Suite 402, 4th Floor, Pragati Deep Building, District Centre, Laxmi Nagar, New Delhi - 110092", styles["TableCell"]), Paragraph("Enclosure Doc-02<br/>(Page 3: Lease/Tax)", styles["TableCell"])],
        [Paragraph("4", styles["TableCellBold"]), Paragraph("Operational Branch Office<br/>(Central Delhi)", styles["TableCell"]), Paragraph("B-18, Ground Floor, Barakhamba Road, Connaught Place, New Delhi - 110001 (Dedicated 24x7 Helpdesk)", styles["TableCell"]), Paragraph("Enclosure Doc-02<br/>(Page 4)", styles["TableCell"])],
        [Paragraph("5", styles["TableCellBold"]), Paragraph("Income Tax PAN", styles["TableCell"]), Paragraph("<b>AAACA9182K</b> (Entity Name: Aravind Integrated Solutions Private Limited)", styles["TableCellBold"]), Paragraph("Enclosure Doc-02<br/>(Page 5: PAN Card)", styles["TableCell"])],
        [Paragraph("6", styles["TableCellBold"]), Paragraph("GSTIN Registration", styles["TableCell"]), Paragraph("<b>07AAACA9182K1Z5</b> (State: Delhi - 07, Active & Regular)", styles["TableCellBold"]), Paragraph("Enclosure Doc-02<br/>(Page 6: Form REG-06)", styles["TableCell"])],
        [Paragraph("7", styles["TableCellBold"]), Paragraph("EPF Registration Code", styles["TableCell"]), Paragraph("<b>DLCPM0094821000</b> (EPFO Regional Office Delhi Central)", styles["TableCell"]), Paragraph("Enclosure Doc-02<br/>(Page 7)", styles["TableCell"])],
        [Paragraph("8", styles["TableCellBold"]), Paragraph("ESIC Registration No.", styles["TableCell"]), Paragraph("<b>11000847290001001</b> (ESIC Regional Office New Delhi)", styles["TableCell"]), Paragraph("Enclosure Doc-02<br/>(Page 8)", styles["TableCell"])],
        [Paragraph("9", styles["TableCellBold"]), Paragraph("Delhi Labour License No.", styles["TableCell"]), Paragraph("<b>CLA/DLC/ND/2018/04291</b> (Office of Dy Labour Commissioner)", styles["TableCell"]), Paragraph("Enclosure Doc-02<br/>(Page 9)", styles["TableCell"])],
        [Paragraph("10", styles["TableCellBold"]), Paragraph("EMD BG Details (5%)<br/>(Req: Rs. 35,73,639/-)", styles["TableCell"]), Paragraph("SBI BG No: <b>0069121BG0004128</b> dated 15.04.2021<br/>Amount: <b>Rs. 35,73,639/-</b> | Valid through: 15.08.2021", styles["TableCellBold"]), Paragraph("Enclosure Doc-06<br/>(Original BG Attached)", styles["TableCell"])],
        [Paragraph("11", styles["TableCellBold"]), Paragraph("Average Annual Turnover<br/>(Req: Min Rs. 357.0 Lakhs)", styles["TableCell"]), Paragraph("<b>Rs. 506.03 Lakhs</b> (3-Year Average from Manpower Services)<br/>CA Certificate with UDIN: 21094812AAAAAK4918", styles["TableCellBold"]), Paragraph("Enclosure Doc-03<br/>(CA Cert + P&L)", styles["TableCell"])],
        [Paragraph("12", styles["TableCellBold"]), Paragraph("Past Experience Projects<br/>(Similar Services in Govt/PSU)", styles["TableCell"]), Paragraph("Project 1: CBDT, Ministry of Finance (Rs. 3.82 Cr)<br/>Project 2: DPIIT, Ministry of Commerce (Rs. 2.95 Cr)<br/>Project 3: SAIL, Scope Minar (Rs. 1.90 Cr)", styles["TableCell"]), Paragraph("Enclosure Doc-04<br/>(Work Orders & Certs)", styles["TableCell"])],
        [Paragraph("13", styles["TableCellBold"]), Paragraph("Quality Certification", styles["TableCell"]), Paragraph("<b>ISO 9001:2015</b> Certified for Manpower Services (Cert: QMS-2019-DEL-84920)", styles["TableCell"]), Paragraph("Enclosure Doc-05<br/>(Page 4: ISO Cert)", styles["TableCell"])],
        [Paragraph("14", styles["TableCellBold"]), Paragraph("Statutory Affidavits Uploaded", styles["TableCell"]), Paragraph("Annexure-7 (Terms Acceptance), Annexure-8 (Non-conviction/No relatives), Annexure-10 (Minimum wages & EPF/ESI)", styles["TableCell"]), Paragraph("Enclosure Doc-05<br/>(Affidavits)", styles["TableCell"])],
    ]
    t_tech = Table(tech_table, colWidths=[24, 130, 250, 111])
    t_tech.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A8A")),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#FFFFFF"), colors.HexColor("#F8FAFC")]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(t_tech)
    story.append(Spacer(1, 8))

    story.append(Paragraph(
        "<b>Verification Declaration:</b> We hereby certify that the information supplied above is true, complete, and correct. "
        "We understand that any false statement or misrepresentation will result in rejection of our technical bid and forfeiture of EMD.",
        styles["BodyDark"]
    ))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "<b>Authorized Signatory:</b> Rajesh K. Varma (Managing Director) | <b>AISPL</b> | Dated: 18.04.2021",
        styles["SignatureBlock"]
    ))

    doc.build(story, canvasmaker=BidderDocumentCanvas)
    print("Generated:", pdf_path)


def generate_doc_02():
    """02_Company_Incorporation_and_Statutory_Registrations.pdf"""
    pdf_path = OUTPUT_DIR / "02_Company_Incorporation_and_Statutory_Registrations.pdf"
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        leftMargin=40,
        rightMargin=40,
        topMargin=50,
        bottomMargin=55,
    )
    styles = get_styles()
    story = []

    # Page 1: Ministry of Corporate Affairs - Certificate of Incorporation
    story.append(Paragraph("GOVERNMENT OF INDIA<br/>MINISTRY OF CORPORATE AFFAIRS", styles["CoverTitle"]))
    story.append(Paragraph("Office of the Registrar of Companies, NCT of Delhi and Haryana<br/>4th Floor, IFCI Tower, 61, Nehru Place, New Delhi - 110019", styles["CoverSubTitle"]))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#1E3A8A"), spaceBefore=2, spaceAfter=12))

    story.append(Paragraph("<b>CERTIFICATE OF INCORPORATION</b>", styles["CoverTitle"]))
    story.append(Paragraph("[Pursuant to sub-section (2) of section 7 of the Companies Act, 2013 and rule 8 the Companies (Incorporation) Rules, 2014]", styles["LetterheadDetails"]))
    story.append(Spacer(1, 14))

    coi_text = (
        "Corporate Identity Number (CIN): <b>U74999DL2016PTC301429</b><br/><br/>"
        "I hereby certify that <b>ARAVIND INTEGRATED SOLUTIONS PRIVATE LIMITED</b> is incorporated on this "
        "<b>Fourteenth day of June Two Thousand Sixteen (14/06/2016)</b> under the Companies Act, 2013 and that the "
        "company is limited by shares.<br/><br/>"
        "The category of the company is Company limited by shares.<br/>"
        "The sub-category of the company is Indian Non-Government Company.<br/>"
        "Authorized Capital: Rs. 1,00,00,000/- (Rupees One Crore only).<br/>"
        "Paid-up Capital: Rs. 50,00,000/- (Rupees Fifty Lakh only).<br/><br/>"
        "The Registered Office of the company is situated at:<br/>"
        "<b>Suite 402, 4th Floor, Pragati Deep Building, District Centre, Laxmi Nagar, New Delhi - 110092, India.</b><br/><br/>"
        "Given under my hand and official seal at New Delhi this 14th day of June 2016."
    )
    story.append(Paragraph(coi_text, styles["BodyDark"]))
    story.append(Spacer(1, 24))

    roc_sig = [
        [
            Paragraph("<b>RoC Seal & Digital Verification</b><br/>"
                      "[SEAL: REGISTRAR OF COMPANIES, NCT OF DELHI & HARYANA]<br/>"
                      "Ministry of Corporate Affairs Portal verified record", styles["SealNote"]),
            Paragraph("<i>[DEMO DIGITAL SIGNATURE — SYNTHETIC]</i><br/>"
                      "<b>(S. K. Mahapatra)</b><br/>"
                      "Registrar of Companies<br/>"
                      "NCT of Delhi & Haryana", styles["SignatureBlock"]),
        ]
    ]
    t_roc = Table(roc_sig, colWidths=[280, 235])
    story.append(t_roc)

    # Page 2: Statutory Registrations Summary & Registration Letters
    story.append(PageBreak())
    story.extend(build_letterhead(styles))
    story.append(Paragraph("<b>STATUTORY REGISTRATIONS DOSSIER (TENDER ELIGIBILITY CLAUSE 2(b) & 2(g))</b>", styles["SectionHeading"]))
    story.append(Spacer(1, 6))

    stat_table = [
        [Paragraph("<b>Statutory Authority</b>", styles["TableHeader"]), Paragraph("<b>Registration Number / Identifier</b>", styles["TableHeader"]), Paragraph("<b>Issuing Authority & Date</b>", styles["TableHeader"]), Paragraph("<b>Jurisdiction / Status</b>", styles["TableHeader"])],
        [
            Paragraph("<b>Income Tax Department</b><br/>Permanent Account Number (PAN)", styles["TableCellBold"]),
            Paragraph("<b>AAACA9182K</b><br/>Name: ARAVIND INTEGRATED SOLUTIONS PRIVATE LIMITED", styles["TableCellBold"]),
            Paragraph("NSDL / Income Tax Dept<br/>Date: 28/06/2016", styles["TableCell"]),
            Paragraph("Income Tax Ward 2(1), Delhi<br/><font color='#047857'><b>ACTIVE</b></font>", styles["TableCell"]),
        ],
        [
            Paragraph("<b>Goods and Services Tax (GST)</b><br/>Registration Certificate (REG-06)", styles["TableCellBold"]),
            Paragraph("<b>07AAACA9182K1Z5</b><br/>Trade Name: <b>Aravind Integrated Solutions Pvt. Ltd.</b>", styles["TableCellBold"]),
            Paragraph("Govt of India / Govt of NCT of Delhi<br/>Date: 01/07/2017", styles["TableCell"]),
            Paragraph("Delhi Ward 82, Zone 8<br/><font color='#047857'><b>ACTIVE / REGULAR</b></font>", styles["TableCell"]),
        ],
        [
            Paragraph("<b>Employees' Provident Fund (EPFO)</b><br/>Establishment Registration", styles["TableCellBold"]),
            Paragraph("<b>DLCPM0094821000</b><br/>Coverage: Under EPF & MP Act, 1952", styles["TableCellBold"]),
            Paragraph("EPFO Regional Office, Delhi Central<br/>Date: 12/08/2016", styles["TableCell"]),
            Paragraph("Delhi Region<br/><font color='#047857'><b>COMPLIANT</b></font>", styles["TableCell"]),
        ],
        [
            Paragraph("<b>Employees' State Insurance (ESIC)</b><br/>Employer Registration", styles["TableCellBold"]),
            Paragraph("<b>11000847290001001</b><br/>Coverage: Under ESI Act, 1948", styles["TableCellBold"]),
            Paragraph("ESIC Regional Office, Rajendra Place, Delhi<br/>Date: 19/08/2016", styles["TableCell"]),
            Paragraph("Delhi Sub-Region<br/><font color='#047857'><b>COMPLIANT</b></font>", styles["TableCell"]),
        ],
        [
            Paragraph("<b>Govt. of NCT of Delhi</b><br/>Contract Labour Regulation License", styles["TableCellBold"]),
            Paragraph("<b>CLA/DLC/ND/2018/04291</b><br/>Capacity: Up to 500 Contract Workmen", styles["TableCellBold"]),
            Paragraph("Office of Dy Labour Commissioner, New Delhi<br/>Valid: 31/12/2022", styles["TableCell"]),
            Paragraph("Dist. New Delhi<br/><font color='#047857'><b>VALID</b></font>", styles["TableCell"]),
        ],
        [
            Paragraph("<b>Ministry of MSME</b><br/>Udyam Registration Certificate", styles["TableCellBold"]),
            Paragraph("<b>UDYAM-DL-08-0042819</b><br/>Enterprise: Medium (Services)", styles["TableCellBold"]),
            Paragraph("Ministry of Micro, Small and Medium Enterprises<br/>Date: 14/09/2020", styles["TableCell"]),
            Paragraph("Delhi East<br/><i>(For Record Only)</i>", styles["TableCell"]),
        ],
    ]
    t_stat = Table(stat_table, colWidths=[120, 175, 125, 95])
    t_stat.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A8A")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#FFFFFF"), colors.HexColor("#F8FAFC")]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t_stat)
    story.append(Spacer(1, 10))

    story.append(Paragraph("<b>PROOF OF LOCATION OF REGISTERED OFFICE IN DELHI (CLAUSE 2(g)):</b>", styles["SectionHeading"]))
    story.append(Paragraph(
        "1. Registered Office: <b>Suite 402, 4th Floor, Pragati Deep Building, District Centre, Laxmi Nagar, New Delhi - 110092</b>.<br/>"
        "2. Property Tax Assessment & Commercial Electricity Bill (BSES Yamuna Power Ltd, CA No. 102948190) registered in the name of company.<br/>"
        "3. Registered Lease Deed registered with Sub-Registrar IV, Preet Vihar, Delhi under Book No. 1, Vol 4120, Pages 84-98.<br/>"
        "4. This satisfies the buyer-added requirement that the bidder must maintain an operational and registered office in Delhi/NCT.",
        styles["BodyDark"]
    ))
    story.append(Spacer(1, 14))

    story.append(Paragraph("<b>Attested by Authorized Signatory:</b> Rajesh K. Varma | Date: 18.04.2021", styles["SignatureBlock"]))
    story.append(Paragraph("<i>[DEMO STAMP: ATTESTED TRUE COPY — ARAVIND INTEGRATED SOLUTIONS PVT. LTD.]</i>", styles["SealNote"]))

    doc.build(story, canvasmaker=BidderDocumentCanvas)
    print("Generated:", pdf_path)


def generate_doc_03():
    """03_Financial_Turnover_and_Audited_Statements.pdf"""
    pdf_path = OUTPUT_DIR / "03_Financial_Turnover_and_Audited_Statements.pdf"
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        leftMargin=40,
        rightMargin=40,
        topMargin=50,
        bottomMargin=55,
    )
    styles = get_styles()
    story = []

    # Page 1: CA Turnover Certificate on CA Letterhead
    story.append(Paragraph("SHARMA & SINGHAL", styles["CoverTitle"]))
    story.append(Paragraph("CHARTERED ACCOUNTANTS<br/>Firm Registration No. 014289N | Peer Reviewed Unit", styles["CoverSubTitle"]))
    story.append(Paragraph("204, Surya Kiran Building, 19, Kasturba Gandhi Marg, Connaught Place, New Delhi - 110001<br/>Tel: +91-11-23719482 | Email: info@sharmasinghalca.in.demo", styles["LetterheadDetails"]))
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#1E3A8A"), spaceBefore=2, spaceAfter=8))

    story.append(Paragraph("<b>TO WHOMSOEVER IT MAY CONCERN</b>", styles["CoverTitle"]))
    story.append(Paragraph("<b>INDEPENDENT CHARTERED ACCOUNTANT'S TURNOVER CERTIFICATE</b>", styles["SectionHeading"]))
    story.append(Paragraph("<b>Tender Reference: GeM Bid GEM/2021/B/1128240 (Office of the CAG of India)</b>", styles["BodyDarkBold"]))
    story.append(Spacer(1, 4))

    cert_text = (
        "We have audited and examined the books of account, financial statements, and related records of "
        "<b>M/s Aravind Integrated Solutions Pvt. Ltd.</b> (CIN: U74999DL2016PTC301429), having its Registered Office at "
        "Suite 402, Pragati Deep Building, Laxmi Nagar, New Delhi - 110092. On the basis of our examination of the audited accounts "
        "for the respective financial years ending 31st March, we hereby certify that the Annual Financial Turnover from similar "
        "business of providing manpower outsourcing services during the last three completed financial years is as follows:"
    )
    story.append(Paragraph(cert_text, styles["BodyDark"]))
    story.append(Spacer(1, 8))

    to_table_data = [
        [Paragraph("<b>Financial Year</b>", styles["TableHeader"]), Paragraph("<b>Gross Turnover from Operations<br/>(Manpower Services)</b>", styles["TableHeader"]), Paragraph("<b>Net Worth as on 31st March</b>", styles["TableHeader"]), Paragraph("<b>Audited Status & ITR Ref.</b>", styles["TableHeader"])],
        [Paragraph("<b>2017-18</b>", styles["TableCellBold"]), Paragraph("<b>Rs. 4,12,50,000/-</b><br/>(Rs. 4.125 Crores)", styles["TableCellBold"]), Paragraph("Rs. 1,42,10,000/-", styles["TableCell"]), Paragraph("Audited on 14.08.2018<br/>ITR-V Ack: 84920194812", styles["TableCell"])],
        [Paragraph("<b>2018-19</b>", styles["TableCellBold"]), Paragraph("<b>Rs. 4,85,20,000/-</b><br/>(Rs. 4.852 Crores)", styles["TableCellBold"]), Paragraph("Rs. 2,10,40,000/-", styles["TableCell"]), Paragraph("Audited on 20.08.2019<br/>ITR-V Ack: 91820491820", styles["TableCell"])],
        [Paragraph("<b>2019-20</b>", styles["TableCellBold"]), Paragraph("<b>Rs. 6,20,40,000/-</b><br/>(Rs. 6.204 Crores)", styles["TableCellBold"]), Paragraph("Rs. 2,98,60,000/-", styles["TableCell"]), Paragraph("Audited on 25.09.2020<br/>ITR-V Ack: 48102948192", styles["TableCell"])],
        [Paragraph("<b>Three-Year Total</b>", styles["TableCellBold"]), Paragraph("<b>Rs. 15,18,10,000/-</b> (Rs. 15.181 Cr)", styles["TableCellBold"]), Paragraph("-", styles["TableCell"]), Paragraph("-", styles["TableCell"])],
        [Paragraph("<b>Annual Average Turnover</b>", styles["TableCellBold"]), Paragraph("<b>Rs. 5,06,03,333/-</b><br/><b>(Rs. 5.06 Crores)</b>", styles["TableCellBold"]), Paragraph("-", styles["TableCell"]), Paragraph("<font color='#047857'><b>Meets Tender Requirement<br/>(Min. Rs. 357.0 Lakhs)</b></font>", styles["TableCell"])],
    ]
    t_to = Table(to_table_data, colWidths=[90, 185, 120, 120])
    t_to.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A8A")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("BACKGROUND", (0, 5), (-1, 5), colors.HexColor("#ECFDF5")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t_to)
    story.append(Spacer(1, 10))

    story.append(Paragraph(
        "This certificate is issued at the specific request of the company for submission to the Office of the Comptroller & Auditor General of India.<br/>"
        "<b>Unique Document Identification Number (UDIN):</b> <b>21094812AAAAAK4918</b>",
        styles["BodyDark"]
    ))
    story.append(Spacer(1, 14))

    ca_sig = [
        [
            Paragraph("<b>Date:</b> 12th April 2021<br/><b>Place:</b> New Delhi", styles["BodyDark"]),
            Paragraph("<b>For Sharma & Singhal</b><br/>"
                      "Chartered Accountants (FRN: 014289N)<br/><br/>"
                      "<i>[DEMO CA SIGNATURE — SYNTHETIC]</i><br/>"
                      "<b>(CA. Alok Sharma, FCA)</b><br/>"
                      "Partner | Membership No. 094812<br/>"
                      "UDIN: 21094812AAAAAK4918", styles["SignatureBlock"]),
        ]
    ]
    t_ca = Table(ca_sig, colWidths=[200, 315])
    story.append(t_ca)

    # Page 2: Audited Financial Statements (FY 2019-20 P&L and Balance Sheet)
    # [NOTE: Discrepancy introduced: P&L revenue from operations states Rs. 5,40,25,000 vs CA Cert Rs. 6,20,40,000]
    story.append(PageBreak())
    story.extend(build_letterhead(styles))
    story.append(Paragraph("<b>AUDITED STATEMENT OF PROFIT AND LOSS FOR THE YEAR ENDED 31ST MARCH 2020</b>", styles["SectionHeading"]))
    story.append(Paragraph("<b>[Extract from Audited Financial Statements pursuant to Section 134 of the Companies Act, 2013]</b>", styles["LetterheadDetails"]))
    story.append(Spacer(1, 6))

    pl_table = [
        [Paragraph("<b>Particulars</b>", styles["TableHeader"]), Paragraph("<b>Note No.</b>", styles["TableHeader"]), Paragraph("<b>Year Ended 31.03.2020 (Rs.)</b>", styles["TableHeader"]), Paragraph("<b>Year Ended 31.03.2019 (Rs.)</b>", styles["TableHeader"])],
        [Paragraph("<b>I. Revenue from Operations</b>", styles["TableCellBold"]), Paragraph("18", styles["TableCell"]), Paragraph("<b>5,40,25,000</b>", styles["TableCellBold"]), Paragraph("4,85,20,000", styles["TableCell"])],
        [Paragraph("<b>II. Other Income</b> (Interest & Dividend)", styles["TableCell"]), Paragraph("19", styles["TableCell"]), Paragraph("18,40,200", styles["TableCell"]), Paragraph("12,15,400", styles["TableCell"])],
        [Paragraph("<b>III. Total Income (I + II)</b>", styles["TableCellBold"]), Paragraph("-", styles["TableCellBold"]), Paragraph("<b>5,58,65,200</b>", styles["TableCellBold"]), Paragraph("<b>4,97,35,400</b>", styles["TableCellBold"])],
        [Paragraph("<b>IV. Expenses:</b>", styles["TableCellBold"]), Paragraph("-", styles["TableCell"]), Paragraph("-", styles["TableCell"]), Paragraph("-", styles["TableCell"])],
        [Paragraph("  (a) Employee Benefits Expense (Salaries, EPF, ESI)", styles["TableCell"]), Paragraph("20", styles["TableCell"]), Paragraph("4,15,80,000", styles["TableCell"]), Paragraph("3,72,10,000", styles["TableCell"])],
        [Paragraph("  (b) Operational & Uniform Costs", styles["TableCell"]), Paragraph("21", styles["TableCell"]), Paragraph("38,50,000", styles["TableCell"]), Paragraph("34,20,000", styles["TableCell"])],
        [Paragraph("  (c) Finance Costs", styles["TableCell"]), Paragraph("22", styles["TableCell"]), Paragraph("8,40,000", styles["TableCell"]), Paragraph("7,90,000", styles["TableCell"])],
        [Paragraph("  (d) Depreciation & Amortization Expense", styles["TableCell"]), Paragraph("10", styles["TableCell"]), Paragraph("11,20,000", styles["TableCell"]), Paragraph("10,50,000", styles["TableCell"])],
        [Paragraph("  (e) Other Administrative Expenses", styles["TableCell"]), Paragraph("23", styles["TableCell"]), Paragraph("24,15,000", styles["TableCell"]), Paragraph("21,80,000", styles["TableCell"])],
        [Paragraph("<b>Total Expenses (IV)</b>", styles["TableCellBold"]), Paragraph("-", styles["TableCellBold"]), Paragraph("<b>4,98,05,000</b>", styles["TableCellBold"]), Paragraph("<b>4,46,50,000</b>", styles["TableCellBold"])],
        [Paragraph("<b>V. Profit Before Tax (III - IV)</b>", styles["TableCellBold"]), Paragraph("-", styles["TableCellBold"]), Paragraph("<b>60,60,200</b>", styles["TableCellBold"]), Paragraph("<b>50,85,400</b>", styles["TableCellBold"])],
        [Paragraph("<b>VI. Tax Expense (Current Tax + Deferred Tax)</b>", styles["TableCell"]), Paragraph("-", styles["TableCell"]), Paragraph("15,75,652", styles["TableCell"]), Paragraph("13,22,204", styles["TableCell"])],
        [Paragraph("<b>VII. Profit for the Year (V - VI)</b>", styles["TableCellBold"]), Paragraph("-", styles["TableCellBold"]), Paragraph("<b>44,84,548</b>", styles["TableCellBold"]), Paragraph("<b>37,63,196</b>", styles["TableCellBold"])],
    ]
    t_pl = Table(pl_table, colWidths=[200, 55, 130, 130])
    t_pl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A8A")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#FFFFFF"), colors.HexColor("#F8FAFC")]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
    ]))
    story.append(t_pl)
    story.append(Spacer(1, 8))

    story.append(Paragraph(
        "<b>Auditor's Note on Revenue:</b> Revenue from operations reflects contracted billings of deployed staff during the fiscal year. "
        "Subject to our statutory audit report of even date.",
        styles["BodyDark"]
    ))
    story.append(Spacer(1, 10))

    audit_sig = [
        [
            Paragraph("<b>For and on behalf of the Board:</b><br/>"
                      "<b>Rajesh K. Varma</b>, Managing Director<br/>"
                      "<b>Anita Varma</b>, Director<br/>"
                      "DIN: 07412895 / 07412899", styles["BodyDark"]),
            Paragraph("<b>As per our Report of even date:</b><br/>"
                      "<b>For Sharma & Singhal</b>, Chartered Accountants<br/>"
                      "CA. Alok Sharma, Partner (M.No. 094812)<br/>"
                      "FRN: 014289N | Date: 25.09.2020", styles["SignatureBlock"]),
        ]
    ]
    t_asig = Table(audit_sig, colWidths=[250, 265])
    story.append(t_asig)

    doc.build(story, canvasmaker=BidderDocumentCanvas)
    print("Generated:", pdf_path)


def generate_doc_04():
    """04_Past_Experience_Work_Orders_and_Completion.pdf"""
    pdf_path = OUTPUT_DIR / "04_Past_Experience_Work_Orders_and_Completion.pdf"
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        leftMargin=40,
        rightMargin=40,
        topMargin=50,
        bottomMargin=55,
    )
    styles = get_styles()
    story = []

    # Page 1: Past Experience Summary Table
    story.extend(build_letterhead(styles))
    story.append(Paragraph("<b>PAST EXPERIENCE DOSSIER: SIMILAR SERVICES IN GOVT / PSU (CLAUSE 4 OF PAGE 2)</b>", styles["SectionHeading"]))
    story.append(Paragraph("<b>Tender Requirement: One order of 80% (Rs. 5.71 Cr) OR Two orders of 50% (Rs. 3.57 Cr) OR Three orders of 40% (Rs. 2.85 Cr)</b>", styles["BodyDarkBold"]))
    story.append(Spacer(1, 6))

    exp_summary = [
        [Paragraph("<b>Project No.</b>", styles["TableHeader"]), Paragraph("<b>Client Organization & Department</b>", styles["TableHeader"]), Paragraph("<b>Contract Reference & Date</b>", styles["TableHeader"]), Paragraph("<b>Services Deployed</b>", styles["TableHeader"]), Paragraph("<b>Contract Value (Rs.)</b>", styles["TableHeader"]), Paragraph("<b>Completion Status</b>", styles["TableHeader"])],
        [
            Paragraph("<b>Project 1</b><br/>(Full Match)", styles["TableCellBold"]),
            Paragraph("Central Board of Direct Taxes (CBDT),<br/>Department of Revenue, Ministry of Finance", styles["TableCellBold"]),
            Paragraph("CBDT/AD-II/Manpower/2018-19/84<br/>Dated: 10.05.2018", styles["TableCell"]),
            Paragraph("95 Personnel (Clerical, DEOs, MTS)", styles["TableCell"]),
            Paragraph("<b>Rs. 3,82,50,000/-</b><br/>(Rs. 3.825 Cr)", styles["TableCellBold"]),
            Paragraph("<font color='#047857'><b>Completed 31.05.2020</b><br/>Certificate Attached</font>", styles["TableCell"]),
        ],
        [
            Paragraph("<b>Project 2</b><br/>(Meets 40% threshold)", styles["TableCellBold"]),
            Paragraph("Department for Promotion of Industry and Internal Trade (DPIIT), Ministry of Commerce", styles["TableCellBold"]),
            Paragraph("DPIIT/ESTT/MPS/2019/112<br/>Dated: 18.06.2019", styles["TableCell"]),
            Paragraph("72 Personnel (Outsourced Support Staff)", styles["TableCell"]),
            Paragraph("<b>Rs. 2,95,00,000/-</b><br/>(Rs. 2.950 Cr)", styles["TableCellBold"]),
            Paragraph("<font color='#047857'><b>Completed 31.07.2020</b><br/>Certificate Attached</font>", styles["TableCell"]),
        ],
        [
            Paragraph("<b>Project 3</b><br/>(Controlled Shortfall)", styles["TableCellBold"]),
            Paragraph("Steel Authority of India Limited (SAIL),<br/>Corporate Office, Scope Minar, Delhi", styles["TableCellBold"]),
            Paragraph("SAIL/CO/PERS/2019/54<br/>Dated: 14.10.2019", styles["TableCell"]),
            Paragraph("35 Personnel (Office Assistants)", styles["TableCell"]),
            Paragraph("<b>Rs. 1,90,00,000/-</b><br/>(Rs. 1.900 Cr)<br/><i>[Below 40% Threshold]</i>", styles["TableCellBold"]),
            Paragraph("<font color='#B91C1C'><b>Interim Letter Only</b><br/>Final Cert Missing</font>", styles["TableCell"]),
        ],
    ]
    t_es = Table(exp_summary, colWidths=[65, 120, 110, 85, 75, 60])
    t_es.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A8A")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#FFFFFF"), colors.HexColor("#F8FAFC")]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(t_es)
    story.append(Spacer(1, 10))

    story.append(Paragraph("<b>PROJECT 1: WORK ORDER & SATISFACTORY COMPLETION CERTIFICATE (CBDT)</b>", styles["SectionHeading"]))
    story.append(Paragraph("GOVERNMENT OF INDIA | MINISTRY OF FINANCE | CENTRAL BOARD OF DIRECT TAXES", styles["SubSectionHeading"]))
    story.append(Paragraph(
        "<b>Certificate Ref No:</b> CBDT/HQ/ADMN/COMPL/2020-21/189 &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <b>Dated:</b> 15th June 2020<br/><br/>"
        "This is to certify that <b>M/s Aravind Integrated Solutions Private Limited</b>, Suite 402, Pragati Deep Building, Laxmi Nagar, "
        "New Delhi has successfully executed the contract for 'Providing Out-sourced Manpower Services (Clerical, Data Entry Operators, and Multi-Tasking Staff)' "
        "awarded under Agreement No. CBDT/AD-II/Manpower/2018-19/84 dated 10.05.2018.<br/><br/>"
        "<b>Details of Contract Executed:</b><br/>"
        "• Period of Contract: 01.06.2018 to 31.05.2020 (24 months)<br/>"
        "• Total Value of Contract Executed: <b>Rs. 3,82,50,000/- (Rupees Three Crores Eighty Two Lakhs Fifty Thousand only)</b><br/>"
        "• Number of Personnel Deployed: 95 staff daily<br/>"
        "• Performance Assessment: <b>EXCELLENT AND SATISFACTORY</b>. Deployed staff maintained punctuality, strict confidentiality, and adherence to security protocols.<br/>"
        "• Statutory Compliance: The agency strictly disbursed minimum wages on time and deposited all EPF/ESI contributions regularly.",
        styles["BodyDark"]
    ))
    story.append(Spacer(1, 10))

    cbdt_sig = [
        [
            Paragraph("Official Seal:<br/>[SEAL: UNDER SECRETARY TO GOVT. OF INDIA, CBDT, NEW DELHI]", styles["SealNote"]),
            Paragraph("<i>[DEMO OFFICIAL SIGNATURE — SYNTHETIC]</i><br/>"
                      "<b>(V. R. Sundararajan)</b><br/>"
                      "Under Secretary to the Government of India<br/>"
                      "Central Board of Direct Taxes, North Block, New Delhi", styles["SignatureBlock"]),
        ]
    ]
    t_cbdt = Table(cbdt_sig, colWidths=[250, 265])
    story.append(t_cbdt)

    # Page 2: Project 2 (DPIIT) & Project 3 (SAIL)
    story.append(PageBreak())
    story.append(Paragraph("<b>PROJECT 2: WORK ORDER & SATISFACTORY COMPLETION CERTIFICATE (DPIIT)</b>", styles["SectionHeading"]))
    story.append(Paragraph("GOVERNMENT OF INDIA | MINISTRY OF COMMERCE & INDUSTRY | DPIIT", styles["SubSectionHeading"]))
    story.append(Paragraph(
        "<b>Certificate Ref No:</b> DPIIT/ADMIN/EVAL/2020/412 &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <b>Dated:</b> 30th August 2020<br/><br/>"
        "This is to certify that <b>M/s Aravind Integrated Solutions Pvt. Ltd.</b> has satisfactorily provided outsourced clerical and support manpower "
        "to the Department for Promotion of Industry and Internal Trade (DPIIT), Udyog Bhawan, New Delhi under Work Order DPIIT/ESTT/MPS/2019/112 dated 18.06.2019.<br/><br/>"
        "• Contract Duration: 01.07.2019 to 30.06.2020<br/>"
        "• Total Gross Amount Paid: <b>Rs. 2,95,00,000/- (Rupees Two Crores Ninety Five Lakhs only)</b><br/>"
        "• Deployed Workforce: 72 Skilled and Semi-Skilled Personnel<br/>"
        "• Quality of Service: <b>SATISFACTORY</b>. No penalties were levied during the contract period.",
        styles["BodyDark"]
    ))
    story.append(Spacer(1, 6))
    dpiit_sig = [
        [
            Paragraph("Official Seal:<br/>[SEAL: DEPUTY DIRECTOR, DPIIT, UDYOG BHAWAN, NEW DELHI]", styles["SealNote"]),
            Paragraph("<i>[DEMO OFFICIAL SIGNATURE — SYNTHETIC]</i><br/>"
                      "<b>(Manish K. Gupta)</b><br/>"
                      "Deputy Director (Establishment)<br/>"
                      "Department for Promotion of Industry & Internal Trade", styles["SignatureBlock"]),
        ]
    ]
    t_dpiit = Table(dpiit_sig, colWidths=[250, 265])
    story.append(t_dpiit)
    story.append(Spacer(1, 14))

    story.append(Paragraph("<b>PROJECT 3: INTERIM LETTER OF PERFORMANCE (SAIL) [PARTIAL EVIDENCE SCENARIO]</b>", styles["SectionHeading"]))
    story.append(Paragraph("STEEL AUTHORITY OF INDIA LIMITED | CORPORATE OFFICE, SCOPE MINAR, DELHI", styles["SubSectionHeading"]))
    story.append(Paragraph(
        "<b>Letter Ref No:</b> SAIL/PERS/CONTRACT/2020/981 &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <b>Dated:</b> 12th November 2020<br/><br/>"
        "To Whom It May Concern,<br/>"
        "This is an interim performance communication in respect of Work Order No. SAIL/CO/PERS/2019/54 dated 14.10.2019 awarded to "
        "M/s Aravind Integrated Solutions Pvt. Ltd. for providing office assistance personnel at Scope Minar, Laxmi Nagar, Delhi.<br/><br/>"
        "• Value of Work Order: <b>Rs. 1,90,00,000/- (Rupees One Crore Ninety Lakhs only)</b><br/>"
        "• Status: The services were provided during 2019-2020. Final reconciliation and audit of final bill is under process by finance.<br/>"
        "<i>[Note for Evaluation: Final Completion Certificate is not enclosed; this letter confirms interim engagement only.]</i>",
        styles["BodyDark"]
    ))
    story.append(Spacer(1, 6))
    sail_sig = [
        [
            Paragraph("Seal:<br/>[SEAL: SENIOR MANAGER (P&A), SAIL, SCOPE MINAR, DELHI]", styles["SealNote"]),
            Paragraph("<i>[DEMO OFFICIAL SIGNATURE — SYNTHETIC]</i><br/>"
                      "<b>(R. S. Narayanan)</b><br/>"
                      "Senior Manager (Personnel & Administration)<br/>"
                      "Steel Authority of India Limited", styles["SignatureBlock"]),
        ]
    ]
    t_sail = Table(sail_sig, colWidths=[250, 265])
    story.append(t_sail)

    doc.build(story, canvasmaker=BidderDocumentCanvas)
    print("Generated:", pdf_path)


def generate_doc_05():
    """05_Statutory_Affidavits_and_Compliance_Undertakings.pdf"""
    pdf_path = OUTPUT_DIR / "05_Statutory_Affidavits_and_Compliance_Undertakings.pdf"
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        leftMargin=40,
        rightMargin=40,
        topMargin=50,
        bottomMargin=55,
    )
    styles = get_styles()
    story = []

    # Page 1: Notarized Affidavit - Annexure-7 (Terms Acceptance) & Annexure-8 (Non-conviction / No relatives)
    story.append(Paragraph("INDIAN NON-JUDICIAL STAMP PAPER — GOVERNMENT OF NCT OF DELHI", styles["CoverSubTitle"]))
    story.append(Paragraph("Certificate No: IN-DL91820491829041T | Date: 16-Apr-2021 | Stamp Value: Rs. 10/-", styles["LetterheadDetails"]))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#0F172A"), spaceBefore=2, spaceAfter=8))

    story.append(Paragraph("<b>ANNEXURE-7: NOTARIZED AFFIDAVIT FOR ACCEPTANCE OF TERMS AND CONDITIONS</b>", styles["SectionHeading"]))
    story.append(Paragraph("<b>BEFORE THE NOTARY PUBLIC, AT NEW DELHI</b>", styles["LetterheadDetails"]))
    story.append(Spacer(1, 4))

    aff1_text = (
        "I, <b>Rajesh K. Varma</b>, S/o Shri K. L. Varma, aged about 48 years, residing at D-42, Anand Vihar, Delhi - 110092, "
        "Managing Director and Authorized Signatory of <b>M/s Aravind Integrated Solutions Private Limited</b>, do hereby solemnly "
        "affirm and declare on oath as under:<br/><br/>"
        "1. That I am fully authorized by the Board of Directors vide Resolution dated 05.04.2021 to sign and submit this affidavit on behalf of the company.<br/>"
        "2. That our company has thoroughly examined, verified, and accepted in toto all terms, conditions, specifications, GCC, SCC, "
        "and ATC of GeM Bid No. <b>GEM/2021/B/1128240</b> (Bid Document No. 46/GS/114-2021) issued by the Office of the Comptroller & Auditor General of India.<br/>"
        "3. That our company unconditionally agrees to comply with all operational directives, penalties, code of conduct, and reporting mechanisms."
    )
    story.append(Paragraph(aff1_text, styles["BodyDark"]))
    story.append(Spacer(1, 10))

    story.append(Paragraph("<b>ANNEXURE-8: NOTARIZED AFFIDAVIT FOR NON-CONVICTION & NO-RELATIVES DECLARATION</b>", styles["SectionHeading"]))
    aff2_text = (
        "4. That neither our firm <b>Aravind Integrated Solutions Private Limited</b> nor any of its Directors/Key Managerial Personnel "
        "has been convicted of any offense under the Indian Penal Code (IPC), the Prevention of Corruption Act, 1988, or any criminal enactment.<br/>"
        "5. That no Director, officer, or key personnel of our company has any near relative employed in any capacity in the Office of the "
        "Comptroller and Auditor General of India, New Delhi.<br/>"
        "6. That we have never been blacklisted, disqualified, or debarred by any Central/State Government Ministry, PSU, or autonomous body."
    )
    story.append(Paragraph(aff2_text, styles["BodyDark"]))
    story.append(Spacer(1, 12))

    notary_box = [
        [
            Paragraph("<b>DEPONENT</b><br/><br/>"
                      "<i>[DEMO SIGNATURE — SYNTHETIC]</i><br/>"
                      "<b>(Rajesh K. Varma)</b><br/>"
                      "Managing Director<br/>"
                      "Aravind Integrated Solutions Pvt. Ltd.", styles["BodyDarkBold"]),
            Paragraph("<b>ATTESTATION BY NOTARY PUBLIC</b><br/>"
                      "Solemnly affirmed and signed before me at New Delhi on this 16th day of April 2021.<br/>"
                      "<i>[DEMO NOTARY STAMP — SYNTHETIC]</i><br/>"
                      "<b>(R. P. Saxena)</b>, Advocate & Notary Public, Govt. of India<br/>"
                      "Registration No. 4819 / Delhi", styles["SealNote"]),
        ]
    ]
    t_not = Table(notary_box, colWidths=[240, 275])
    t_not.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOX", (1, 0), (1, 0), 0.5, colors.HexColor("#047857")),
        ("PADDING", (1, 0), (1, 0), 6),
    ]))
    story.append(t_not)

    # Page 2: Annexure-10 (Minimum Wages & Labour Compliance) + ISO 9001 Certificate + Technical Ambiguity Note
    story.append(PageBreak())
    story.append(Paragraph("INDIAN NON-JUDICIAL STAMP PAPER — GOVERNMENT OF NCT OF DELHI", styles["CoverSubTitle"]))
    story.append(Paragraph("Certificate No: IN-DL91820491829042U | Date: 16-Apr-2021 | Stamp Value: Rs. 10/-", styles["LetterheadDetails"]))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#0F172A"), spaceBefore=2, spaceAfter=8))

    story.append(Paragraph("<b>ANNEXURE-10: UNDERTAKING FOR COMPLIANCE WITH MINIMUM WAGES, EPF & ESIC</b>", styles["SectionHeading"]))
    story.append(Paragraph("<b>[Mandatory Statutory Undertaking pursuant to Clause 2(f) & Annexure-10]</b>", styles["LetterheadDetails"]))
    story.append(Spacer(1, 4))

    ann10_text = (
        "I, Rajesh K. Varma, Authorized Signatory of Aravind Integrated Solutions Private Limited, do hereby solemnly undertake and covenant that:<br/><br/>"
        "1. Our company maintains its own trained manpower on rolls and maintains strict compliance with the Minimum Wages Act, 1948.<br/>"
        "2. All personnel deployed under this contract (Unskilled Peon/MTS, Clerical/DEO, and Skilled Drivers) shall be disbursed monthly wages "
        "at rates <b>not less than the prevailing minimum rates of wages</b> notified by the Government of NCT of Delhi from time to time.<br/>"
        "3. Monthly wages shall be credited directly to the individual bank accounts of deployed staff via electronic NEFT/RTGS on or before the "
        "7th day of each following month, regardless of whether client payment has been released.<br/>"
        "4. Full statutory contributions towards Employees' Provident Fund (EPF), Employees' State Insurance (ESIC), and statutory bonus "
        "shall be deposited with concerned authorities by the 15th of every month without fail, and proof uploaded with monthly invoices.<br/>"
        "5. The company shall abide by all provisions of the Contract Labour (R&A) Act 1970, Equal Remuneration Act, and Delhi Shops & Establishments Act."
    )
    story.append(Paragraph(ann10_text, styles["BodyDark"]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("<b>ISO 9001:2015 CERTIFICATE OF REGISTRATION (BUYER ATC CLAUSE 5)</b>", styles["SectionHeading"]))
    iso_text = (
        "• Certification Body: <b>Universal Quality Registrar (UQR) Accredited by NABCB</b><br/>"
        "• Certificate Number: <b>QMS-2019-DEL-84920</b> | Original Issue Date: 18th July 2019 | Valid Till: 17th July 2022<br/>"
        "• Certified Entity: <b>Aravind Integrated Solutions Private Limited</b><br/>"
        "• Scope of Certification: <b>Provision of Outsourced Manpower Services, Facility Management, Technical Support & Office Assistance</b>.<br/>"
        "• Surveillance Audit Completed on: 10th June 2020 (Status: <font color='#047857'><b>CONFIRMED COMPLIANT</b></font>)."
    )
    story.append(Paragraph(iso_text, styles["BodyDark"]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("<b>TECHNICAL COMPETENCY & TYPING SKILL STATEMENT [CONTROLLED AMBIGUITY SCENARIO]</b>", styles["SectionHeading"]))
    ambiguity_text = (
        "With respect to Annexure-5 Deployment Schedule requiring Graduate Clerical / DEO staff to possess 15,000 key depressions per hour: "
        "<i>'The company confirms that all clerical and DEO staff proposed for deployment are screened and evaluated through the company's internal "
        "HR assessment procedures, and all candidates are found reasonably proficient in computer applications and document handling.'</i><br/>"
        "<i>[Note for Evaluation: Formal typing speed assessment logs or individual skill speed test certificates are not enclosed with this statement.]</i>"
    )
    story.append(Paragraph(ambiguity_text, styles["BodyDark"]))
    story.append(Spacer(1, 10))

    story.append(Paragraph("<b>Authorized Signatory:</b> Rajesh K. Varma (Managing Director) | Date: 16.04.2021", styles["SignatureBlock"]))
    story.append(Paragraph("<i>[NOTARY PUBLIC ATTESTED SEAL: DELHI JURISDICTION]</i>", styles["SealNote"]))

    # [NOTE: Annexure-9 Notarized Affidavit for VVIP/Sensitive Area Experience is intentionally omitted from this package]

    doc.build(story, canvasmaker=BidderDocumentCanvas)
    print("Generated:", pdf_path)


def generate_doc_06():
    """06_EMD_Bank_Guarantee_State_Bank_of_India.pdf"""
    pdf_path = OUTPUT_DIR / "06_EMD_Bank_Guarantee_State_Bank_of_India.pdf"
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        leftMargin=40,
        rightMargin=40,
        topMargin=50,
        bottomMargin=55,
    )
    styles = get_styles()
    story = []

    # Page 1: SBI Bank Guarantee Letterhead
    story.append(Paragraph("STATE BANK OF INDIA", styles["CoverTitle"]))
    story.append(Paragraph("COMMERCIAL BRANCH : 11, PARLIAMENT STREET / BARAKHAMBA ROAD, NEW DELHI - 110001<br/>IFSC: SBIN0000691 | Branch Code: 0691 | Email: sbi.00691@sbi.co.in.demo", styles["CoverSubTitle"]))
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#1E3A8A"), spaceBefore=2, spaceAfter=8))

    story.append(Paragraph("<b>EARNEST MONEY DEPOSIT (BID SECURITY) BANK GUARANTEE</b>", styles["CoverTitle"]))
    story.append(Paragraph("<b>[Issued as per Annexure-13 & GeM GTC / Clause 3 of Bid Document No. 46/GS/114-2021]</b>", styles["LetterheadDetails"]))
    story.append(Spacer(1, 6))

    bg_meta = [
        [Paragraph("<b>Bank Guarantee No:</b>", styles["TableCellBold"]), Paragraph("<b>0069121BG0004128</b>", styles["TableCellBold"]), Paragraph("<b>Date of Issue:</b>", styles["TableCellBold"]), Paragraph("15th April 2021", styles["TableCell"])],
        [Paragraph("<b>Guarantee Amount:</b>", styles["TableCellBold"]), Paragraph("<b>Rs. 35,73,639/-</b>", styles["TableCellBold"]), Paragraph("<b>Expiry Date:</b>", styles["TableCellBold"]), Paragraph("15th August 2021", styles["TableCell"])],
        [Paragraph("<b>Claim Lodgment Expiry:</b>", styles["TableCellBold"]), Paragraph("15th September 2021", styles["TableCell"]), Paragraph("<b>Beneficiary:</b>", styles["TableCellBold"]), Paragraph("PAO, Office of CAG of India", styles["TableCellBold"])],
    ]
    t_bg_meta = Table(bg_meta, colWidths=[120, 150, 110, 135])
    t_bg_meta.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(t_bg_meta)
    story.append(Spacer(1, 10))

    bg_text = (
        "<b>To,</b><br/>"
        "The Pay & Accounts Officer (PAO),<br/>"
        "Office of the Comptroller and Auditor General of India,<br/>"
        "Pocket-9, Deen Dayal Upadhyaya Marg, New Delhi - 110124.<br/><br/>"
        "WHEREAS <b>M/s Aravind Integrated Solutions Private Limited</b>, a company registered under the Companies Act 2013 and having "
        "its registered office at Suite 402, Pragati Deep Building, Laxmi Nagar, New Delhi - 110092 (hereinafter called 'the Bidder') has submitted "
        "its Bid dated 18.04.2021 in response to GeM Bid No. <b>GEM/2021/B/1128240</b> (Tender No. 46/GS/114-2021) for 'Hiring of Manpower Services'.<br/><br/>"
        "AND WHEREAS it is one of the conditions of the said Tender Document that the Bidder shall furnish an unconditional and irrevocable Bank Guarantee "
        "for an amount of <b>Rs. 35,73,639/- (Rupees Thirty Five Lakh Seventy Three Thousand Six Hundred Thirty Nine only)</b> as Earnest Money Deposit (5% of Estimated Value).<br/><br/>"
        "1. THEREFORE, WE, <b>State Bank of India</b>, Commercial Branch, Barakhamba Road, New Delhi, at the request of the Bidder, do hereby "
        "unconditionally and irrevocably guarantee and undertake to pay to the Beneficiary on demand without demur, reservation, contest, or protest, "
        "any sum or sums not exceeding in the total an amount of <b>Rs. 35,73,639/-</b> upon receipt of the Beneficiary's first written demand stating that:<br/>"
        "  (a) The Bidder has withdrawn or modified its bid during the period of bid validity (90 days); OR<br/>"
        "  (b) The Bidder, having been notified of the acceptance of its bid by the Client, fails or refuses to execute the Contract Agreement within stipulated time; OR<br/>"
        "  (c) The Bidder fails or refuses to furnish the Performance Bank Guarantee (10%) in accordance with the Bid Document.<br/><br/>"
        "2. Any such demand made on the Bank by the Beneficiary in writing shall be conclusive and binding upon the Bank, notwithstanding any dispute "
        "or proceedings pending before any Court, Tribunal, or Arbitrator.<br/><br/>"
        "3. This Guarantee shall remain in full force and effect up to <b>15th August 2021</b> (with a claim lodgment period up to 15th September 2021). "
        "Unless a claim or demand in writing is presented to the Bank on or before the said expiry date, all rights of the Beneficiary under this guarantee "
        "shall cease and the Bank shall be discharged from all liabilities."
    )
    story.append(Paragraph(bg_text, styles["BodyDark"]))
    story.append(Spacer(1, 14))

    sbi_sig = [
        [
            Paragraph("Bank Seal & Code:<br/>[STAMP: STATE BANK OF INDIA, COMMERCIAL BRANCH, NEW DELHI]<br/>SFMS Confirmation: SBIN0000691214819", styles["SealNote"]),
            Paragraph("<i>[DEMO BANK SIGNATURES — SYNTHETIC]</i><br/>"
                      "<b>1. (B. K. Nambiar)</b>, Chief Manager (Credit) | P.P. No. 49182<br/>"
                      "<b>2. (Sunil Sethi)</b>, Assistant General Manager | P.P. No. 38201<br/>"
                      "State Bank of India, Barakhamba Road, New Delhi", styles["SignatureBlock"]),
        ]
    ]
    t_sbi = Table(sbi_sig, colWidths=[250, 265])
    story.append(t_sbi)

    doc.build(story, canvasmaker=BidderDocumentCanvas)
    print("Generated:", pdf_path)


def generate_manifest():
    """manifest.json"""
    manifest_data = {
        "demo": True,
        "synthetic_data": True,
        "notice": "DEMO / SYNTHETIC DATA — FOR TESTING AND EVALUATION ONLY — NOT A REAL GOVERNMENT RECORD",
        "tender": {
            "file_name": "01_CAG_Manpower_Hiring_BidDoc_GEM_2021_B_1128240.pdf",
            "bid_number": "GEM/2021/B/1128240",
            "internal_document_no": "46/GS/114-2021",
            "title": "Hiring of Manpower Services (Un-skilled, Skilled and Clerical/Non-Technical Supervisory staff)",
            "issuing_authority": "Office of the Comptroller & Auditor General (CAG) of India, New Delhi",
            "ministry": "Comptroller And Auditor General Of India",
            "estimated_value": 71472780,
            "estimated_value_display": "₹7,14,72,780 (₹7.14 Cr)",
            "emd_amount": 3573639,
            "turnover_requirement_lakhs": 357.0,
            "past_experience_years": 3,
            "mse_exemption_permitted": False,
            "startup_exemption_permitted": False,
        },
        "bidder": {
            "legal_name": "Aravind Integrated Solutions Private Limited",
            "trade_name": "Aravind Integrated Solutions Pvt. Ltd.",
            "synthetic": True,
            "company_type": "Private Limited Company (Companies Act, 2013)",
            "incorporation_date": "2016-06-14",
            "cin": "U74999DL2016PTC301429",
            "pan": "AAACA9182K",
            "gstin": "07AAACA9182K1Z5",
            "epf_code": "DLCPM0094821000",
            "esic_code": "11000847290001001",
            "delhi_labour_license": "CLA/DLC/ND/2018/04291",
            "udyam_number": "UDYAM-DL-08-0042819",
            "registered_address": "Suite 402, 4th Floor, Pragati Deep Building, District Centre, Laxmi Nagar, New Delhi - 110092",
            "delhi_branch_address": "B-18, Ground Floor, Barakhamba Road, Connaught Place, New Delhi - 110001",
            "authorized_signatory": "Rajesh K. Varma (Managing Director, DIN: 07412895)",
            "contact_email": "tenders@aravindsolutions.in.demo",
            "contact_phone": "+91-11-48291040",
        },
        "documents": [
            {
                "file_name": "01_Bid_Submission_and_Technical_Bid_Form.pdf",
                "document_type": "BID_SUBMISSION_AND_TECHNICAL_FORM",
                "pages": 2,
                "description": "Annexure-1 Letter of Bid committing to 90 days validity & Annexure-6 Technical Bid Form with comprehensive bidder profile and checklist.",
            },
            {
                "file_name": "02_Company_Incorporation_and_Statutory_Registrations.pdf",
                "document_type": "STATUTORY_REGISTRATIONS_DOSSIER",
                "pages": 2,
                "description": "RoC Certificate of Incorporation, Delhi Office Proof, PAN Card, GSTIN Registration (with trade name variation), EPF, ESIC, and Delhi Labour License.",
            },
            {
                "file_name": "03_Financial_Turnover_and_Audited_Statements.pdf",
                "document_type": "FINANCIAL_TURNOVER_AND_AUDITED_STATEMENTS",
                "pages": 2,
                "description": "CA Turnover Certificate with UDIN certifying 3-year average of Rs. 5.06 Cr + Audited P&L showing FY 2019-20 operational revenue of Rs. 5.40 Cr.",
            },
            {
                "file_name": "04_Past_Experience_Work_Orders_and_Completion.pdf",
                "document_type": "PAST_EXPERIENCE_EVIDENCE",
                "pages": 2,
                "description": "Work Orders and Completion Certificates for Project 1 (CBDT, Rs. 3.82 Cr), Project 2 (DPIIT, Rs. 2.95 Cr), and Project 3 (SAIL, Rs. 1.90 Cr).",
            },
            {
                "file_name": "05_Statutory_Affidavits_and_Compliance_Undertakings.pdf",
                "document_type": "STATUTORY_AFFIDAVITS_AND_UNDERTAKINGS",
                "pages": 2,
                "description": "Annexure-7 (Terms Acceptance), Annexure-8 (Non-conviction/No relatives), Annexure-10 (Minimum Wages & Labour Compliance), ISO 9001:2015 Cert, and typing speed statement.",
            },
            {
                "file_name": "06_EMD_Bank_Guarantee_State_Bank_of_India.pdf",
                "document_type": "EARNEST_MONEY_DEPOSIT_BANK_GUARANTEE",
                "pages": 1,
                "description": "Original SBI Bank Guarantee for Rs. 35,73,639/- valid through 15.08.2021 in favour of PAO CAG.",
            },
        ],
        "intentional_findings": [
            {
                "type": "NAME_VARIATION",
                "details": "Legal name 'Aravind Integrated Solutions Private Limited' on Incorporation vs Trade Name 'Aravind Integrated Solutions Pvt. Ltd.' on GST and CA Certificate.",
                "expected_result": "MATCH_WITH_VARIATION / ACCEPTABLE_NORMALIZATION",
            },
            {
                "type": "FINANCIAL_DISCREPANCY",
                "details": "CA Certificate certifies FY 2019-20 turnover as Rs. 6,20,40,000/-, whereas Audited P&L reports Revenue from Operations as Rs. 5,40,25,000/- (Discrepancy: Rs. 80.15 Lakhs).",
                "expected_result": "DISCREPANCY_FLAGGED / OFFICER_REVIEW_REQUIRED",
            },
            {
                "type": "EXPERIENCE_PARTIALITY",
                "details": "Tender requires 1 order of 80% (Rs. 5.71 Cr) OR 2 orders of 50% (Rs. 3.57 Cr) OR 3 orders of 40% (Rs. 2.85 Cr). Project 3 (SAIL) is only Rs. 1.90 Cr and lacks a formal final completion certificate.",
                "expected_result": "PARTIAL_COMPLIANCE / DEFICIENCY_FLAGGED",
            },
            {
                "type": "MISSING_DOCUMENT",
                "details": "Annexure-9 Notarized Affidavit for VVIP / Sensitive Area Experience (Clause 2(d)(ii)) was not uploaded in the package.",
                "expected_result": "EVIDENCE_MISSING / MANDATORY_CRITERION_UNFULFILLED",
            },
            {
                "type": "TECHNICAL_AMBIGUITY",
                "details": "Annexure-5 specifies 15,000 key depressions/hour for clerical staff; bidder provides an in-house assertion without third-party skill certification or speed logs.",
                "expected_result": "CLARIFICATION_PENDING",
            },
            {
                "type": "EXTERNAL_VERIFICATION_LIMITATION",
                "details": "Synthetic GST/PAN/Udyam values are processed without claiming unauthenticated external government verification.",
                "expected_result": "SOURCE_ACCESS_NOT_CONFIGURED / MANUAL_VERIFICATION_ADVISED",
            },
        ],
    }

    out_file = OUTPUT_DIR / "manifest.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)
    print("Generated:", out_file)


def generate_requirement_evidence_matrix():
    """requirement_evidence_matrix.json"""
    matrix_data = [
        {
            "requirement_id": "REQ-CAG-01",
            "tender_clause": "Annexure-2, Clause 2(a) (Page 3 & 4)",
            "dimension": "ELIGIBILITY",
            "requirement": "The Bidder shall necessarily be a legally valid entity, either a Limited Company / Private Limited Company registered under the Companies Act, 2013, or an LLP under the LLP Act, 2008. JV/Consortium/Partnership/Proprietorship not permitted.",
            "is_mandatory": True,
            "required_evidence": ["Attested copy of Incorporation Certificate issued by RoC/MCA"],
            "submitted_documents": ["02_Company_Incorporation_and_Statutory_Registrations.pdf (Page 1)"],
            "extracted_value": "Private Limited Company incorporated on 14/06/2016 (CIN: U74999DL2016PTC301429)",
            "expected_status": "COMPLIANT",
            "expected_finding": "Valid legal entity incorporated under Companies Act 2013; no prohibited consortium/JV structure.",
            "verification_method": "MCA Incorporation Registry Structure Verification",
        },
        {
            "requirement_id": "REQ-CAG-02",
            "tender_clause": "Annexure-2, Clause 2(g) (Page 4)",
            "dimension": "ELIGIBILITY",
            "requirement": "The bidder should have its office located in Delhi / NCT of Delhi region. Documentary proof shall be submitted.",
            "is_mandatory": True,
            "required_evidence": ["Registered Lease Deed / Property Tax / Commercial Electricity Bill in Delhi"],
            "submitted_documents": ["02_Company_Incorporation_and_Statutory_Registrations.pdf (Page 1 & 2)"],
            "extracted_value": "Registered Office: Suite 402, Pragati Deep Building, Laxmi Nagar, New Delhi - 110092 + BSES Yamuna CA No. 102948190",
            "expected_status": "COMPLIANT",
            "expected_finding": "Registered office located within NCT of Delhi region as certified by MCA and municipal utility records.",
            "verification_method": "Documentary verification of Delhi municipal jurisdiction",
        },
        {
            "requirement_id": "REQ-CAG-03",
            "tender_clause": "Annexure-2, Clause 2(b) (Page 3 & 4)",
            "dimension": "STATUTORY",
            "requirement": "Registration under Income Tax (PAN), Goods and Services Tax (GST), Employees Provident Fund (EPF), Employees State Insurance (ESIC), and Labour License.",
            "is_mandatory": True,
            "required_evidence": ["PAN Card", "GST REG-06", "EPF Registration Code", "ESIC Employer Registration", "Delhi Labour License"],
            "submitted_documents": ["02_Company_Incorporation_and_Statutory_Registrations.pdf (Page 2)"],
            "extracted_value": "PAN: AAACA9182K | GST: 07AAACA9182K1Z5 | EPF: DLCPM0094821000 | ESIC: 11000847290001001 | Labour License: CLA/DLC/ND/2018/04291",
            "expected_status": "COMPLIANT",
            "expected_finding": "All five mandatory statutory registration certificates submitted; entity name exhibits minor 'Private Limited' vs 'Pvt. Ltd.' variation on GST.",
            "verification_method": "Format checking and statutory registration code validation",
        },
        {
            "requirement_id": "REQ-CAG-04",
            "tender_clause": "Bid Data Sheet & Annexure-2, Clause 2(e) (Page 1 & 4)",
            "dimension": "FINANCIAL",
            "requirement": "Minimum Average Annual Financial Turnover of Rs. 357.0 Lakhs in the similar business of providing manpower during last 3 financial years (2017-18, 2018-19, 2019-20).",
            "is_mandatory": True,
            "required_evidence": ["Certified Audited Balance Sheets", "CA Turnover Certificate with UDIN"],
            "submitted_documents": ["03_Financial_Turnover_and_Audited_Statements.pdf (Page 1 & 2)"],
            "extracted_value": "CA Certificate Turnover: FY 17-18 Rs. 4.12 Cr, FY 18-19 Rs. 4.85 Cr, FY 19-20 Rs. 6.20 Cr (Avg: Rs. 5.06 Cr). Audited P&L FY 19-20: Rs. 5.40 Cr.",
            "expected_status": "REVIEW",
            "expected_finding": "Average turnover exceeds threshold; however, an internal discrepancy of Rs. 80.15 Lakhs exists between CA Certificate (Rs. 6.20 Cr) and Audited P&L (Rs. 5.40 Cr) for FY 2019-20.",
            "verification_method": "Cross-examination of CA Certificate vs Audited P&L Statements",
        },
        {
            "requirement_id": "REQ-CAG-05",
            "tender_clause": "Bid Details & Clause 3, Annexure-2 (Page 1 & 4)",
            "dimension": "FINANCIAL",
            "requirement": "Earnest Money Deposit (EMD) of Rs. 35,73,639/- (5% of Estimated Value) via Bank Guarantee / DD from State Bank of India valid for 90 days + 30 days.",
            "is_mandatory": True,
            "required_evidence": ["Bank Guarantee from State Bank of India in favour of PAO CAG"],
            "submitted_documents": ["06_EMD_Bank_Guarantee_State_Bank_of_India.pdf (Page 1)"],
            "extracted_value": "SBI BG No: 0069121BG0004128 for Rs. 35,73,639/- valid up to 15.08.2021",
            "expected_status": "COMPLIANT",
            "expected_finding": "EMD Bank Guarantee matches exact required amount (Rs. 35,73,639/-), issued by required advisory bank (SBI), valid for 120 days.",
            "verification_method": "Bank Guarantee validity, amount, and advisory bank verification",
        },
        {
            "requirement_id": "REQ-CAG-06",
            "tender_clause": "Bid Data Sheet Page 2, Clause 4",
            "dimension": "EXPERIENCE",
            "requirement": "Executed at least 1 order of 80% (Rs. 5.71 Cr) OR 2 orders of 50% (Rs. 3.57 Cr) OR 3 orders of 40% (Rs. 2.85 Cr) for similar services in last 3 years to Govt/PSU with completion certificates.",
            "is_mandatory": True,
            "required_evidence": ["Contracts / Work Orders", "Documentary evidence of successful completion with client contact"],
            "submitted_documents": ["04_Past_Experience_Work_Orders_and_Completion.pdf (Page 1 & 2)"],
            "extracted_value": "Project 1 (CBDT): Rs. 3.82 Cr (Completed). Project 2 (DPIIT): Rs. 2.95 Cr (Completed). Project 3 (SAIL): Rs. 1.90 Cr (Interim letter only).",
            "expected_status": "NON_COMPLIANT",
            "expected_finding": "Does not satisfy 1x80% (no Rs. 5.71 Cr order), does not satisfy 2x50% (only 1 order exceeds Rs. 3.57 Cr), and fails 3x40% (Project 3 is Rs. 1.90 Cr vs min Rs. 2.85 Cr and lacks final completion certificate).",
            "verification_method": "Numerical threshold evaluation and completion certificate audit",
        },
        {
            "requirement_id": "REQ-CAG-07",
            "tender_clause": "Annexure-2, Clause 2(d)(ii) (Page 3)",
            "dimension": "EXPERIENCE",
            "requirement": "Experience in providing manpower services in any of the sensitive / VVIP areas like PMO, IB, Ministries/Departments of GOI, President's Secretariat, Parliament, Supreme Court, High Court, supported by Annexure-9 Notarized Affidavit.",
            "is_mandatory": True,
            "required_evidence": ["Annexure-9 Notarized Affidavit for VVIP/Sensitive Area Experience"],
            "submitted_documents": ["01_Bid_Submission_and_Technical_Bid_Form.pdf (Clause mentions)", "05_Statutory_Affidavits_and_Compliance_Undertakings.pdf"],
            "extracted_value": "VVIP experience mentioned informally in bid letter, but sworn Annexure-9 Notarized Affidavit is missing from dossier.",
            "expected_status": "NON_COMPLIANT",
            "expected_finding": "Mandatory Annexure-9 Notarized Affidavit for VVIP/Sensitive Area Experience was not submitted in the application pack.",
            "verification_method": "Mandatory checklist document presence audit",
        },
        {
            "requirement_id": "REQ-CAG-08",
            "tender_clause": "Annexure-2, Clause 2(f) & Annexure-10 (Page 4)",
            "dimension": "STATUTORY",
            "requirement": "Notarized affidavit and undertaking that workers employed would be paid at least minimum wages as per orders of Govt. of NCT of Delhi and oblige all statutory requirements (EPF/ESI).",
            "is_mandatory": True,
            "required_evidence": ["Annexure-10 Notarized Affidavit on Rs. 10 Stamp Paper"],
            "submitted_documents": ["05_Statutory_Affidavits_and_Compliance_Undertakings.pdf (Page 2)"],
            "extracted_value": "Annexure-10 Notarized Affidavit executed on Stamp Paper IN-DL91820491829042U committing to Delhi NCT minimum wages and 15th-of-month EPF/ESI deposits.",
            "expected_status": "COMPLIANT",
            "expected_finding": "Complete statutory undertaking furnished with explicit commitment to NCT of Delhi wage notifications.",
            "verification_method": "Legal text and notary attestation validation",
        },
        {
            "requirement_id": "REQ-CAG-09",
            "tender_clause": "Additional Terms & Conditions (ATC) Clause 5 (Page 2)",
            "dimension": "TECHNICAL",
            "requirement": "The bidder or the OEM of the offered products must have ISO 9001 certification.",
            "is_mandatory": True,
            "required_evidence": ["Valid ISO 9001:2015 Certificate"],
            "submitted_documents": ["05_Statutory_Affidavits_and_Compliance_Undertakings.pdf (Page 2)"],
            "extracted_value": "ISO 9001:2015 Certificate QMS-2019-DEL-84920 valid till 17.07.2022 for Manpower & Facility Management.",
            "expected_status": "COMPLIANT",
            "expected_finding": "Valid ISO 9001:2015 certificate from accredited body submitted covering outsourced manpower scope.",
            "verification_method": "Accreditation and validity date verification",
        },
        {
            "requirement_id": "REQ-CAG-10",
            "tender_clause": "Annexure-5 Schedule of Works / Services (Page 5)",
            "dimension": "TECHNICAL",
            "requirement": "Clerical/Non-Technical Graduate personnel must have MS Office proficiency and minimum 15,000 key depressions per hour typing speed.",
            "is_mandatory": True,
            "required_evidence": ["Typing speed certification / skill evaluation evidence"],
            "submitted_documents": ["05_Statutory_Affidavits_and_Compliance_Undertakings.pdf (Page 2)"],
            "extracted_value": "Self-declaration of internal in-house HR evaluation; no test certificates or speed logs attached.",
            "expected_status": "REVIEW",
            "expected_finding": "Technical ambiguity: Bidder claims in-house screening but omits objective third-party typing test reports or speed verification logs.",
            "verification_method": "Technical competency evidence audit",
        },
    ]

    out_file = OUTPUT_DIR / "requirement_evidence_matrix.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(matrix_data, f, indent=2)
    print("Generated:", out_file)


def generate_readme():
    """DEMO_APPLICATION_README.md"""
    content = """# BidGuard Synthetic Bidder Demo Application

## Tender Used

- **Tender Title**: Hiring of Manpower Services (Un-skilled, Skilled and Clerical/Non-Technical Supervisory staff)
- **Issuing Authority**: Office of the Comptroller & Auditor General (CAG) of India, New Delhi
- **Ministry**: Comptroller And Auditor General Of India
- **GeM Bid Number**: `GEM/2021/B/1128240`
- **Internal Bid Document No.**: `46/GS/114-2021`
- **Estimated Bid Value**: ₹7,14,72,780 (₹7.14 Cr)
- **EMD Required**: ₹35,73,639 (5.00%, State Bank of India)
- **Turnover Required**: ₹357.0 Lakhs (3-Year Average from Manpower Services)
- **Source File**: `backend/data/reference_tenders/01_CAG_Manpower_Hiring_BidDoc_GEM_2021_B_1128240.pdf`

## Synthetic Bidder Identity

- **Legal Entity Name**: `Aravind Integrated Solutions Private Limited`
- **Trade Name / Variation**: `Aravind Integrated Solutions Pvt. Ltd.`
- **Constitution**: Private Limited Company registered under Companies Act, 2013 on 14/06/2016
- **Synthetic CIN**: `U74999DL2016PTC301429`
- **Synthetic PAN**: `AAACA9182K`
- **Synthetic GSTIN**: `07AAACA9182K1Z5` (Delhi State Code: 07)
- **Synthetic EPF Code**: `DLCPM0094821000` (Delhi Central)
- **Synthetic ESIC Code**: `11000847290001001` (Delhi Sub-Region)
- **Delhi Labour License**: `CLA/DLC/ND/2018/04291`
- **Synthetic Notice**:
  > **[DEMO / SYNTHETIC DATA — FOR TESTING AND EVALUATION ONLY — NOT A REAL GOVERNMENT RECORD]**

## Submitted Bidder Application Documents

| File Name | Document Type | Pages | Key Evidence Provided |
| :--- | :--- | :---: | :--- |
| `01_Bid_Submission_and_Technical_Bid_Form.pdf` | Bid Submission & Technical Bid | 2 | Annexure-1 Letter of Bid, 90-day validity commitment, and Annexure-6 Technical Form with full bidder particulars and checklist. |
| `02_Company_Incorporation_and_Statutory_Registrations.pdf` | Corporate & Statutory Dossier | 2 | RoC Incorporation Certificate, Delhi registered office lease proof, PAN Card, GSTIN Registration (REG-06), EPF, ESIC, and Delhi Labour License. |
| `03_Financial_Turnover_and_Audited_Statements.pdf` | Financial Dossier | 2 | CA Turnover Certificate with UDIN: 21094812AAAAAK4918 certifying ₹5.06 Cr average + Audited Balance Sheet and P&L statements. |
| `04_Past_Experience_Work_Orders_and_Completion.pdf` | Experience Evidence | 2 | CBDT Project 1 (₹3.82 Cr + Completion Cert), DPIIT Project 2 (₹2.95 Cr + Completion Cert), and SAIL Project 3 (₹1.90 Cr + Interim letter). |
| `05_Statutory_Affidavits_and_Compliance_Undertakings.pdf` | Affidavits & Quality Dossier | 2 | Annexure-7 (Terms Acceptance), Annexure-8 (Non-conviction/No relatives), Annexure-10 (Minimum Wages & Labour Laws), ISO 9001:2015 Cert, and typing speed statement. |
| `06_EMD_Bank_Guarantee_State_Bank_of_India.pdf` | Bid Security (EMD) | 1 | Original SBI Bank Guarantee No. 0069121BG0004128 for ₹35,73,639/- valid through 15.08.2021 in favour of PAO CAG. |

## Controlled Verification Scenarios

| Scenario Type | Implementation in Demo Application | Expected BidGuard AI Evaluation Result |
| :--- | :--- | :--- |
| **A. Compliant Evidence** | Valid Certificate of Incorporation, PAN, EPF, ESIC, Delhi Labour License, Annexure-1, 7, 8, 10, ISO 9001:2015, and exact SBI EMD Bank Guarantee. | `COMPLIANT` with evidence citations and page references. |
| **B. Name Variation** | Incorporation has full name `Aravind Integrated Solutions Private Limited`; GST and CA certificate display `Aravind Integrated Solutions Pvt. Ltd.` | `MATCH_WITH_VARIATION` / fuzzy normalization; no false failure. |
| **C. Financial Discrepancy** | CA Certificate reports FY 2019-20 turnover as **₹6,20,40,000/-**, whereas Audited P&L schedule reports Revenue from Operations as **₹5,40,25,000/-** (discrepancy of ₹80.15 Lakhs). | `DISCREPANCY_FLAGGED` / `OFFICER_REVIEW_REQUIRED`. |
| **D. Experience Partiality** | Tender requires 1 order of 80% (₹5.71 Cr) OR 2 orders of 50% (₹3.57 Cr) OR 3 orders of 40% (₹2.85 Cr). Project 3 (SAIL) is only ₹1.90 Cr and lacks a formal completion certificate. | `PARTIAL` / `DEFICIENCY_FLAGGED`. |
| **E. Missing Document** | Mandatory Annexure-9 Notarized Affidavit for VVIP/Sensitive Area Experience (Clause 2(d)(ii)) is intentionally omitted from the submission pack. | `EVIDENCE_MISSING` / `MANDATORY_CRITERION_UNFULFILLED`. |
| **F. Technical Ambiguity** | Annexure-5 specifies 15,000 key depressions/hour for clerical staff; bidder provides an in-house self-assertion without third-party skill test certificates or speed logs. | `CLARIFICATION_PENDING`. |
| **G. External Verification Limitation** | Synthetic identifiers (PAN, GSTIN, Udyam) reflect realistic format but are not claimed as verified against live government APIs when connectors are unconfigured. | `NOT_CONFIGURED` / `MANUAL_VERIFICATION_ADVISED`. |

## End-to-End Demo Flow

```text
Tender Document (GEM/2021/B/1128240)
       ↓
Requirement Extraction (Clauses 2a-g, 3, 4, ATC)
       ↓
Bidder Application Upload (6 Multi-Page PDFs)
       ↓
Document Classification (LayoutLMv3 + TrOCR)
       ↓
Evidence Extraction & Chunking (BGE-Small 384-dim Embeddings)
       ↓
RAG Retrieval & Neural Reranking (ms-marco-MiniLM Cross-Encoder)
       ↓
Requirement / Evidence Cross-Examination (Qwen2.5-1.5B Non-Autonomous Prompting)
       ↓
Compliance Matrix & Discrepancy Detection (Flagging Financial Discrepancy & Missing Annexure-9)
       ↓
Officer Review Dashboard (Human Authority Decision Support)
```

## AI Components Used

All processing utilizes the **EXISTING** BidGuard AI implementation:
- `DocumentAIProvider`: LayoutLMv3 Base visual structure understanding
- `OCRProvider`: TrOCR Small Printed optical character recognition
- `EmbeddingProvider`: BAAI/bge-small-en-v1.5 dense vector embeddings (384-dim)
- `RerankerProvider`: cross-encoder/ms-marco-MiniLM-L-6-v2 cross-attention neural reranking
- `LLMProvider`: Qwen/Qwen2.5-1.5B-Instruct grounded analytical synthesis with non-autonomous guardrails
- `DocumentAgent`: Clause parsing and table isolation
- `RAGAgent`: Dense retrieval, reranking, and citation generation
- `AnalysisAgent`: Cross-examination, discrepancy flagging, and statutory auditing
- `AgentRouter`: Multi-agent intent classification and orchestration
- `AIAssistantService`: High-level chat, document analysis, and status checks

## Strict Non-Autonomous Procurement Safeguard

In accordance with public procurement laws (GFR 2017, Public Procurement Act) and BidGuard core architecture:
- BidGuard AI **NEVER** declares a winning bidder, recommends contract awards, or eliminates bidders autonomously.
- All evaluation outputs provide verifiable evidence citations (source document, page number, clause excerpt) and require final confirmation by authorized procurement officers.
"""
    out_file = OUTPUT_DIR / "DEMO_APPLICATION_README.md"
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(content)
    print("Generated:", out_file)


if __name__ == "__main__":
    generate_doc_01()
    generate_doc_02()
    generate_doc_03()
    generate_doc_04()
    generate_doc_05()
    generate_doc_06()
    generate_manifest()
    generate_requirement_evidence_matrix()
    generate_readme()
    print("Demo bidder package generation completed successfully!")

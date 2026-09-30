"""Generator script to build standardized PDF binaries of the authentic GeM tender collection.

Input sources:
    BidGuard_AI_Tender_Documents/
        01_CAG_Manpower_Hiring_BidDoc_46-GS-114-2021.txt
        02_AIIMS_Bhubaneswar_GeM_Bid_7437194.txt
        03_MIB_RRTD_Dashboard_GeM_Bid_5391658.txt
        04_PrasarBharati_Doordarshan_GeM_Bid_7439008.txt

Target output:
    backend/data/reference_tenders/
        01_CAG_Manpower_Hiring_BidDoc_GEM_2021_B_1128240.pdf
        02_AIIMS_Bhubaneswar_GeM_Bid_7437194.pdf
        03_MIB_RRTD_Dashboard_GeM_Bid_5391658.pdf
        04_PrasarBharati_Doordarshan_GeM_Bid_7439008.pdf
"""
import os
import re
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
)
from reportlab.pdfgen import canvas


class GeMNumberedCanvas(canvas.Canvas):
    """Canvas that computes total pages dynamically and adds GeM header/footer."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []
        self.doc_title = "Government e-Marketplace (GeM) Bid Document"

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
            self.drawString(54, 800, "GOVERNMENT E-MARKETPLACE (GeM) — OFFICIAL BID DOCUMENT")
            self.setFont("Helvetica", 7)
            self.setFillColor(colors.HexColor("#555555"))
            self.drawRightString(540, 800, getattr(self, "header_info", "GeM Bid Document"))
            self.setStrokeColor(colors.HexColor("#CCCCCC"))
            self.setLineWidth(0.5)
            self.line(54, 792, 540, 792)

        # Footer (all pages)
        self.setStrokeColor(colors.HexColor("#CCCCCC"))
        self.setLineWidth(0.5)
        self.line(54, 45, 540, 45)

        self.setFont("Helvetica", 7)
        self.setFillColor(colors.HexColor("#555555"))
        self.drawString(54, 34, "BidGuard AI Reference Repository | Authentic Government Tender Document")
        self.drawRightString(540, 34, f"Page {self._pageNumber} of {page_count}")
        self.restoreState()


def convert_text_tender_to_pdf(txt_path: Path, output_pdf_path: Path, title: str, bid_number: str, authority: str):
    """Convert a structured extracted text tender into an authentic, readable GeM PDF."""
    with open(txt_path, "r", encoding="utf-8") as f:
        raw_text = f.read()

    doc = SimpleDocTemplate(
        str(output_pdf_path),
        pagesize=A4,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54,
    )

    styles = getSampleStyleSheet()
    
    # Custom Typography
    title_style = ParagraphStyle(
        "GeMTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#0D3B66"),
        spaceAfter=6,
    )
    subtitle_style = ParagraphStyle(
        "GeMSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#2B2D42"),
        spaceAfter=12,
    )
    h1_style = ParagraphStyle(
        "GeMH1",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#0D3B66"),
        spaceBefore=10,
        spaceAfter=6,
    )
    h2_style = ParagraphStyle(
        "GeMH2",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#1D3557"),
        spaceBefore=8,
        spaceAfter=4,
    )
    body_style = ParagraphStyle(
        "GeMBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11.5,
        textColor=colors.HexColor("#222222"),
        spaceAfter=4,
    )
    code_style = ParagraphStyle(
        "GeMCode",
        parent=styles["Normal"],
        fontName="Courier",
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#333333"),
        spaceAfter=3,
    )

    story = []

    # Title Banner
    story.append(Paragraph(f"<b>Government e-Marketplace (GeM)</b>", title_style))
    story.append(Paragraph(f"<b>{title}</b>", h1_style))
    story.append(Paragraph(f"<b>Bid Number:</b> {bid_number} &nbsp;|&nbsp; <b>Issuing Authority:</b> {authority}", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#0D3B66"), spaceAfter=10))

    lines = raw_text.splitlines()
    in_header_block = True

    for line in lines:
        stripped = line.strip()
        if not stripped:
            story.append(Spacer(1, 4))
            continue

        if stripped.startswith("=====") or stripped.startswith("-----"):
            in_header_block = False
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#BDC3C7"), spaceAfter=6))
            continue

        if in_header_block and (stripped.startswith("SOURCE") or stripped.startswith("Retrieved via")):
            continue

        # Major Headings
        if (stripped.isupper() and len(stripped) > 4) or stripped.endswith(":") and len(stripped) < 60:
            story.append(Spacer(1, 6))
            story.append(Paragraph(stripped, h1_style))
            continue

        # Numbered Clauses
        if re.match(r"^\d+\.\s+", stripped):
            escaped = stripped.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            story.append(Paragraph(f"<b>{escaped}</b>", h2_style))
            continue

        # Sub-clauses or Bullet points
        if stripped.startswith("-") or stripped.startswith("•") or re.match(r"^\([a-z0-9]\)", stripped):
            escaped = stripped.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;{escaped}", body_style))
            continue

        # Key-value / Table-like lines
        if ":" in stripped and len(stripped.split(":")[0]) < 40:
            parts = stripped.split(":", 1)
            k = parts[0].strip().replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            v = parts[1].strip().replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            story.append(Paragraph(f"<b>{k}:</b> {v}", body_style))
            continue

        # Regular Body Text
        escaped = stripped.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        story.append(Paragraph(escaped, body_style))

    # Canvas customizer
    def make_canvas(*args, **kwargs):
        c = GeMNumberedCanvas(*args, **kwargs)
        c.header_info = f"{bid_number} | {authority[:35]}"
        return c

    doc.build(story, canvasmaker=make_canvas)
    print(f"Generated: {output_pdf_path} ({output_pdf_path.stat().st_size:,} bytes)")


def main():
    root_dir = Path(__file__).resolve().parent.parent.parent
    source_dir = root_dir / "BidGuard_AI_Tender_Documents"
    target_dir = root_dir / "backend" / "data" / "reference_tenders"
    target_dir.mkdir(parents=True, exist_ok=True)

    tenders = [
        {
            "txt_name": "01_CAG_Manpower_Hiring_BidDoc_46-GS-114-2021.txt",
            "pdf_name": "01_CAG_Manpower_Hiring_BidDoc_GEM_2021_B_1128240.pdf",
            "title": "Hiring of Manpower Services (Unskilled, Skilled, Clerical/Supervisory)",
            "bid_number": "GEM/2021/B/1128240",
            "authority": "Office of the Comptroller & Auditor General (CAG) of India",
        },
        {
            "txt_name": "02_AIIMS_Bhubaneswar_GeM_Bid_7437194.txt",
            "pdf_name": "02_AIIMS_Bhubaneswar_GeM_Bid_7437194.pdf",
            "title": "Supply of Acyclovir Tablets, Metoprolol Injection & Budesonide Solution",
            "bid_number": "GEM/2026/B/7437194",
            "authority": "AIIMS Bhubaneswar, Ministry of Health & Family Welfare",
        },
        {
            "txt_name": "03_MIB_RRTD_Dashboard_GeM_Bid_5391658.txt",
            "pdf_name": "03_MIB_RRTD_Dashboard_GeM_Bid_5391658.pdf",
            "title": "Custom Bid: Design, Development, Implementation & Maintenance of Integrated Dashboard",
            "bid_number": "GEM/2024/B/5391658",
            "authority": "RRTD, Ministry of Information and Broadcasting",
        },
        {
            "txt_name": "04_PrasarBharati_Doordarshan_GeM_Bid_7439008.txt",
            "pdf_name": "04_PrasarBharati_Doordarshan_GeM_Bid_7439008.pdf",
            "title": "Custom Bid: Electronic Program Guide (EPG) Service for DD Free Dish Channels",
            "bid_number": "GEM/2026/B/7439008",
            "authority": "Doordarshan (Prasar Bharati), DTH Todapur, New Delhi",
        },
    ]

    for t in tenders:
        src = source_dir / t["txt_name"]
        dst = target_dir / t["pdf_name"]
        if not src.exists():
            print(f"Error: Source file not found: {src}")
            continue
        convert_text_tender_to_pdf(
            txt_path=src,
            output_pdf_path=dst,
            title=t["title"],
            bid_number=t["bid_number"],
            authority=t["authority"],
        )


if __name__ == "__main__":
    main()

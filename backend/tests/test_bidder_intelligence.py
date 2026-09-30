import pytest
from pathlib import Path
import pypdf

from app.models.enums import BidderDocumentType, EntityType
from app.services.bidder_intelligence_service import (
    classify_bidder_document,
    extract_entities_from_text,
)


def test_classify_gst_certificate():
    text = "FORM GST REG-06 Government of India Registration Certificate GSTIN: 33AAACA1234A1Z5 Taxpayer Type: Regular"
    doc_type, conf = classify_bidder_document(text, "GST_Certificate.pdf")
    assert doc_type == BidderDocumentType.GST_CERTIFICATE
    assert conf >= 0.70


def test_classify_pan_card():
    text = "INCOME TAX DEPARTMENT GOVT OF INDIA Permanent Account Number PAN Card AAACA1234A"
    doc_type, conf = classify_bidder_document(text, "PAN_Card.pdf")
    assert doc_type == BidderDocumentType.PAN_CARD
    assert conf >= 0.70


def test_classify_udyam_certificate():
    text = "UDYAM REGISTRATION CERTIFICATE Ministry of Micro, Small and Medium Enterprises MSME Enterprise Type Small"
    doc_type, conf = classify_bidder_document(text, "Udyam_Certificate.pdf")
    assert doc_type == BidderDocumentType.UDYAM_CERTIFICATE
    assert conf >= 0.70


def test_classify_design_calculation():
    text = "PV Elite Mechanical Design Calculation ASME Section VIII Div 2 Maximum Allowable Working Pressure Stress Analysis"
    doc_type, conf = classify_bidder_document(text, "Design_Calculations.pdf")
    assert doc_type == BidderDocumentType.DESIGN_CALCULATION
    assert conf >= 0.70


def test_classify_integrity_pact():
    text = "INTEGRITY PACT between purchaser and bidder. Independent External Monitor (IEM) Shri R. K. Sharma. Commitments of the bidder."
    doc_type, conf = classify_bidder_document(text, "Integrity_Pact.pdf")
    assert doc_type == BidderDocumentType.INTEGRITY_PACT
    assert conf >= 0.70


def test_classify_zero_deviation():
    text = "Zero Deviation Confirmation Certificate. We confirm compliance without any deviation, caveat or exception."
    doc_type, conf = classify_bidder_document(text, "Zero_Deviation.pdf")
    assert doc_type == BidderDocumentType.ZERO_DEVIATION_DECLARATION
    assert conf >= 0.70


def test_extract_gstin_pan_udyam():
    sample_text = (
        "The bidder Apex Heavy Engineering Private Limited has GSTIN 33AAACA1234A1Z5 "
        "and PAN AAACA1234A. Registered with Udyam under number UDYAM-TN-02-0012345."
    )
    entities = extract_entities_from_text(sample_text, page_number=1)
    
    types = {e["entity_type"] for e in entities}
    values = {e["normalized_value"] for e in entities}

    assert EntityType.GSTIN in types
    assert "33AAACA1234A1Z5" in values

    assert EntityType.PAN in types
    assert "AAACA1234A" in values

    assert EntityType.UDYAM_NUMBER in types
    assert "UDYAM-TN-02-0012345" in values


def test_extract_technical_metrics():
    sample_text = (
        "High pressure separator designed for design pressure: 68.0 bar(g) "
        "with shell thickness: 48.0 mm and hydrotest pressure: 88.4 bar(g). "
        "Built under ASME 'U2' Code authorization."
    )
    entities = extract_entities_from_text(sample_text, page_number=2)

    pressures = [e["normalized_value"] for e in entities if e["entity_type"] == EntityType.PRESSURE_VALUE]
    thicknesses = [e["normalized_value"] for e in entities if e["entity_type"] == EntityType.THICKNESS_VALUE]
    asme = [e["normalized_value"] for e in entities if e["entity_type"] == EntityType.ASME_STAMP]

    assert any("68.0 bar(g)" in p or "68.0" in p for p in pressures)
    assert any("48.0 mm" in t for t in thicknesses)
    assert any("U2" in a for a in asme)


def test_extract_entities_from_demo_bidder_a_pdfs():
    """Verify that generated Bidder A PDFs contain valid extractable entities."""
    base_dir = Path("data/demo_bidders/bidder_a_compliant")
    assert base_dir.is_dir()

    # Test GST PDF
    gst_pdf = base_dir / "GST_Certificate.pdf"
    assert gst_pdf.is_file()
    reader = pypdf.PdfReader(str(gst_pdf))
    text = reader.pages[0].extract_text()
    entities = extract_entities_from_text(text)
    
    gst_found = any(e["entity_type"] == EntityType.GSTIN and e["normalized_value"] == "33AAACA1234A1Z5" for e in entities)
    assert gst_found, f"GSTIN not found in {text}"

    # Test Udyam PDF
    udyam_pdf = base_dir / "Udyam_Certificate.pdf"
    reader = pypdf.PdfReader(str(udyam_pdf))
    text = reader.pages[0].extract_text()
    entities = extract_entities_from_text(text)
    
    udyam_found = any(e["entity_type"] == EntityType.UDYAM_NUMBER and e["normalized_value"] == "UDYAM-TN-02-0012345" for e in entities)
    assert udyam_found, f"Udyam not found in {text}"

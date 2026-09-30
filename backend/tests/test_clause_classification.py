import pytest
from app.models.enums import ClauseCategory
from app.services.clause_extraction_service import classify_clause


def test_classify_administrative():
    text = "The bid validity shall be strictly 120 days from the date of opening. Any communication regarding tender queries should be addressed to the designated nodal officer."
    cat, conf = classify_clause(text, title="Bid Validity and Communication")
    assert cat == ClauseCategory.ADMINISTRATIVE
    assert conf >= 0.70


def test_classify_statutory():
    text = "Bidder must furnish valid GSTIN registration certificate and PAN copy. The establishment must comply with statutory requirements under the MSME Act and EPF regulations."
    cat, conf = classify_clause(text, title="Statutory Registrations")
    assert cat == ClauseCategory.STATUTORY
    assert conf >= 0.75


def test_classify_technical():
    text = "All fabrication shall comply with ASME Section VIII Div 1. The GA drawing, bill of materials (BOM), and 100% NDT radiography test report must be submitted for engineer review."
    cat, conf = classify_clause(text, title="Technical Specifications and Welding Procedures")
    assert cat == ClauseCategory.TECHNICAL
    assert conf >= 0.80


def test_classify_commercial():
    text = "100% payment terms within 30 days of receipt of invoice. Delivery period shall be 6 weeks. Liquidated damages of 0.5% per week subject to a maximum penalty of 10% shall apply."
    cat, conf = classify_clause(text, title="Payment Terms & Liquidated Damages")
    assert cat == ClauseCategory.COMMERCIAL
    assert conf >= 0.80


def test_classify_financial():
    text = "The bidder shall have an average annual turnover of at least INR 5 Crores during the last 3 financial years. Earnest Money Deposit (EMD) and Performance Bank Guarantee (PBG) of 5% are mandatory."
    cat, conf = classify_clause(text, title="Annual Turnover and PBG Requirement")
    assert cat == ClauseCategory.FINANCIAL
    assert conf >= 0.80


def test_classify_eligibility():
    text = "Bidders must have prior experience in completing similar work for government refineries. The firm should not be debarred or blacklisted by any PSU or central ministry."
    cat, conf = classify_clause(text, title="Qualification and Eligibility Criteria")
    assert cat == ClauseCategory.ELIGIBILITY
    assert conf >= 0.75


def test_classify_submission():
    text = "The tender follows a two-bid envelope system. Unpriced techno-commercial bid and priced bid must be submitted online along with the signed integrity pact and sworn affidavit."
    cat, conf = classify_clause(text, title="Mode of Submission and Checklist of Documents")
    assert cat == ClauseCategory.SUBMISSION
    assert conf >= 0.80


def test_classify_general_fallback():
    text = "In this tender document, words importing the singular shall also include the plural and vice versa unless context requires otherwise."
    cat, conf = classify_clause(text, title="Interpretation and Definitions")
    assert cat == ClauseCategory.GENERAL
    assert conf == 0.50


def test_title_weight_boost():
    """Verify that title keywords strongly drive categorization even if body has mixed text."""
    title = "Statutory GST and PAN Compliance"
    text = "General procedures to be followed by the vendor during supply."
    cat, conf = classify_clause(text, title=title)
    assert cat == ClauseCategory.STATUTORY
    assert conf >= 0.70

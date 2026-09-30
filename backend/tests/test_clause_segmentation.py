import uuid
import pytest

from app.services.clause_extraction_service import (
    _match_clause_header,
    normalize_text,
    segment_pages_into_clauses,
)


def test_normalize_text():
    """Verify whitespace, non-breaking spaces, and excessive line breaks are normalized."""
    raw = "  Clause   1.0   \t  \r\n\r\n\r\n  This is   a test.   \n\n\n  Subclause (a)   "
    normalized = normalize_text(raw)
    assert "  " not in normalized.replace("\n", "")
    assert "\r" not in normalized
    assert normalized == "Clause 1.0\n\nThis is a test.\n\nSubclause (a)"


def test_header_matching_numbered():
    """Test numbered patterns like 1., 1.1, 2.1.3."""
    # 1. Number with title
    match1 = _match_clause_header("1. General Conditions")
    assert match1 is not None
    num, title, body = match1
    assert num == "1"
    assert title == "General Conditions"

    # 1.1 Nested number
    match2 = _match_clause_header("1.1 Scope of Work")
    assert match2 is not None
    num, title, _ = match2
    assert num == "1.1"
    assert title == "Scope of Work"

    # 2.1.3 Multi-level
    match3 = _match_clause_header("2.1.3 Radiography Examination Requirements")
    assert match3 is not None
    num, title, _ = match3
    assert num == "2.1.3"
    assert title == "Radiography Examination Requirements"


def test_header_matching_explicit_prefix():
    """Test explicit prefixes like Clause 1, Section 2:, Article 3."""
    match1 = _match_clause_header("Clause 1.0 Payment Terms")
    assert match1 is not None
    assert match1[0] == "Clause 1.0"
    assert match1[1] == "Payment Terms"

    match2 = _match_clause_header("Section 2: Technical Specifications")
    assert match2 is not None
    assert match2[0] == "Section 2"
    assert match2[1] == "Technical Specifications"

    match3 = _match_clause_header("Article 4 Special Conditions")
    assert match3 is not None
    assert match3[0] == "Article 4"
    assert match3[1] == "Special Conditions"


def test_header_matching_lists():
    """Test list markers like (a), (i), A."""
    match_a = _match_clause_header("(a) Bidder shall provide valid GSTIN.")
    assert match_a is not None
    assert match_a[0] == "(a)"
    assert "Bidder shall provide" in match_a[2]

    match_roman = _match_clause_header("(ii) Minimum 3 years of continuous manufacturing experience.")
    assert match_roman is not None
    assert match_roman[0] == "(ii)"
    assert "Minimum 3 years" in match_roman[2]


def test_header_matching_uppercase_headings():
    """Test standard uppercase and predefined section headers."""
    match1 = _match_clause_header("ELIGIBILITY CRITERIA")
    assert match1 is not None
    assert match1[1] == "ELIGIBILITY CRITERIA"

    match2 = _match_clause_header("PAYMENT TERMS:")
    assert match2 is not None
    assert match2[1] == "PAYMENT TERMS"

    match3 = _match_clause_header("TECHNICAL SPECIFICATIONS")
    assert match3 is not None
    assert match3[1] == "TECHNICAL SPECIFICATIONS"


def test_multiple_clauses_on_single_page():
    """Test segmenting multiple distinct clauses residing on the same page."""
    doc_id = uuid.uuid4()
    page_id = uuid.uuid4()
    page_text = """
    1.0 Eligibility Requirements
    The bidder must be an OEM or authorized partner.
    
    2.0 Payment Terms
    100% payment upon final site inspection and acceptance.
    
    3.0 Delivery Schedule
    Equipment must be delivered within 8 weeks from order date.
    """
    pages_data = [(doc_id, page_id, 1, page_text)]
    clauses = segment_pages_into_clauses(pages_data)

    assert len(clauses) == 3
    assert clauses[0].clause_number == "1.0"
    assert clauses[0].title == "Eligibility Requirements"
    assert "OEM or authorized partner" in clauses[0].get_full_text()
    assert clauses[0].page_number == 1

    assert clauses[1].clause_number == "2.0"
    assert clauses[1].title == "Payment Terms"
    assert "100% payment" in clauses[1].get_full_text()

    assert clauses[2].clause_number == "3.0"
    assert clauses[2].title == "Delivery Schedule"
    assert "8 weeks" in clauses[2].get_full_text()


def test_multi_page_clause_continuation():
    """Test that a clause starting on page 1 continues across page 2 until a new header starts."""
    doc_id = uuid.uuid4()
    p1_id = uuid.uuid4()
    p2_id = uuid.uuid4()

    p1_text = """
    Section 4.1 Technical Pressure Vessel Design Calculations
    The fabricator shall compute wall thickness in accordance with ASME Sec VIII Div 1.
    All design load combinations including internal pressure and wind load must be
    """
    p2_text = """
    evaluated using finite element analysis where nozzle openings exceed 200mm diameter.
    
    Section 4.2 Non-Destructive Testing
    All circumferential weld joints shall be subjected to 100% radiographic examination.
    """

    pages_data = [
        (doc_id, p1_id, 1, p1_text),
        (doc_id, p2_id, 2, p2_text),
    ]
    clauses = segment_pages_into_clauses(pages_data)

    assert len(clauses) == 2
    # First clause originated on page 1
    c1 = clauses[0]
    assert c1.clause_number == "Section 4.1"
    assert c1.title == "Technical Pressure Vessel Design Calculations"
    assert c1.page_number == 1
    assert c1.page_id == p1_id
    full_c1_text = c1.get_full_text()
    assert "ASME Sec VIII Div 1" in full_c1_text
    assert "finite element analysis" in full_c1_text  # Proves continuation across page 2 boundary

    # Second clause started on page 2
    c2 = clauses[1]
    assert c2.clause_number == "Section 4.2"
    assert c2.title == "Non-Destructive Testing"
    assert c2.page_number == 2
    assert c2.page_id == p2_id
    assert "100% radiographic examination" in c2.get_full_text()


def test_irregular_whitespace_and_empty_pages():
    """Verify robust handling of empty pages and strange whitespace in PDF text."""
    doc_id = uuid.uuid4()
    pages_data = [
        (doc_id, uuid.uuid4(), 1, "   \n\n   "),  # blank page
        (doc_id, uuid.uuid4(), 2, "Clause 1.0\t\tAdministrative Details\n  Submission by  speed  post.\n\n"),
        (doc_id, uuid.uuid4(), 3, ""),  # completely empty page
    ]
    clauses = segment_pages_into_clauses(pages_data)
    assert len(clauses) == 1
    assert clauses[0].clause_number == "Clause 1.0"
    assert clauses[0].page_number == 2
    assert "Submission by speed post." in clauses[0].get_full_text()

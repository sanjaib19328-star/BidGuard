import json
from pathlib import Path
import uuid
import pypdf
import pytest

from app.models.enums import ClauseCategory
from app.services.clause_extraction_service import (
    classify_clause,
    segment_pages_into_clauses,
)


def test_gem_tenders_and_manifest_exist():
    ref_dir = Path(__file__).resolve().parent.parent / "data" / "reference_tenders"
    manifest_path = ref_dir / "gem_tender_manifest.json"

    assert manifest_path.exists(), "Manifest gem_tender_manifest.json must exist."
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    assert "tenders" in manifest
    assert len(manifest["tenders"]) == 5, "Expected 4 GeM tenders + 1 CPCL package"

    expected_files = [
        "01_CAG_Manpower_Hiring_BidDoc_GEM_2021_B_1128240.pdf",
        "02_AIIMS_Bhubaneswar_GeM_Bid_7437194.pdf",
        "03_MIB_RRTD_Dashboard_GeM_Bid_5391658.pdf",
        "04_PrasarBharati_Doordarshan_GeM_Bid_7439008.pdf",
        "CPCL_EIL_B649_Pressure_Vessel_RFQ_Tendernotice_1.pdf",
    ]

    manifest_files = [t["file_name"] for t in manifest["tenders"]]
    for ef in expected_files:
        assert ef in manifest_files, f"Expected {ef} in manifest."
        pdf_file = ref_dir / ef
        assert pdf_file.exists(), f"PDF binary {ef} must exist in reference_tenders."


def test_gem_tenders_pdf_readability():
    ref_dir = Path(__file__).resolve().parent.parent / "data" / "reference_tenders"
    gem_files = [
        "01_CAG_Manpower_Hiring_BidDoc_GEM_2021_B_1128240.pdf",
        "02_AIIMS_Bhubaneswar_GeM_Bid_7437194.pdf",
        "03_MIB_RRTD_Dashboard_GeM_Bid_5391658.pdf",
        "04_PrasarBharati_Doordarshan_GeM_Bid_7439008.pdf",
    ]

    for f_name in gem_files:
        pdf_path = ref_dir / f_name
        reader = pypdf.PdfReader(str(pdf_path))
        assert len(reader.pages) > 0, f"{f_name} must have at least 1 page"
        text = "".join([p.extract_text() or "" for p in reader.pages])
        assert len(text.strip()) > 100, f"{f_name} text extraction failed or is empty"
        assert "Government e-Marketplace" in text or "GeM" in text


def test_cag_tender_clause_extraction():
    ref_dir = Path(__file__).resolve().parent.parent / "data" / "reference_tenders"
    cag_pdf = ref_dir / "01_CAG_Manpower_Hiring_BidDoc_GEM_2021_B_1128240.pdf"

    reader = pypdf.PdfReader(str(cag_pdf))
    doc_id = uuid.uuid4()
    pages = [(doc_id, uuid.uuid4(), idx + 1, p.extract_text() or "") for idx, p in enumerate(reader.pages)]
    clauses = segment_pages_into_clauses(pages)
    assert len(clauses) > 0, "Failed to segment clauses from authentic CAG tender PDF"

    # Verify extracted clauses match expected procurement requirements
    combined_text = " ".join([c.get_full_text() for c in clauses]).lower()
    assert "turnover" in combined_text
    assert "experience" in combined_text
    assert "emd" in combined_text


def test_aiims_tender_clause_extraction_and_classification():
    ref_dir = Path(__file__).resolve().parent.parent / "data" / "reference_tenders"
    aiims_pdf = ref_dir / "02_AIIMS_Bhubaneswar_GeM_Bid_7437194.pdf"

    reader = pypdf.PdfReader(str(aiims_pdf))
    doc_id = uuid.uuid4()
    pages = [(doc_id, uuid.uuid4(), idx + 1, p.extract_text() or "") for idx, p in enumerate(reader.pages)]
    clauses = segment_pages_into_clauses(pages)
    assert len(clauses) > 0, "Failed to segment clauses from authentic AIIMS tender PDF"

    combined_text = " ".join([c.get_full_text() for c in clauses]).lower()
    assert "mse" in combined_text
    assert "relaxation" in combined_text or "exemption" in combined_text

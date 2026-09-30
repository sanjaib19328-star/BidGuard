import pytest
from app.models.enums import NameMatchVerdict
from app.services.name_matching_service import (
    NameMatchResult,
    compare_legal_names,
    extract_legal_entity_types,
    normalize_legal_name,
)


def test_normalize_legal_name():
    raw = "  Apex Heavy Engineering Pvt. Ltd. (Chennai)  "
    norm = normalize_legal_name(raw)
    assert "private limited" in norm
    assert "apex heavy engineering" in norm
    assert "(" not in norm
    assert "." not in norm


def test_exact_name_match():
    name1 = "Apex Heavy Engineering Private Limited"
    name2 = "Apex Heavy Engineering Private Limited"
    res = compare_legal_names(name1, name2)
    assert res.verdict == NameMatchVerdict.EXACT_MATCH
    assert res.score == 1.0
    assert res.is_acceptable is True


def test_formatting_difference_pvt_ltd():
    name1 = "Apex Heavy Engineering Pvt. Ltd."
    name2 = "APEX HEAVY ENGINEERING PRIVATE LIMITED"
    res = compare_legal_names(name1, name2)
    assert res.verdict in (
        NameMatchVerdict.EXACT_MATCH,
        NameMatchVerdict.FORMATTING_VARIATION,
    )
    assert res.score >= 0.95
    assert res.is_acceptable is True


def test_minor_variation():
    name1 = "Bharat Vessels and Fabrication Works Private Limited"
    name2 = "Bharat Vessel & Fabrication Works Pvt Ltd"
    res = compare_legal_names(name1, name2)
    assert res.verdict in (
        NameMatchVerdict.FORMATTING_VARIATION,
        NameMatchVerdict.MINOR_VARIATION,
    )
    assert res.score >= 0.80
    assert res.is_acceptable is True


def test_moderate_variation():
    name1 = "Coromandel Process Systems Private Limited"
    name2 = "Coromandel Process Equipments India Private Limited"
    res = compare_legal_names(name1, name2)
    assert res.verdict in (
        NameMatchVerdict.MINOR_VARIATION,
        NameMatchVerdict.POTENTIAL_MISMATCH,
    )
    assert res.score >= 0.55


def test_serious_mismatch():
    name1 = "Apex Heavy Engineering Private Limited"
    name2 = "Delta Steel Fabricators Private Limited"
    res = compare_legal_names(name1, name2)
    assert res.verdict == NameMatchVerdict.SERIOUS_MISMATCH
    assert res.score < 0.60
    assert res.is_acceptable is False


def test_entity_type_conflict_llp_vs_pvt_ltd():
    # If one is an LLP and the other is a Private Limited, even with same name prefix,
    # it must be flagged as a legal discrepancy.
    name1 = "Coromandel Process Systems LLP"
    name2 = "Coromandel Process Systems Private Limited"
    res = compare_legal_names(name1, name2)
    assert res.verdict == NameMatchVerdict.SERIOUS_MISMATCH
    assert res.score <= 0.50
    assert res.is_acceptable is False
    assert any("Legal entity type mismatch detected" in d for d in res.discrepancies)


def test_empty_or_none_handling():
    res1 = compare_legal_names("", "Apex Heavy Engineering")
    assert res1.verdict == NameMatchVerdict.SERIOUS_MISMATCH
    assert res1.score == 0.0

    res2 = compare_legal_names(None, "Apex Heavy Engineering")
    assert res2.verdict == NameMatchVerdict.SERIOUS_MISMATCH
    assert res2.score == 0.0

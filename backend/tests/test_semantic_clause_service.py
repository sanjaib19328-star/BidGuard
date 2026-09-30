import pytest
from app.services.semantic_clause_service import (
    SemanticClauseService,
    tokenize,
    build_tf_vector,
    cosine_similarity,
)


def test_tokenize_and_vector():
    tokens = tokenize("Annual Turnover must exceed INR 357 Lakhs in the last 3 financial years.")
    assert "turnover" in tokens
    assert "357" in tokens
    assert "lakhs" in tokens

    vec = build_tf_vector(tokens)
    assert "turnover" in vec
    assert vec["turnover"] > 0


def test_cosine_similarity():
    v1 = {"turnover": 0.5, "inr": 0.5}
    v2 = {"turnover": 0.5, "inr": 0.5}
    assert cosine_similarity(v1, v2) == pytest.approx(1.0)

    v3 = {"completely": 0.5, "different": 0.5}
    assert cosine_similarity(v1, v3) == 0.0


def test_classify_clause_semantics():
    cat, conf = SemanticClauseService.classify_clause_semantics(
        text="Bidder must submit valid GSTIN registration and PAN card.",
        title="Statutory Registrations",
    )
    assert cat == "STATUTORY"
    assert conf > 0.60

    cat_tech, conf_tech = SemanticClauseService.classify_clause_semantics(
        text="Design pressure of pressure vessel shall be at least 68 bar(g) with MAWP calculation.",
        title="Technical Scope",
    )
    assert cat_tech == "TECHNICAL"
    assert conf_tech > 0.60


def test_match_evidence_to_requirement():
    req = "Minimum design pressure 68 bar(g) required for vessel design"
    ev = "Hydrotest calculation verified at 68.0 bar(g) MAWP per ASME Sec VIII"
    score, details = SemanticClauseService.match_evidence_to_requirement(req, ev)
    assert score > 0.40
    assert details["acceptable"] is True
    assert details["number_match"] is True

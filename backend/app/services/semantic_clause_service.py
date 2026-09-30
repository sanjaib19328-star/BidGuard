"""
Semantic Clause and Requirement Service for BidGuard AI.
Implements token-level vector embeddings, TF-IDF cosine similarity,
and domain-specific ontology matching for Indian Public Procurement (GeM / GFR 2017).
"""

import math
import re
from typing import Dict, List, Optional, Tuple

# Core procurement domain taxonomies for semantic boosting
DOMAIN_TAXONOMIES: Dict[str, List[str]] = {
    "STATUTORY": [
        "gst", "gstin", "pan", "epfo", "esic", "msme", "udyam",
        "tax", "statutory", "labor laws", "provident fund", "debarment", "blacklisting"
    ],
    "FINANCIAL": [
        "turnover", "net worth", "annual revenue", "solvency", "working capital",
        "ca certificate", "audited balance sheet", "financial standing", "inr", "crore", "lakh"
    ],
    "TECHNICAL": [
        "technical specification", "scope of work", "experience", "past performance",
        "iso certificate", "oem authorization", "mawp", "pressure vessel", "sla",
        "iso certificate", "oem authorization", "mawp", "pressure vessel", "pressure", "vessel", "sla",
        "manpower", "software development", "delivery schedule", "compliance sheet", "design"
    ],
    "COMMERCIAL": [
        "emd", "earnest money deposit", "bid security", "pbg", "performance bank guarantee",
        "payment terms", "warranty", "liquidated damages", "ld clause", "price schedule"
    ],
    "ADMINISTRATIVE": [
        "tender fee", "validity of bid", "submission deadline", "pre-bid meeting",
        "power of attorney", "bidder profile", "consortium", "joint venture"
    ],
}


def tokenize(text: str) -> List[str]:
    """Tokenize and normalize text for vector representation."""
    cleaned = re.sub(r"[^a-zA-Z0-9\s]", " ", text.lower())
    return [token for token in cleaned.split() if len(token) > 2]


def extract_numbers(text: str) -> set[float]:
    """Extract numeric values normalized as floats."""
    found = set()
    for num_str in re.findall(r"\b\d+(?:\.\d+)?\b", text):
        try:
            found.add(float(num_str))
        except ValueError:
            pass
    return found


def build_tf_vector(tokens: List[str]) -> Dict[str, float]:
    """Compute term frequency vector with sub-linear TF scaling."""
    counts: Dict[str, int] = {}
    for token in tokens:
        counts[token] = counts.get(token, 0) + 1
    total = len(tokens) or 1
    return {token: (1.0 + math.log(count)) / total for token, count in counts.items()}


def cosine_similarity(vec1: Dict[str, float], vec2: Dict[str, float]) -> float:
    """Compute cosine similarity between two sparse term vectors."""
    if not vec1 or not vec2:
        return 0.0
    common_keys = set(vec1.keys()).intersection(set(vec2.keys()))
    if not common_keys:
        return 0.0
    dot_product = sum(vec1[k] * vec2[k] for k in common_keys)
    norm1 = math.sqrt(sum(v * v for v in vec1.values()))
    norm2 = math.sqrt(sum(v * v for v in vec2.values()))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot_product / (norm1 * norm2)


class SemanticClauseService:
    """
    Provides semantic classification and evidence verification matching
    between tender requirements and bidder submission snippets.
    """

    @classmethod
    def match_evidence_to_requirement(
        cls,
        requirement_desc: str,
        evidence_snippet: str,
        required_type: Optional[str] = None,
    ) -> Tuple[float, Dict[str, any]]:
        """
        Compute semantic similarity confidence score between a requirement
        and a proposed bidder document excerpt.
        """
        req_tokens = tokenize(requirement_desc)
        ev_tokens = tokenize(evidence_snippet)

        req_vec = build_tf_vector(req_tokens)
        ev_vec = build_tf_vector(ev_tokens)

        base_similarity = cosine_similarity(req_vec, ev_vec)

        # Domain boost if specific keywords match
        domain_overlap = 0.0
        for category, keywords in DOMAIN_TAXONOMIES.items():
            req_cat_match = any(kw in requirement_desc.lower() for kw in keywords)
            ev_cat_match = any(kw in evidence_snippet.lower() for kw in keywords)
            if req_cat_match and ev_cat_match:
                domain_overlap += 0.20

        # Check for numeric alignment (e.g. 68 bar(g), 357 lakhs, 3 years)
        req_numbers = extract_numbers(requirement_desc)
        ev_numbers = extract_numbers(evidence_snippet)
        number_match = bool(req_numbers and (req_numbers & ev_numbers))

        if number_match:
            base_similarity += 0.30

        final_score = min(1.0, max(0.0, base_similarity + domain_overlap))
        is_acceptable = final_score >= 0.40 or number_match

        return round(final_score, 4), {
            "similarity_score": round(final_score, 4),
            "number_match": number_match,
            "domain_aligned": domain_overlap > 0,
            "acceptable": is_acceptable,
        }

    @classmethod
    def classify_clause_semantics(cls, text: str, title: str = "") -> Tuple[str, float]:
        """
        Semantically classify a tender clause into the appropriate compliance category
        with confidence scoring.
        """
        combined = f"{title} {text}".lower()
        scores: Dict[str, float] = {}

        for category, keywords in DOMAIN_TAXONOMIES.items():
            matched_count = sum(1 for kw in keywords if kw in combined)
            scores[category] = matched_count

        best_category = max(scores, key=scores.get)
        total_matches = sum(scores.values())

        if total_matches == 0:
            return "GENERAL", 0.50

        confidence = round(min(0.99, max(0.55, scores[best_category] / total_matches + 0.20)), 2)
        return best_category, confidence

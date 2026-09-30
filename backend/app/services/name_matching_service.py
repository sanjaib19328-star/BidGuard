import difflib
import re
from typing import List, NamedTuple, Set, Tuple
from app.models.enums import NameMatchVerdict


class NameMatchResult(NamedTuple):
    verdict: NameMatchVerdict
    score: float
    reason: str

    @property
    def is_acceptable(self) -> bool:
        return self.verdict in (
            NameMatchVerdict.EXACT_MATCH,
            NameMatchVerdict.FORMATTING_VARIATION,
            NameMatchVerdict.MINOR_VARIATION,
        )

    @property
    def discrepancies(self) -> List[str]:
        if not self.is_acceptable:
            return [self.reason]
        return []


# Common business suffixes and abbreviations mapped to canonical forms
SUFFIX_MAPPINGS = [
    (r"\b(pvt\.?\s*ltd\.?|private\s+limited)\b", "private limited"),
    (r"\b(ltd\.?|limited)\b", "limited"),
    (r"\b(llp|l\.l\.p\.?|limited\s+liability\s+partnership)\b", "llp"),
    (r"\b(corp\.?|corporation)\b", "corporation"),
    (r"\b(inc\.?|incorporated)\b", "incorporated"),
    (r"\b(co\.?|company)\b", "company"),
    (r"\b(mfg\.?|manufacturing)\b", "manufacturing"),
    (r"\b(engg\.?|engineering)\b", "engineering"),
    (r"\b(ind\.?|industries)\b", "industries"),
    (r"\b(sys\.?|systems)\b", "systems"),
    (r"\b(ent\.?|enterprises)\b", "enterprises"),
]

LEGAL_STRUCTURES = {"private limited", "limited", "llp", "corporation", "proprietorship", "partnership"}


def normalize_entity_name(name: str) -> str:
    """Normalize company name by standardizing legal suffixes, removing punctuation, and collapsing whitespace."""
    if not name:
        return ""

    text = name.lower().strip()
    # Replace common symbol equivalents
    text = text.replace("&", " and ")
    
    # Standardize suffixes using regex
    for pattern, replacement in SUFFIX_MAPPINGS:
        text = re.sub(pattern, replacement, text)

    # Remove all punctuation except alphanumeric and whitespace
    text = re.sub(r"[^\w\s]", " ", text)
    # Collapse multiple whitespaces
    text = re.sub(r"\s+", " ", text).strip()
    return text


normalize_legal_name = normalize_entity_name


def extract_legal_structure(normalized_name: str) -> str:
    """Detect the legal entity form if present in the normalized name."""
    if "private limited" in normalized_name:
        return "private limited"
    elif "llp" in normalized_name:
        return "llp"
    elif "limited" in normalized_name:
        return "limited"
    elif "corporation" in normalized_name:
        return "corporation"
    return "unspecified"


extract_legal_entity_types = extract_legal_structure


def get_core_tokens(normalized_name: str) -> Set[str]:
    """Extract significant tokens excluding generic legal terms and single characters."""
    tokens = set(normalized_name.split())
    # Remove generic legal filler
    stop_words = {"and", "the", "of", "in", "for", "a", "an"}
    return {t for t in tokens if t not in stop_words and len(t) > 1}


def compare_legal_names(name1: str, name2: str) -> NameMatchResult:
    """Compare two organization names and return the verdict, similarity score, and explanation."""
    if not name1 or not name2:
        return NameMatchResult(NameMatchVerdict.SERIOUS_MISMATCH, 0.0, "One or both names are missing")

    # Exact raw match
    if name1.strip().lower() == name2.strip().lower():
        return NameMatchResult(NameMatchVerdict.EXACT_MATCH, 1.0, "Exact character match")

    norm1 = normalize_entity_name(name1)
    norm2 = normalize_entity_name(name2)

    # Exact normalized match
    if norm1 == norm2:
        return NameMatchResult(NameMatchVerdict.FORMATTING_VARIATION, 0.98, "Match after standardizing abbreviations, punctuation, and casing")

    # Check for fundamental entity type divergence (e.g. LLP vs Private Limited)
    type1 = extract_legal_structure(norm1)
    type2 = extract_legal_structure(norm2)
    entity_type_divergence = (type1 != "unspecified" and type2 != "unspecified" and type1 != type2)

    # Calculate token overlap (Jaccard similarity)
    tokens1 = get_core_tokens(norm1)
    tokens2 = get_core_tokens(norm2)
    
    if not tokens1 or not tokens2:
        jaccard = 0.0
    else:
        intersection = tokens1.intersection(tokens2)
        union = tokens1.union(tokens2)
        jaccard = len(intersection) / len(union)

    # Calculate SequenceMatcher string similarity
    string_ratio = difflib.SequenceMatcher(None, norm1, norm2).ratio()

    # Weighted combined score
    combined_score = round(0.5 * jaccard + 0.5 * string_ratio, 4)

    # If entity structure conflicts (e.g. LLP vs Private Limited), maximum verdict is SERIOUS_MISMATCH
    if entity_type_divergence:
        return NameMatchResult(
            NameMatchVerdict.SERIOUS_MISMATCH,
            min(combined_score, 0.50),
            f"Legal entity type mismatch detected: '{type1.upper()}' vs '{type2.upper()}'",
        )

    # Verdict classification
    if combined_score >= 0.90:
        return NameMatchResult(NameMatchVerdict.FORMATTING_VARIATION, combined_score, "High-confidence match with minor formatting or punctuation differences")
    elif combined_score >= 0.78:
        return NameMatchResult(NameMatchVerdict.MINOR_VARIATION, combined_score, "Substantial token and stem overlap with acceptable abbreviations")
    elif combined_score >= 0.55:
        return NameMatchResult(NameMatchVerdict.POTENTIAL_MISMATCH, combined_score, "Partial match; officer review required to confirm legal entity identity")
    else:
        return NameMatchResult(NameMatchVerdict.SERIOUS_MISMATCH, combined_score, "Significant discrepancy between registered names")


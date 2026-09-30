import hashlib
import re
import uuid
from typing import Any, Dict, List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.clause import TenderClause
from app.models.enums import (
    ClauseCategory,
    RequirementApplicability,
    RequirementOperator,
    RequirementType,
    RiskHint,
    VerificationMethod,
)
from app.models.requirement import TenderRequirement
from app.services.audit_service import log_audit_event
from app.services.tender_service import get_tender_by_id


# ==============================================================================
# 1. Candidate Detection
# ==============================================================================

RE_OBLIGATION = re.compile(
    r"\b(?:shall|must|mandatory|compulsory|required|stipulated|obligat(?:ed|ion))\b",
    re.IGNORECASE,
)

RE_REQUIREMENT_KEYWORDS = re.compile(
    r"\b(?:"
    r"turnover|net\s+worth|experience|similar\s+(?:works?|projects?|orders?)|"
    r"gstin?|pan(?:\s+(?:card|number))?|license|licence|oem|authori[sz]ation|"
    r"specification|datasheet|welding|radiograph|hydrostatic|asme|is\s+code|"
    r"payment\s+terms?|delivery\s+(?:period|schedule)|warranty|liquidated\s+damages?|"
    r"emd|bid\s+security|pbg|performance\s+security|performance\s+bank\s+guarantee|"
    r"declaration|affidavit|integrity\s+pact|blacklisted?|debarred|"
    r"minimum|maximum|at\s+least|not\s+less\s+than|not\s+more\s+than|exceeding|"
    r"eligib(?:le|ility)|qualification"
    r")\b",
    re.IGNORECASE,
)

INFORMATIONAL_ONLY = [
    r"^this\s+tender\s+(?:was|is)\s+published",
    r"^table\s+of\s+contents",
    r"^tender\s+notice\s+details",
    r"^press\s+release",
]


def is_requirement_candidate(clause_text: str, title: Optional[str] = None) -> bool:
    """Determine whether a clause is a candidate containing verifiable procurement requirements."""
    full_text = f"{title or ''} {clause_text}".strip()
    if not full_text or len(full_text) < 15:
        return False

    # Filter out purely informational clauses
    lowered = full_text.lower()
    for pattern in INFORMATIONAL_ONLY:
        if re.search(pattern, lowered):
            return False

    # Check for obligation verbs or procurement keywords
    if RE_OBLIGATION.search(full_text) or RE_REQUIREMENT_KEYWORDS.search(full_text):
        return True

    return False


# ==============================================================================
# 2. Operator Extractor
# ==============================================================================

OPERATOR_PATTERNS = [
    (re.compile(r"\b(?:at\s+least|minimum|not\s+less\s+than|no\s+less\s+than|min\.?)\b", re.I), ">="),
    (re.compile(r"\b(?:maximum|not\s+more\s+than|not\s+exceeding|no\s+more\s+than|within|up\s+to|max\.?)\b", re.I), "<="),
    (re.compile(r"\b(?:more\s+than|greater\s+than|(?<!not\s)(?<!no\s)exceeding|strictly\s+above)\b", re.I), ">"),
    (re.compile(r"\b(?:strictly\s+less\s+than|below)\b", re.I), "<"),
    (re.compile(r"\b(?:equal\s+to|exactly)\b", re.I), "="),
    (re.compile(r"\b(?:prohibited|strictly\s+forbidden|not\s+allowed|disqualified)\b", re.I), "PROHIBITED"),
    (re.compile(r"\b(?:optional|may\s+submit|recommended)\b", re.I), "OPTIONAL"),
    (re.compile(r"\b(?:mandatory|compulsory|required|must\s+possess|must\s+submit|shall\s+submit)\b", re.I), "REQUIRED"),
]


def extract_operator(text: str) -> Optional[str]:
    """Extract normalized comparison operator from text."""
    for pattern, op_val in OPERATOR_PATTERNS:
        if pattern.search(text):
            return op_val
    return "REQUIRED"


# ==============================================================================
# 3. Numeric, Unit & Currency Extractor
# ==============================================================================

WORD_NUMBERS = {
    "one": 1.0,
    "two": 2.0,
    "three": 3.0,
    "four": 4.0,
    "five": 5.0,
    "six": 6.0,
    "seven": 7.0,
    "eight": 8.0,
    "nine": 9.0,
    "ten": 10.0,
    "twelve": 12.0,
    "twenty": 20.0,
    "twenty-five": 25.0,
    "thirty": 30.0,
    "sixty": 60.0,
    "ninety": 90.0,
}


def _parse_num(val_str: str) -> Optional[float]:
    """Convert number string or word to float."""
    try:
        return float(val_str.replace(",", ""))
    except ValueError:
        return WORD_NUMBERS.get(val_str.lower().strip())


def extract_numeric_and_unit(text: str) -> Tuple[Optional[float], Optional[str], Optional[str]]:
    """Extract scalar value, unit, and currency from procurement clause text.
    
    Returns:
        (value_numeric, unit, currency)
    """
    # 1. Indian Currency: Crores (e.g. ₹10 crore, Rs. 10 Crores, INR 10 Cr, 10 Crore)
    match_cr = re.search(
        r"(?:₹|rs\.?|inr)?\s*([0-9]+(?:\.[0-9]+)?|[a-z\-]+)\s*(?:cr(?:ore)?s?|crores?)\b",
        text,
        re.IGNORECASE,
    )
    if match_cr:
        val = _parse_num(match_cr.group(1))
        if val is not None:
            return val, "CRORE_INR", "INR"

    # 2. Indian Currency: Lakhs (e.g. ₹500 lakh, Rs 50 Lakhs, 500 lacs)
    match_lakh = re.search(
        r"(?:₹|rs\.?|inr)?\s*([0-9]+(?:\.[0-9]+)?|[a-z\-]+)\s*(?:lakh?s?|lacs?)\b",
        text,
        re.IGNORECASE,
    )
    if match_lakh:
        val = _parse_num(match_lakh.group(1))
        if val is not None:
            return val, "LAKH_INR", "INR"

    # 3. Standard INR currency with direct number (e.g. ₹50,000, Rs. 10000)
    match_inr = re.search(
        r"(?:₹|rs\.?|inr)\s*([0-9]+(?:,[0-9]{3})*(?:\.[0-9]+)?)\b",
        text,
        re.IGNORECASE,
    )
    if match_inr:
        val = _parse_num(match_inr.group(1))
        if val is not None:
            return val, "INR", "INR"

    # 4. Time: Years (e.g. 5 years, 3 financial years, three years)
    match_years = re.search(
        r"\b([0-9]+(?:\.[0-9]+)?|[a-z\-]+)\s*(?:financial\s+)?(?:years?|yrs?)\b",
        text,
        re.IGNORECASE,
    )
    if match_years:
        val = _parse_num(match_years.group(1))
        if val is not None:
            return val, "YEARS", None

    # 5. Time: Months (e.g. 12 months, 6 months, twelve months)
    match_months = re.search(
        r"\b([0-9]+(?:\.[0-9]+)?|[a-z\-]+)\s*(?:months?|mos?)\b",
        text,
        re.IGNORECASE,
    )
    if match_months:
        val = _parse_num(match_months.group(1))
        if val is not None:
            return val, "MONTHS", None

    # 6. Time: Days (e.g. 90 days, 120 days, within 30 days)
    match_days = re.search(
        r"\b([0-9]+(?:\.[0-9]+)?|[a-z\-]+)\s*(?:days?)\b",
        text,
        re.IGNORECASE,
    )
    if match_days:
        val = _parse_num(match_days.group(1))
        if val is not None:
            return val, "DAYS", None

    # 7. Percentage (e.g. 25%, 0.5%, 10 percent)
    match_pct = re.search(
        r"\b([0-9]+(?:\.[0-9]+)?)\s*(?:%|\bpercent(?:age)?\b)",
        text,
        re.IGNORECASE,
    )
    if match_pct:
        val = _parse_num(match_pct.group(1))
        if val is not None:
            return val, "PERCENT", None

    # 8. Projects / Works count (e.g. 3 similar works, at least two projects)
    match_proj = re.search(
        r"\b([0-9]+|[a-z\-]+)\s*(?:similar\s+)?(?:works?|projects?|contracts?|orders?)\b",
        text,
        re.IGNORECASE,
    )
    if match_proj:
        val = _parse_num(match_proj.group(1))
        if val is not None:
            return val, "PROJECTS", None

    # 9. Units count (e.g. 100 units, 50 nos)
    match_units = re.search(
        r"\b([0-9]+)\s*(?:units?|nos?\.?|items?|pieces?)\b",
        text,
        re.IGNORECASE,
    )
    if match_units:
        val = _parse_num(match_units.group(1))
        if val is not None:
            return val, "UNITS", None

    return None, None, None


# ==============================================================================
# 4. Period Extractor
# ==============================================================================

def extract_period(text: str) -> Optional[str]:
    """Extract explicit time period when specified in requirement."""
    # Last 3 financial years
    if re.search(r"\b(?:last|previous|preceding)\s+(?:3|three)\s+(?:financial\s+)?years\b", text, re.I):
        return "LAST_3_FINANCIAL_YEARS"

    # Previous 5 years
    if re.search(r"\b(?:last|previous|preceding)\s+(?:5|five)\s+(?:financial\s+)?years\b", text, re.I):
        return "PREVIOUS_5_YEARS"

    # Generic financial years
    m_fy = re.search(r"\b(?:last|previous|preceding)\s+([0-9]+)\s+(?:financial\s+)?years\b", text, re.I)
    if m_fy:
        return f"LAST_{m_fy.group(1)}_FINANCIAL_YEARS"

    # Within N days
    m_within = re.search(r"\bwithin\s+([0-9]+)\s+days\b", text, re.I)
    if m_within:
        return f"WITHIN_{m_within.group(1)}_DAYS"

    # Validity N days
    m_valid = re.search(r"\b(?:valid\s+(?:for|upto)|validity\s+(?:of)?)\s*([0-9]+)\s*days\b", text, re.I)
    if m_valid:
        return f"VALIDITY_{m_valid.group(1)}_DAYS"

    return None


# ==============================================================================
# 5. Mandatory Detection
# ==============================================================================

RE_MANDATORY_WORDS = re.compile(
    r"\b(?:shall|must|mandatory|compulsory|required|strictly\s+required|obligation)\b",
    re.IGNORECASE,
)

RE_OPTIONAL_WORDS = re.compile(
    r"\b(?:may|optional|preferable|recommended|discretionary|not\s+mandatory)\b",
    re.IGNORECASE,
)


def detect_mandatory(text: str) -> Optional[bool]:
    """Detect mandatory status: True for mandatory, False for optional, None for ambiguous."""
    if RE_MANDATORY_WORDS.search(text):
        return True
    if RE_OPTIONAL_WORDS.search(text):
        return False
    return None


# ==============================================================================
# 6. Applicability Detection
# ==============================================================================

def detect_applicability(text: str) -> Tuple[RequirementApplicability, Optional[str]]:
    """Determine who the requirement applies to and preserve conditions if any."""
    # 1. Conditional statements
    m_cond = re.search(
        r"\b(if\s+(?:the\s+)?bidder\s+is\s+[^,\.;]+|in\s+case\s+of\s+[^,\.;]+|where\s+applicable|if\s+applicable)\b",
        text,
        re.IGNORECASE,
    )
    if m_cond:
        return RequirementApplicability.CONDITIONAL, m_cond.group(1).strip()

    lowered = text.lower()
    if re.search(r"\b(?:oem|original\s+equipment\s+manufacturer)\b", lowered):
        return RequirementApplicability.OEM, None
    if re.search(r"\b(?:authorized\s+(?:dealer|distributor|partner)|channel\s+partner)\b", lowered):
        return RequirementApplicability.AUTHORIZED_DEALER, None
    if re.search(r"\b(?:manufacturer)\b", lowered):
        return RequirementApplicability.MANUFACTURER, None
    if re.search(r"\b(?:msme|mse|udyam|micro\s+and\s+small)\b", lowered):
        return RequirementApplicability.MSME, None
    if re.search(r"\b(?:start-?up)\b", lowered):
        return RequirementApplicability.STARTUP, None
    if re.search(r"\b(?:joint\s+venture|jv)\b", lowered):
        return RequirementApplicability.JOINT_VENTURE, None
    if re.search(r"\b(?:consortium)\b", lowered):
        return RequirementApplicability.CONSORTIUM, None
    if re.search(r"\b(?:domestic\s+bidder|class-i\s+local|local\s+supplier)\b", lowered):
        return RequirementApplicability.DOMESTIC_BIDDER, None
    if re.search(r"\b(?:foreign\s+bidder|global\s+tender)\b", lowered):
        return RequirementApplicability.FOREIGN_BIDDER, None

    return RequirementApplicability.ALL_BIDDERS, None


# ==============================================================================
# 7. Evidence & Verification Mapping
# ==============================================================================

REQUIREMENT_METADATA_MAP: Dict[RequirementType, Tuple[List[str], VerificationMethod, RiskHint]] = {
    RequirementType.MIN_TURNOVER: (
        ["FINANCIAL_STATEMENTS", "TURNOVER_CERTIFICATE"],
        VerificationMethod.DOCUMENT,
        RiskHint.HIGH,
    ),
    RequirementType.MIN_NET_WORTH: (
        ["NET_WORTH_CERTIFICATE", "FINANCIAL_STATEMENTS"],
        VerificationMethod.DOCUMENT,
        RiskHint.HIGH,
    ),
    RequirementType.MIN_EXPERIENCE: (
        ["EXPERIENCE_CERTIFICATE", "WORK_ORDERS"],
        VerificationMethod.DOCUMENT,
        RiskHint.HIGH,
    ),
    RequirementType.MIN_SIMILAR_WORK_EXPERIENCE: (
        ["COMPLETION_CERTIFICATE", "PURCHASE_ORDER"],
        VerificationMethod.DOCUMENT,
        RiskHint.HIGH,
    ),
    RequirementType.MIN_TECHNICAL_CAPACITY: (
        ["CAPACITY_CERTIFICATE", "PLANT_INSPECTION_REPORT"],
        VerificationMethod.DOCUMENT,
        RiskHint.HIGH,
    ),
    RequirementType.GST_REGISTRATION: (
        ["GST_CERTIFICATE"],
        VerificationMethod.DOCUMENT,
        RiskHint.HIGH,
    ),
    RequirementType.PAN_REQUIRED: (
        ["PAN_DOCUMENT"],
        VerificationMethod.DOCUMENT,
        RiskHint.HIGH,
    ),
    RequirementType.STATUTORY_LICENSE: (
        ["LICENSE_CERTIFICATE"],
        VerificationMethod.DOCUMENT,
        RiskHint.HIGH,
    ),
    RequirementType.LEGAL_REGISTRATION: (
        ["REGISTRATION_CERTIFICATE"],
        VerificationMethod.DOCUMENT,
        RiskHint.HIGH,
    ),
    RequirementType.OEM_AUTHORIZATION: (
        ["OEM_AUTHORIZATION_LETTER"],
        VerificationMethod.DOCUMENT,
        RiskHint.HIGH,
    ),
    RequirementType.AUTHORIZED_DEALER: (
        ["DEALERSHIP_AGREEMENT"],
        VerificationMethod.DOCUMENT,
        RiskHint.MEDIUM,
    ),
    RequirementType.ELIGIBILITY_CONDITION: (
        ["UNDERTAKING_DECLARATION"],
        VerificationMethod.DOCUMENT,
        RiskHint.HIGH,
    ),
    RequirementType.TECHNICAL_SPECIFICATION: (
        ["TECHNICAL_DATASHEET", "COMPLIANCE_MATRIX"],
        VerificationMethod.DOCUMENT,
        RiskHint.MEDIUM,
    ),
    RequirementType.TECHNICAL_PARAMETER: (
        ["TEST_CERTIFICATE", "DRAWING"],
        VerificationMethod.DOCUMENT,
        RiskHint.MEDIUM,
    ),
    RequirementType.MODEL_REQUIREMENT: (
        ["PRODUCT_BROCHURE"],
        VerificationMethod.DOCUMENT,
        RiskHint.MEDIUM,
    ),
    RequirementType.BRAND_REQUIREMENT: (
        ["BRAND_APPROVAL_LETTER"],
        VerificationMethod.DOCUMENT,
        RiskHint.MEDIUM,
    ),
    RequirementType.CERTIFICATION_REQUIRED: (
        ["QUALITY_CERTIFICATE"],
        VerificationMethod.DOCUMENT,
        RiskHint.MEDIUM,
    ),
    RequirementType.ISO_CERTIFICATION: (
        ["ISO_CERTIFICATE"],
        VerificationMethod.DOCUMENT,
        RiskHint.MEDIUM,
    ),
    RequirementType.QUALITY_CERTIFICATION: (
        ["QC_INSPECTION_REPORT"],
        VerificationMethod.DOCUMENT,
        RiskHint.MEDIUM,
    ),
    RequirementType.BID_VALIDITY: (
        ["BID_SUBMISSION_LETTER"],
        VerificationMethod.RULE,
        RiskHint.LOW,
    ),
    RequirementType.DELIVERY_PERIOD: (
        ["DELIVERY_SCHEDULE_COMMITMENT"],
        VerificationMethod.RULE,
        RiskHint.MEDIUM,
    ),
    RequirementType.WARRANTY_PERIOD: (
        ["WARRANTY_CERTIFICATE"],
        VerificationMethod.RULE,
        RiskHint.MEDIUM,
    ),
    RequirementType.SUBMISSION_DEADLINE: (
        ["PORTAL_ACKNOWLEDGEMENT"],
        VerificationMethod.RULE,
        RiskHint.LOW,
    ),
    RequirementType.EMD_REQUIRED: (
        ["EMD_PAYMENT_RECEIPT", "BANK_GUARANTEE"],
        VerificationMethod.DOCUMENT,
        RiskHint.HIGH,
    ),
    RequirementType.PBG_REQUIRED: (
        ["PERFORMANCE_BANK_GUARANTEE"],
        VerificationMethod.DOCUMENT,
        RiskHint.HIGH,
    ),
    RequirementType.PERFORMANCE_SECURITY: (
        ["SECURITY_DEPOSIT_RECEIPT"],
        VerificationMethod.DOCUMENT,
        RiskHint.HIGH,
    ),
    RequirementType.DOCUMENT_REQUIRED: (
        ["SPECIFIED_DOCUMENT"],
        VerificationMethod.DOCUMENT,
        RiskHint.MEDIUM,
    ),
    RequirementType.DECLARATION_REQUIRED: (
        ["DECLARATION_FORM", "INTEGRITY_PACT"],
        VerificationMethod.DOCUMENT,
        RiskHint.MEDIUM,
    ),
    RequirementType.AFFIDAVIT_REQUIRED: (
        ["SWORN_AFFIDAVIT"],
        VerificationMethod.DOCUMENT,
        RiskHint.MEDIUM,
    ),
    RequirementType.PRICE_REQUIREMENT: (
        ["PRICE_BID_SCHEDULE"],
        VerificationMethod.RULE,
        RiskHint.MEDIUM,
    ),
    RequirementType.PAYMENT_TERM: (
        ["COMMERCIAL_ACCEPTANCE"],
        VerificationMethod.RULE,
        RiskHint.MEDIUM,
    ),
    RequirementType.TAX_REQUIREMENT: (
        ["TAX_INVOICE_UNDERTAKING"],
        VerificationMethod.RULE,
        RiskHint.MEDIUM,
    ),
    RequirementType.OTHER: (
        ["SPECIFIED_DOCUMENT"],
        VerificationMethod.DOCUMENT,
        RiskHint.LOW,
    ),
}


def infer_evidence_and_method(req_type: RequirementType) -> Tuple[List[str], VerificationMethod, RiskHint]:
    """Retrieve standard required evidence, verification method, and preliminary risk hint."""
    return REQUIREMENT_METADATA_MAP.get(
        req_type,
        (["SPECIFIED_DOCUMENT"], VerificationMethod.DOCUMENT, RiskHint.MEDIUM),
    )


# ==============================================================================
# 8. Requirement Extraction & Splitting Engine
# ==============================================================================

def extract_requirements_from_clause(
    clause: TenderClause,
) -> List[Dict[str, Any]]:
    """Extract one or more structured requirements from a single TenderClause."""
    full_text = f"{clause.title or ''}\n{clause.clause_text}".strip()
    if not is_requirement_candidate(clause.clause_text, clause.title):
        return []

    requirements: List[Dict[str, Any]] = []
    lowered = full_text.lower()

    # Determine sub-requirements if multiple obligations are present
    type_matches: List[Tuple[RequirementType, str]] = []

    # Financial checks
    if re.search(r"\b(?:annual\s+turnover|turnover)\b", lowered):
        type_matches.append((RequirementType.MIN_TURNOVER, "Minimum average annual turnover requirement"))
    if re.search(r"\b(?:net\s+worth)\b", lowered):
        type_matches.append((RequirementType.MIN_NET_WORTH, "Minimum net worth requirement"))
    if re.search(r"\b(?:earnest\s+money|emd|bid\s+security)\b", lowered):
        type_matches.append((RequirementType.EMD_REQUIRED, "Earnest Money Deposit (EMD) requirement"))
    if re.search(r"\b(?:performance\s+bank\s+guarantee|pbg)\b", lowered):
        type_matches.append((RequirementType.PBG_REQUIRED, "Performance Bank Guarantee (PBG) requirement"))
    elif re.search(r"\b(?:performance\s+security|security\s+deposit)\b", lowered):
        type_matches.append((RequirementType.PERFORMANCE_SECURITY, "Performance Security requirement"))

    # Statutory checks
    if re.search(r"\bgst(?:in)?\b", lowered):
        type_matches.append((RequirementType.GST_REGISTRATION, "GST registration certificate requirement"))
    if re.search(r"\bpan\s*(?:card|number|registration)?\b", lowered):
        type_matches.append((RequirementType.PAN_REQUIRED, "PAN card requirement"))
    if re.search(r"\b(?:statutory\s+licen[sc]e|factory\s+licen[sc]e)\b", lowered):
        type_matches.append((RequirementType.STATUTORY_LICENSE, "Statutory license requirement"))

    # Eligibility & Experience checks
    if re.search(r"\b(?:similar\s+(?:works?|projects?|orders?|contracts?))\b", lowered):
        type_matches.append((RequirementType.MIN_SIMILAR_WORK_EXPERIENCE, "Minimum similar work experience requirement"))
    elif re.search(r"\b(?:prior\s+experience|past\s+performance|years?\s+of\s+experience)\b", lowered):
        type_matches.append((RequirementType.MIN_EXPERIENCE, "Minimum past experience requirement"))
    if re.search(r"\b(?:oem\s+authori[sz]ation|manufacturer\s+authori[sz]ation|maf)\b", lowered):
        type_matches.append((RequirementType.OEM_AUTHORIZATION, "OEM authorization requirement"))
    if re.search(r"\b(?:blacklisted?|debarred)\b", lowered):
        type_matches.append((RequirementType.ELIGIBILITY_CONDITION, "Non-blacklisted and non-debarred declaration requirement"))

    # Technical checks
    if re.search(r"\biso\s*[0-9]+\b", lowered):
        type_matches.append((RequirementType.ISO_CERTIFICATION, "ISO quality certification requirement"))
    elif re.search(r"\b(?:quality\s+certif|asme|welding\s+procedure|ndt|radiograph)\b", lowered):
        type_matches.append((RequirementType.TECHNICAL_SPECIFICATION, "Technical specification and inspection compliance requirement"))
    elif clause.category == ClauseCategory.TECHNICAL and not type_matches:
        type_matches.append((RequirementType.TECHNICAL_SPECIFICATION, "Technical specification requirement"))

    # Commercial checks
    if re.search(r"\b(?:payment\s+terms?|terms\s+of\s+payment)\b", lowered):
        type_matches.append((RequirementType.PAYMENT_TERM, "Commercial payment terms requirement"))
    if re.search(r"\b(?:delivery\s+(?:period|schedule|terms)|dispatch)\b", lowered):
        type_matches.append((RequirementType.DELIVERY_PERIOD, "Delivery period requirement"))
    if re.search(r"\bwarranty|guarantee\s+period\b", lowered):
        type_matches.append((RequirementType.WARRANTY_PERIOD, "Warranty period requirement"))
    if re.search(r"\b(?:bid|tender)\s+validity\b", lowered):
        type_matches.append((RequirementType.BID_VALIDITY, "Bid validity period requirement"))

    # Documentary & Submissions checks
    if re.search(r"\bintegrity\s+pact\b", lowered):
        type_matches.append((RequirementType.DECLARATION_REQUIRED, "Signed integrity pact requirement"))
    if re.search(r"\baffidavit\b", lowered):
        type_matches.append((RequirementType.AFFIDAVIT_REQUIRED, "Sworn affidavit requirement"))

    # Fallback to general clause-derived requirement
    if not type_matches:
        fallback_desc = clause.title or clause.clause_text[:120].strip()
        type_matches.append((RequirementType.OTHER, f"Requirement: {fallback_desc}"))

    # Shared properties across requirements in the clause
    op = extract_operator(full_text)
    val_num, unit, currency = extract_numeric_and_unit(full_text)
    period = extract_period(full_text)
    mandatory = detect_mandatory(full_text)
    applicability, app_condition = detect_applicability(full_text)

    for req_type, base_desc in type_matches:
        evidence_list, v_method, risk = infer_evidence_and_method(req_type)

        # Build clean descriptive text
        if val_num is not None and unit is not None:
            desc = f"{base_desc}: {op or ''} {val_num} {unit}".strip()
            if period:
                desc = f"{desc} ({period})"
        else:
            desc = f"{base_desc}. {clause.clause_text[:150].strip()}"

        # If specific text value (e.g. ISO 9001)
        val_text = None
        if req_type == RequirementType.ISO_CERTIFICATION:
            m_iso = re.search(r"\b(iso\s*[0-9]+(?::[0-9]+)?)\b", full_text, re.I)
            if m_iso:
                val_text = m_iso.group(1).upper()
        elif req_type == RequirementType.TECHNICAL_SPECIFICATION:
            m_spec = re.search(r"\b(asme\s+section\s+[ivxcdm]+(?:\s+div\s+[0-9]+)?)\b", full_text, re.I)
            if m_spec:
                val_text = m_spec.group(1).upper()

        confidence = 0.95 if (val_num is not None and op is not None) else 0.88

        requirements.append({
            "requirement_type": req_type,
            "category": clause.category,
            "description": desc,
            "operator": op,
            "value_numeric": val_num,
            "value_text": val_text,
            "unit": unit,
            "currency": currency,
            "period": period,
            "mandatory": mandatory,
            "applicability": applicability,
            "applicability_condition": app_condition,
            "required_evidence": evidence_list,
            "verification_method": v_method,
            "risk_hint": risk,
            "confidence": confidence,
        })

    return requirements


def build_requirement_signature(
    tender_id: uuid.UUID,
    clause_id: uuid.UUID,
    req_type: RequirementType,
    description: str,
    operator: Optional[str],
    value_numeric: Optional[float],
    value_text: Optional[str],
    unit: Optional[str],
    currency: Optional[str],
    period: Optional[str],
    applicability: RequirementApplicability,
    applicability_condition: Optional[str],
) -> str:
    """Compute a deterministic SHA-256 signature for requirement deduplication."""
    raw = (
        f"{tender_id}|{clause_id}|{req_type.value}|{description.strip()}|"
        f"{operator or ''}|{value_numeric if value_numeric is not None else ''}|"
        f"{value_text or ''}|{unit or ''}|{currency or ''}|{period or ''}|"
        f"{applicability.value}|{applicability_condition or ''}"
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


# ==============================================================================
# 9. Service Operations
# ==============================================================================

async def extract_tender_requirements(
    session: AsyncSession,
    tender_id: uuid.UUID,
    organization_id: uuid.UUID,
    user_id: uuid.UUID,
    force_reextract: bool = False,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> Tuple[List[TenderRequirement], int, int, Dict[str, int], Dict[str, int]]:
    """Extract, normalize, and persist structured requirements from tender clauses.
    
    Atomicity & Idempotency:
        - If requirements already exist and force_reextract is False, returns existing set.
        - If force_reextract is True, prepares full validated set in memory first,
          then replaces old requirements atomically in a single transaction.
    """
    # 1. Tenant verification
    await get_tender_by_id(session, tender_id, organization_id)

    # 2. Check for existing requirements
    existing_stmt = (
        select(TenderRequirement)
        .options(selectinload(TenderRequirement.clause))
        .where(TenderRequirement.tender_id == tender_id)
        .order_by(TenderRequirement.sequence_order.asc())
    )
    existing_res = await session.execute(existing_stmt)
    existing_reqs = list(existing_res.scalars().all())

    if existing_reqs and not force_reextract:
        cat_breakdown: Dict[str, int] = {}
        type_breakdown: Dict[str, int] = {}
        for r in existing_reqs:
            cat_breakdown[r.category.value] = cat_breakdown.get(r.category.value, 0) + 1
            type_breakdown[r.requirement_type.value] = type_breakdown.get(r.requirement_type.value, 0) + 1
        return existing_reqs, 0, len(existing_reqs), cat_breakdown, type_breakdown

    # 3. Retrieve clauses for this tender
    clause_stmt = (
        select(TenderClause)
        .where(TenderClause.tender_id == tender_id)
        .order_by(TenderClause.sequence_order.asc())
    )
    clause_res = await session.execute(clause_stmt)
    clauses = list(clause_res.scalars().all())

    if not clauses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tender has no extracted clauses yet. Please run clause extraction first.",
        )

    # 4. In-memory requirement extraction & validation
    new_entities: List[TenderRequirement] = []
    seen_signatures = set()
    cat_breakdown: Dict[str, int] = {}
    type_breakdown: Dict[str, int] = {}

    seq_counter = 1
    for clause in clauses:
        extracted_dicts = extract_requirements_from_clause(clause)
        for req_dict in extracted_dicts:
            sig = build_requirement_signature(
                tender_id=tender_id,
                clause_id=clause.id,
                req_type=req_dict["requirement_type"],
                description=req_dict["description"],
                operator=req_dict["operator"],
                value_numeric=req_dict["value_numeric"],
                value_text=req_dict["value_text"],
                unit=req_dict["unit"],
                currency=req_dict["currency"],
                period=req_dict["period"],
                applicability=req_dict["applicability"],
                applicability_condition=req_dict["applicability_condition"],
            )
            # Avoid duplicate signature within the same clause
            if sig in seen_signatures:
                continue
            seen_signatures.add(sig)

            req_entity = TenderRequirement(
                tender_id=tender_id,
                clause_id=clause.id,
                category=req_dict["category"],
                requirement_type=req_dict["requirement_type"],
                description=req_dict["description"],
                operator=req_dict["operator"],
                value_numeric=req_dict["value_numeric"],
                value_text=req_dict["value_text"],
                unit=req_dict["unit"],
                currency=req_dict["currency"],
                period=req_dict["period"],
                mandatory=req_dict["mandatory"],
                applicability=req_dict["applicability"],
                applicability_condition=req_dict["applicability_condition"],
                required_evidence=req_dict["required_evidence"],
                verification_method=req_dict["verification_method"],
                risk_hint=req_dict["risk_hint"],
                sequence_order=seq_counter,
                extraction_method="RULE_BASED",
                confidence=req_dict["confidence"],
                requirement_signature=sig,
            )
            new_entities.append(req_entity)
            seq_counter += 1

            cat_key = req_dict["category"].value
            cat_breakdown[cat_key] = cat_breakdown.get(cat_key, 0) + 1

            type_key = req_dict["requirement_type"].value
            type_breakdown[type_key] = type_breakdown.get(type_key, 0) + 1

    # 5. Atomic database transaction
    if force_reextract and existing_reqs:
        del_stmt = delete(TenderRequirement).where(TenderRequirement.tender_id == tender_id)
        await session.execute(del_stmt)
        await session.flush()

    for ent in new_entities:
        session.add(ent)

    await session.flush()

    # 6. Audit Logging
    await log_audit_event(
        session=session,
        action="TENDER_REQUIREMENTS_EXTRACTED",
        entity_type="tender",
        entity_id=str(tender_id),
        organization_id=organization_id,
        actor_user_id=user_id,
        new_state={
            "tender_id": str(tender_id),
            "requirements_created": len(new_entities),
            "requirements_reused": 0,
            "force_reextract": force_reextract,
            "categories_breakdown": cat_breakdown,
            "types_breakdown": type_breakdown,
            "extraction_method": "RULE_BASED",
        },
        ip_address=ip_address,
        user_agent=user_agent,
    )

    await session.commit()
    for ent in new_entities:
        await session.refresh(ent)

    return new_entities, len(new_entities), 0, cat_breakdown, type_breakdown


async def list_tender_requirements(
    session: AsyncSession,
    tender_id: uuid.UUID,
    organization_id: uuid.UUID,
    category: Optional[ClauseCategory] = None,
    requirement_type: Optional[RequirementType] = None,
    mandatory: Optional[bool] = None,
    applicability: Optional[RequirementApplicability] = None,
    verification_method: Optional[VerificationMethod] = None,
    risk_hint: Optional[RiskHint] = None,
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
) -> Tuple[List[TenderRequirement], int, Dict[str, int], Dict[str, int]]:
    """List requirements for a tender with filtering, search, and pagination."""
    # Tenant verification
    await get_tender_by_id(session, tender_id, organization_id)

    base_query = (
        select(TenderRequirement)
        .options(selectinload(TenderRequirement.clause))
        .where(TenderRequirement.tender_id == tender_id)
    )

    if category is not None:
        base_query = base_query.where(TenderRequirement.category == category)
    if requirement_type is not None:
        base_query = base_query.where(TenderRequirement.requirement_type == requirement_type)
    if mandatory is not None:
        base_query = base_query.where(TenderRequirement.mandatory == mandatory)
    if applicability is not None:
        base_query = base_query.where(TenderRequirement.applicability == applicability)
    if verification_method is not None:
        base_query = base_query.where(TenderRequirement.verification_method == verification_method)
    if risk_hint is not None:
        base_query = base_query.where(TenderRequirement.risk_hint == risk_hint)
    if search:
        search_pattern = f"%{search.strip()}%"
        base_query = base_query.where(
            or_(
                TenderRequirement.description.ilike(search_pattern),
                TenderRequirement.value_text.ilike(search_pattern),
                TenderRequirement.unit.ilike(search_pattern),
            )
        )

    # Total matching count
    count_stmt = select(func.count()).select_from(base_query.subquery())
    total_res = await session.execute(count_stmt)
    total = total_res.scalar_one()

    # Paginated results
    offset = (page - 1) * page_size
    query = base_query.order_by(TenderRequirement.sequence_order.asc()).offset(offset).limit(page_size)
    res = await session.execute(query)
    items = list(res.scalars().all())

    # Category and Type breakdowns for the whole tender
    cat_stmt = (
        select(TenderRequirement.category, func.count(TenderRequirement.id))
        .where(TenderRequirement.tender_id == tender_id)
        .group_by(TenderRequirement.category)
    )
    cat_res = await session.execute(cat_stmt)
    cat_breakdown = {row[0].value: row[1] for row in cat_res.all()}

    type_stmt = (
        select(TenderRequirement.requirement_type, func.count(TenderRequirement.id))
        .where(TenderRequirement.tender_id == tender_id)
        .group_by(TenderRequirement.requirement_type)
    )
    type_res = await session.execute(type_stmt)
    type_breakdown = {row[0].value: row[1] for row in type_res.all()}

    return items, total, cat_breakdown, type_breakdown


async def get_tender_requirement(
    session: AsyncSession,
    tender_id: uuid.UUID,
    requirement_id: uuid.UUID,
    organization_id: uuid.UUID,
) -> TenderRequirement:
    """Retrieve an individual tender requirement with source clause details."""
    # Tenant verification
    await get_tender_by_id(session, tender_id, organization_id)

    query = (
        select(TenderRequirement)
        .options(selectinload(TenderRequirement.clause))
        .where(
            TenderRequirement.id == requirement_id,
            TenderRequirement.tender_id == tender_id,
        )
    )
    res = await session.execute(query)
    req = res.scalar_one_or_none()
    if not req:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tender requirement not found.",
        )
    return req

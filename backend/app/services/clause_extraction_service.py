import re
import uuid
from typing import Any, Dict, List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.clause import TenderClause
from app.models.enums import ClauseCategory
from app.models.tender import Tender, TenderDocument, TenderPage
from app.services.audit_service import log_audit_event
from app.services.document_service import ensure_pages_extracted
from app.services.tender_service import get_tender_by_id


# ==============================================================================
# 1. Text Normalization Utilities
# ==============================================================================

def normalize_text(text: str) -> str:
    """Normalize whitespace, lines, and broken layout artifacts while preserving structure."""
    if not text:
        return ""
    # Standardize line breaks
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Replace non-breaking and unusual spaces with standard space
    text = re.sub(r"[\t\u00A0\u1680\u2000-\u200a\u202f\u205f\u3000]", " ", text)
    # Collapse 2+ horizontal spaces into one (without touching newlines)
    text = re.sub(r"[ ]{2,}", " ", text)
    # Remove leading/trailing space from each line
    lines = [line.strip() for line in text.split("\n")]
    # Collapse multiple blank lines into at most one blank line
    cleaned_lines = []
    blank_seen = False
    for line in lines:
        if not line:
            if not blank_seen:
                cleaned_lines.append("")
                blank_seen = True
        else:
            cleaned_lines.append(line)
            blank_seen = False
    return "\n".join(cleaned_lines).strip()


# ==============================================================================
# 2. Deterministic Segmentation Engine
# ==============================================================================

# Regex patterns for clause boundaries
RE_NUMERICAL = re.compile(
    r"^(\d+(?:\.\d+)+|\d+\.)(?:\s+(.*))?$"
)

RE_EXPLICIT_PREFIX = re.compile(
    r"^(Clause|Section|Article|Chapter|Part)\s+([0-9A-Za-z]+(?:\.[0-9A-Za-z]+)*)[:\.]?\s*(.*)$",
    re.IGNORECASE,
)

RE_LIST_MARKER = re.compile(
    r"^(\([a-z0-9]+\)|\([ivxcdm]+\)|[A-Z]\.|\([A-Z]\))\s*(.*)$"
)

RE_UPPERCASE_HEADING = re.compile(
    r"^([A-Z0-9\s,\-–—\(\)/&]{4,80}):?$"
)

COMMON_HEADING_KEYWORDS = {
    "ELIGIBILITY CRITERIA",
    "QUALIFICATION CRITERIA",
    "TECHNICAL SPECIFICATIONS",
    "SCOPE OF WORK",
    "PAYMENT TERMS",
    "TERMS OF PAYMENT",
    "SPECIAL CONDITIONS OF CONTRACT",
    "GENERAL CONDITIONS OF CONTRACT",
    "COMMERCIAL CONDITIONS",
    "STATUTORY REQUIREMENTS",
    "SUBMISSION OF BIDS",
    "INSTRUCTIONS TO BIDDERS",
    "ANNEXURE",
    "SCHEDULE OF REQUIREMENTS",
    "BILL OF QUANTITIES",
    "EARNEST MONEY DEPOSIT",
    "PERFORMANCE SECURITY",
    "INTEGRITY PACT",
    "ZERO DEVIATION",
    "MAKE IN INDIA",
}


def _match_clause_header(line: str) -> Optional[Tuple[Optional[str], Optional[str], Optional[str]]]:
    """Inspect line to determine if it is a new clause boundary.
    
    Returns:
        (clause_number, title, initial_body) if line starts a new clause, or None.
    """
    line = line.strip()
    if not line or len(line) < 2:
        return None

    # 1. Explicit Prefix (e.g. "Clause 1.0 Payment Terms" or "Section 2: Scope")
    match_prefix = RE_EXPLICIT_PREFIX.match(line)
    if match_prefix:
        prefix_type, num, rest = match_prefix.groups()
        clause_num = f"{prefix_type} {num}"
        title = rest.strip() if rest else None
        return (clause_num, title, "")

    # 2. Numbered headings (e.g. "1.1 Technical Specification", "2. Payment Terms")
    match_num = RE_NUMERICAL.match(line)
    if match_num:
        num, rest = match_num.groups()
        num_clean = num.rstrip(".")
        title = rest.strip() if rest and rest.strip() else None
        return (num_clean, title, "")


    # 3. Known uppercase or predefined headings
    clean_upper = line.rstrip(":").strip()
    if clean_upper.upper() in COMMON_HEADING_KEYWORDS or (RE_UPPERCASE_HEADING.match(line) and len(line.split()) <= 8 and not line.endswith(".")):
        return (None, clean_upper, "")

    # 4. List markers (e.g. "(a) Bidder shall submit...", "(i) Annual turnover...")
    match_list = RE_LIST_MARKER.match(line)
    if match_list:
        marker, rest = match_list.groups()
        return (marker, None, rest.strip())

    return None


class RawClause:
    def __init__(
        self,
        document_id: uuid.UUID,
        page_id: Optional[uuid.UUID],
        page_number: int,
        clause_number: Optional[str] = None,
        title: Optional[str] = None,
        initial_text: str = "",
    ):
        self.document_id = document_id
        self.page_id = page_id
        self.page_number = page_number
        self.clause_number = clause_number
        self.title = title
        self.lines: List[str] = [initial_text] if initial_text else []

    def append_line(self, line: str) -> None:
        if line:
            self.lines.append(line)

    def get_full_text(self) -> str:
        raw = "\n".join(self.lines)
        return normalize_text(raw)


def segment_pages_into_clauses(
    pages_data: List[Tuple[uuid.UUID, Optional[uuid.UUID], int, str]],
) -> List[RawClause]:
    """Segment sequentially ordered pages of a tender into logical clause structures.
    
    pages_data is a list of tuples: (document_id, page_id, page_number, text_content).
    """
    clauses: List[RawClause] = []
    current_clause: Optional[RawClause] = None

    for doc_id, page_id, page_num, raw_content in pages_data:
        text = normalize_text(raw_content or "")
        lines = text.split("\n")

        for line in lines:
            line_str = line.strip()
            if not line_str:
                continue

            header_match = _match_clause_header(line_str)
            if header_match:
                clause_num, title, body = header_match

                # Finalize previous clause if it contains text or titles
                if current_clause and (current_clause.lines or current_clause.title):
                    clauses.append(current_clause)

                # Start new clause anchored to current page
                current_clause = RawClause(
                    document_id=doc_id,
                    page_id=page_id,
                    page_number=page_num,
                    clause_number=clause_num,
                    title=title,
                    initial_text=body,
                )
            else:
                # Continuation text
                if current_clause is None:
                    # Create an initial general clause
                    current_clause = RawClause(
                        document_id=doc_id,
                        page_id=page_id,
                        page_number=page_num,
                        clause_number=None,
                        title=None,
                        initial_text=line_str,
                    )
                else:
                    current_clause.append_line(line_str)

    if current_clause and (current_clause.lines or current_clause.title):
        clauses.append(current_clause)

    return clauses


# ==============================================================================
# 3. Deterministic Classification Engine
# ==============================================================================

# Keyword pattern tables with category weights
CLASSIFICATION_RULES = {
    ClauseCategory.ADMINISTRATIVE: [
        (r"\b(?:bid|tender)\s+validity\b", 4.0),
        (r"\bpre-bid\s+(?:meeting|conference)\b", 3.5),
        (r"\bauthorized\s+(?:signatory|representative)\b", 3.5),
        (r"\bnodal\s+officer\b", 3.0),
        (r"\bjurisdiction\s+of\s+court\b", 3.0),
        (r"\bcorrigendum|amendment\b", 2.5),
        (r"\bclarification\s+of\s+bids?\b", 2.5),
        (r"\bcommunication\b", 1.5),
    ],
    ClauseCategory.STATUTORY: [
        (r"\bgstin\b", 4.5),
        (r"\bgoods\s+and\s+services\s+tax\b", 4.0),
        (r"\bpan\s+(?:card|number)?\b", 4.0),
        (r"\bstatutory\s+(?:registration|compliance|requirements?)\b", 4.0),
        (r"\bepf|esic\b", 3.5),
        (r"\bfactory\s+licen[sc]e\b", 3.5),
        (r"\bmsme\s+act|udyam\b", 3.5),
        (r"\bpollution\s+clearance\b", 3.0),
        (r"\blabou?r\s+laws?\b", 2.5),
        (r"\bgst\b", 2.0),
    ],
    ClauseCategory.TECHNICAL: [
        (r"\btechnical\s+specifications?\b", 4.5),
        (r"\bgeneral\s+arrangement\s+drawing|ga\s+drawing\b", 4.0),
        (r"\bwelding\s+procedures?\b", 4.0),
        (r"\bndt\s+(?:report|testing)?\b", 4.0),
        (r"\bradiograph(?:ic|y)\s+(?:test|examination)\b", 4.0),
        (r"\bdatasheet|data\s+sheet\b", 3.5),
        (r"\bhydrostatic\s+test\b", 3.5),
        (r"\basme\s+(?:section|code)?\b", 3.5),
        (r"\bis\s+standards?|is\s+code\b", 3.5),
        (r"\bbill\s+of\s+materials?|bom\b", 3.5),
        (r"\bvendor\s+data\s+requirements?|vdr\b", 3.5),
        (r"\btolerances?\b", 3.0),
        (r"\bdimensions?\b", 3.0),
        (r"\bcapacity\b", 2.5),
        (r"\bspecifications?\b", 2.0),
    ],
    ClauseCategory.COMMERCIAL: [
        (r"\bpayment\s+terms\b", 4.5),
        (r"\bterms\s+of\s+payment\b", 4.5),
        (r"\bprice\s+validity\b", 4.0),
        (r"\bliquidated\s+damages\b", 4.0),
        (r"\bincoterms\b", 4.0),
        (r"\bprice\s+variation\b", 3.5),
        (r"\btransit\s+insurance\b", 3.5),
        (r"\bdispatch|freight\b", 3.0),
        (r"\bconsignee\b", 3.0),
        (r"\bwarranty|guarantee\s+period\b", 3.0),
        (r"\bpenalt(?:y|ies)\b", 2.5),
        (r"\bdelivery\s+(?:period|schedule|terms)\b", 3.5),
    ],
    ClauseCategory.FINANCIAL: [
        (r"\baverage\s+annual\s+turnover\b", 4.5),
        (r"\bannual\s+turnover\b", 4.0),
        (r"\bearnest\s+money\s+deposit|emd\b", 4.5),
        (r"\bperformance\s+bank\s+guarantee|pbg\b", 4.5),
        (r"\bperformance\s+security\b", 4.0),
        (r"\bbid\s+security\b", 4.0),
        (r"\bnet\s+worth\b", 3.5),
        (r"\bsolvency\s+certificate\b", 3.5),
        (r"\bworking\s+capital\b", 3.0),
        (r"\bturnover\b", 2.0),
    ],
    ClauseCategory.ELIGIBILITY: [
        (r"\beligibility\s+criteria\b", 4.5),
        (r"\bqualification\s+criteria\b", 4.5),
        (r"\bprior\s+experience\b", 4.0),
        (r"\bpast\s+performance\b", 4.0),
        (r"\bsimilar\s+work\s+experience\b", 4.0),
        (r"\bsimilar\s+(?:works?|orders?|contracts?)\b", 3.5),
        (r"\bdebarred|blacklisted?\b", 4.0),
        (r"\boem\s+authori[sz]ation\b", 4.0),
        (r"\bmanufacturer\s+authori[sz]ation\b", 4.0),
        (r"\beligible\s+bidder\b", 3.0),
        (r"\bexperience\b", 2.0),
    ],
    ClauseCategory.SUBMISSION: [
        (r"\bmode\s+of\s+submission\b", 4.5),
        (r"\btwo[- ]bid\s+(?:system|envelope)\b", 4.5),
        (r"\bunpriced\s+(?:bid|techno-commercial)\b", 4.0),
        (r"\bformat\s+of\s+bid\b", 4.0),
        (r"\bintegrity\s+pact\b", 4.5),
        (r"\baffidavit\b", 4.0),
        (r"\bchecklist\s+of\s+documents\b", 4.0),
        (r"\bdocuments\s+to\s+(?:be\s+)?submitted\b", 4.0),
        (r"\bsealed\s+cover|envelope\b", 3.0),
        (r"\bdeclaration\b", 2.5),
    ],
}


def classify_clause(clause_text: str, title: Optional[str] = None) -> Tuple[ClauseCategory, float]:
    """Deterministically classify a clause into one of 8 ClauseCategory enums.
    
    Returns:
        (category, confidence)
    """
    full_search_text = f"{title or ''} {clause_text}".lower()

    scores: Dict[ClauseCategory, float] = {cat: 0.0 for cat in CLASSIFICATION_RULES.keys()}

    for category, patterns in CLASSIFICATION_RULES.items():
        for pattern, weight in patterns:
            # Check title first (double weight for title matches)
            if title and re.search(pattern, title.lower()):
                scores[category] += weight * 2.0
            elif re.search(pattern, full_search_text):
                scores[category] += weight

    best_category, max_score = max(scores.items(), key=lambda x: x[1])

    # Threshold for classification
    if max_score >= 3.0:
        confidence = min(0.98, 0.70 + (max_score * 0.03))
        return best_category, round(confidence, 2)
    elif max_score >= 1.5:
        confidence = min(0.85, 0.60 + (max_score * 0.04))
        return best_category, round(confidence, 2)
    else:
        return ClauseCategory.GENERAL, 0.50


# ==============================================================================
# 4. Service Operations
# ==============================================================================

async def extract_tender_clauses(
    session: AsyncSession,
    tender_id: uuid.UUID,
    organization_id: uuid.UUID,
    user_id: uuid.UUID,
    force_reextract: bool = False,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> Tuple[List[TenderClause], int, Dict[str, int]]:
    """Extract, segment, classify, and persist tender clauses from tender PDF pages.
    
    Idempotency:
        - If extraction already exists and force_reextract is False, returns existing clauses.
        - If force_reextract is True, deletes existing clauses and performs clean re-extraction.
    """
    # 1. Verify tender exists and belongs to the user's organization
    await get_tender_by_id(session, tender_id, organization_id)

    # 2. Check for existing clauses
    existing_clauses_stmt = (
        select(TenderClause)
        .where(TenderClause.tender_id == tender_id)
        .order_by(TenderClause.sequence_order.asc())
    )
    existing_res = await session.execute(existing_clauses_stmt)
    existing_clauses = list(existing_res.scalars().all())

    if existing_clauses and not force_reextract:
        breakdown = {}
        for c in existing_clauses:
            cat_name = c.category.value
            breakdown[cat_name] = breakdown.get(cat_name, 0) + 1
        return existing_clauses, len(existing_clauses), breakdown

    # 3. If force_reextract is True, remove existing clauses
    if existing_clauses and force_reextract:
        del_stmt = delete(TenderClause).where(TenderClause.tender_id == tender_id)
        await session.execute(del_stmt)
        await session.flush()

    # 4. Retrieve all documents for this tender
    doc_stmt = (
        select(TenderDocument)
        .where(
            TenderDocument.tender_id == tender_id,
            TenderDocument.organization_id == organization_id,
        )
        .order_by(TenderDocument.created_at.asc())
    )
    doc_res = await session.execute(doc_stmt)
    documents = list(doc_res.scalars().all())

    if not documents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tender has no documents uploaded. Please upload a tender PDF first.",
        )

    # 5. Ensure pages are extracted for each document and gather pages sequentially
    pages_data: List[Tuple[uuid.UUID, Optional[uuid.UUID], int, str]] = []
    total_pages = 0

    for doc in documents:
        doc_pages = await ensure_pages_extracted(session, doc)
        for page in doc_pages:
            total_pages += 1
            pages_data.append((doc.id, page.id, page.page_number, page.text_content or ""))

    if not pages_data:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No page text could be extracted from tender documents.",
        )

    # 6. Run segmentation engine across pages
    raw_clauses = segment_pages_into_clauses(pages_data)

    # 7. Classify each clause and construct TenderClause entities
    persisted_clauses: List[TenderClause] = []
    category_breakdown: Dict[str, int] = {}

    for idx, raw in enumerate(raw_clauses, start=1):
        clause_text = raw.get_full_text()
        if not clause_text and not raw.title:
            continue

        cat, confidence = classify_clause(clause_text, raw.title)
        cat_key = cat.value
        category_breakdown[cat_key] = category_breakdown.get(cat_key, 0) + 1

        clause_entity = TenderClause(
            tender_id=tender_id,
            document_id=raw.document_id,
            page_id=raw.page_id,
            page_number=raw.page_number,
            clause_number=raw.clause_number,
            title=raw.title,
            clause_text=clause_text if clause_text else (raw.title or "Untitled Clause"),
            category=cat,
            sequence_order=idx,
            extraction_method="RULE_BASED",
            confidence=confidence,
        )
        session.add(clause_entity)
        persisted_clauses.append(clause_entity)

    await session.flush()

    # 8. Record audit log
    await log_audit_event(
        session=session,
        action="TENDER_CLAUSES_EXTRACTED",
        entity_type="tender",
        entity_id=str(tender_id),
        organization_id=organization_id,
        actor_user_id=user_id,
        new_state={
            "tender_id": str(tender_id),
            "document_count": len(documents),
            "page_count": total_pages,
            "clause_count": len(persisted_clauses),
            "category_breakdown": category_breakdown,
            "extraction_method": "RULE_BASED",
            "force_reextract": force_reextract,
        },
        ip_address=ip_address,
        user_agent=user_agent,
    )

    await session.commit()
    for c in persisted_clauses:
        await session.refresh(c)

    return persisted_clauses, len(persisted_clauses), category_breakdown


async def list_tender_clauses(
    session: AsyncSession,
    tender_id: uuid.UUID,
    organization_id: uuid.UUID,
    category: Optional[ClauseCategory] = None,
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
) -> Tuple[List[TenderClause], int, Dict[str, int]]:
    """List clauses for a tender with filtering, text search, and pagination."""
    # Verify tender ownership
    await get_tender_by_id(session, tender_id, organization_id)

    # Base query for counts and filtering
    base_query = select(TenderClause).where(TenderClause.tender_id == tender_id)

    if category is not None:
        base_query = base_query.where(TenderClause.category == category)

    if search:
        search_pattern = f"%{search.strip()}%"
        base_query = base_query.where(
            or_(
                TenderClause.clause_text.ilike(search_pattern),
                TenderClause.title.ilike(search_pattern),
                TenderClause.clause_number.ilike(search_pattern),
            )
        )

    # Total count matching filters
    count_stmt = select(func.count()).select_from(base_query.subquery())
    total_res = await session.execute(count_stmt)
    total = total_res.scalar_one()

    # Paginated results
    offset = (page - 1) * page_size
    query = base_query.order_by(TenderClause.sequence_order.asc()).offset(offset).limit(page_size)
    res = await session.execute(query)
    items = list(res.scalars().all())

    # Category breakdown across all clauses of this tender
    breakdown_stmt = (
        select(TenderClause.category, func.count(TenderClause.id))
        .where(TenderClause.tender_id == tender_id)
        .group_by(TenderClause.category)
    )
    breakdown_res = await session.execute(breakdown_stmt)
    breakdown = {row[0].value: row[1] for row in breakdown_res.all()}

    return items, total, breakdown


async def get_tender_clause(
    session: AsyncSession,
    tender_id: uuid.UUID,
    clause_id: uuid.UUID,
    organization_id: uuid.UUID,
) -> TenderClause:
    """Retrieve a single clause with organization scope verification."""
    # Verify tender ownership
    await get_tender_by_id(session, tender_id, organization_id)

    query = select(TenderClause).where(
        TenderClause.id == clause_id,
        TenderClause.tender_id == tender_id,
    )
    res = await session.execute(query)
    clause = res.scalar_one_or_none()
    if not clause:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tender clause not found.",
        )
    return clause

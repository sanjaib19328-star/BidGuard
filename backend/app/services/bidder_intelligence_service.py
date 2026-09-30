import re
from typing import Any, Dict, List, Optional, Tuple
import uuid
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bidder import Bidder, BidderDocument, BidderDocumentPage, ExtractedEntity
from app.models.enums import BidderDocumentType, DocumentProcessingStatus, EntityType
from app.services.bidder_document_service import ensure_bidder_pages_extracted, get_bidder_document

# ==============================================================================
# 1. Deterministic Entity Extraction Regular Expressions
# ==============================================================================

RE_GSTIN = re.compile(
    r"\b([0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1})\b"
)

RE_PAN = re.compile(
    r"\b([A-Z]{5}[0-9]{4}[A-Z]{1})\b"
)

RE_UDYAM = re.compile(
    r"\b(UDYAM-[A-Z]{2}-[0-9]{2}-[0-9]{7})\b",
    re.IGNORECASE,
)

RE_UDIN = re.compile(
    r"\bUDIN\s*[:\-]?\s*([0-9]{18})\b",
    re.IGNORECASE,
)

RE_DATE = re.compile(
    r"\b(\d{1,2}[\/\-\.](?:\d{1,2}|[A-Za-z]{3,9})[\/\-\.]\d{2,4})\b"
)

RE_PRESSURE = re.compile(
    r"\b(?:design\s+pressure|test\s+pressure|operating\s+pressure)?\s*[:\=]?\s*(\d+(?:\.\d+)?)\s*(bar\(g\)|bar|barg|MPa|kg\/cm2)\b",
    re.IGNORECASE,
)

RE_THICKNESS = re.compile(
    r"\b(?:shell\s+thickness|wall\s+thickness|head\s+thickness|thickness|nominal\s+thk)?\s*[:\=]?\s*(\d+(?:\.\d+)?)\s*(mm|millimeters)\b",
    re.IGNORECASE,
)

RE_ASME = re.compile(
    r"\b(ASME\s+(?:'?[Uu]'?|'?[Uu]2'?|Sec(?:tion)?\s+VIII\s+Div(?:ision)?\s+[12]))\b"
)

RE_TURNOVER = re.compile(
    r"\b(?:turnover|annual\s+turnover|average\s+turnover)?\s*[:\=]?\s*(?:INR|Rs\.?|₹)?\s*(\d+(?:\.\d+)?)\s*(Crores?|Cr|Lakhs?|Lacs?)\b",
    re.IGNORECASE,
)

RE_COMPANY_NAME = re.compile(
    r"\b([A-Z][A-Za-z0-9\s,\.\-&]{2,60}\s+(?:Pvt\.?\s*Ltd\.?|Private\s+Limited|Limited|Ltd\.?|LLP|Corporation|Corp\.?))\b"
)

# ==============================================================================
# 2. Document Classification Profiles
# ==============================================================================

DOC_TYPE_KEYWORDS: Dict[BidderDocumentType, List[Tuple[str, float]]] = {
    BidderDocumentType.GST_CERTIFICATE: [
        ("goods and services tax", 0.4),
        ("gstin", 0.3),
        ("form gst reg-06", 0.5),
        ("registration certificate", 0.2),
        ("taxpayer type", 0.2),
    ],
    BidderDocumentType.PAN_CARD: [
        ("income tax department", 0.5),
        ("permanent account number", 0.5),
        ("pan card", 0.4),
        ("govt. of india", 0.2),
    ],
    BidderDocumentType.UDYAM_CERTIFICATE: [
        ("udyam registration certificate", 0.6),
        ("ministry of micro, small and medium enterprises", 0.5),
        ("msme", 0.3),
        ("enterprise type", 0.3),
        ("national industry classification", 0.3),
    ],
    BidderDocumentType.ASME_CERTIFICATE: [
        ("american society of mechanical engineers", 0.6),
        ("certificate of authorization", 0.5),
        ("u stamp", 0.4),
        ("u2 stamp", 0.4),
        ("asme code", 0.3),
    ],
    BidderDocumentType.GA_DRAWING: [
        ("general arrangement", 0.5),
        ("ga drawing", 0.5),
        ("nozzle schedule", 0.4),
        ("design pressure", 0.2),
        ("design temperature", 0.2),
        ("orientation", 0.2),
    ],
    BidderDocumentType.DESIGN_CALCULATION: [
        ("design calculation", 0.5),
        ("pv elite", 0.4),
        ("compress", 0.4),
        ("asme section viii", 0.4),
        ("maximum allowable working pressure", 0.3),
        ("stress analysis", 0.3),
    ],
    BidderDocumentType.WPS_PQR: [
        ("welding procedure specification", 0.6),
        ("procedure qualification record", 0.6),
        ("wps", 0.3),
        ("pqr", 0.3),
        ("asme section ix", 0.4),
    ],
    BidderDocumentType.MTC_REPORT: [
        ("material test certificate", 0.6),
        ("en 10204", 0.5),
        ("chemical composition", 0.3),
        ("mechanical properties", 0.3),
        ("charpy v-notch", 0.3),
        ("sa-516", 0.3),
    ],
    BidderDocumentType.NDT_REPORT: [
        ("radiographic examination", 0.5),
        ("ultrasonic examination", 0.5),
        ("non-destructive testing", 0.5),
        ("ndt report", 0.5),
        ("asnt level", 0.3),
    ],
    BidderDocumentType.PWHT_REPORT: [
        ("post weld heat treatment", 0.6),
        ("pwht", 0.4),
        ("soaking temperature", 0.4),
        ("heating rate", 0.3),
        ("cooling rate", 0.3),
    ],
    BidderDocumentType.HYDROTEST_REPORT: [
        ("hydrostatic test", 0.6),
        ("hydro test", 0.5),
        ("test pressure", 0.3),
        ("holding time", 0.3),
        ("chloride content", 0.3),
    ],
    BidderDocumentType.INTEGRITY_PACT: [
        ("integrity pact", 0.7),
        ("independent external monitor", 0.5),
        ("iem", 0.3),
        ("commitments of the bidder", 0.4),
    ],
    BidderDocumentType.ZERO_DEVIATION_DECLARATION: [
        ("zero deviation", 0.6),
        ("nil deviation", 0.6),
        ("no deviation certificate", 0.5),
        ("without any deviation", 0.4),
    ],
    BidderDocumentType.MAKE_IN_INDIA_DECLARATION: [
        ("make in india", 0.6),
        ("ppp-mii", 0.5),
        ("local content", 0.4),
        ("class-i local supplier", 0.5),
        ("class-ii local supplier", 0.5),
    ],
    BidderDocumentType.LAND_BORDER_DECLARATION: [
        ("land border", 0.6),
        ("order f.no.6/18/2019-ppd", 0.5),
        ("department of expenditure", 0.4),
        ("beneficial ownership", 0.4),
    ],
    BidderDocumentType.POWER_OF_ATTORNEY: [
        ("power of attorney", 0.6),
        ("board resolution", 0.5),
        ("authorized signatory", 0.4),
        ("attorney", 0.3),
    ],
    BidderDocumentType.FINANCIAL_AUDIT_REPORT: [
        ("independent auditor's report", 0.5),
        ("balance sheet", 0.4),
        ("profit and loss", 0.4),
        ("chartered accountants", 0.3),
        ("udin", 0.4),
    ],
    BidderDocumentType.PRIOR_EXPERIENCE_PROOF: [
        ("purchase order", 0.4),
        ("completion certificate", 0.5),
        ("work completion", 0.4),
        ("inspection release note", 0.4),
        ("client certificate", 0.4),
    ],
}


def classify_bidder_document(text: str, filename: str = "") -> Tuple[BidderDocumentType, float]:
    """Classify bidder document type based on weighted text signals and filename hints."""
    combined_text = (filename + " " + text).lower()
    scores: Dict[BidderDocumentType, float] = {}

    for doc_type, keywords in DOC_TYPE_KEYWORDS.items():
        score = 0.0
        for kw, weight in keywords:
            if kw in combined_text:
                score += weight
        scores[doc_type] = score

    best_type = max(scores, key=scores.get)
    best_score = scores[best_type]

    if best_score < 0.3:
        return BidderDocumentType.OTHER, 0.40

    confidence = min(0.99, max(0.60, best_score))
    return best_type, confidence


def extract_entities_from_text(
    text: str,
    page_number: int = 1,
) -> List[Dict[str, Any]]:
    """Deterministic entity extraction from page text with context extraction."""
    extracted = []

    def _add_entity(e_type: EntityType, raw: str, norm: str, conf: float, start_pos: int):
        # Extract 60 chars before and after for context
        start = max(0, start_pos - 60)
        end = min(len(text), start_pos + len(raw) + 60)
        context = text[start:end].replace("\n", " ").strip()

        extracted.append({
            "page_number": page_number,
            "entity_type": e_type,
            "raw_value": raw.strip(),
            "normalized_value": norm.strip(),
            "confidence": conf,
            "context_snippet": context,
        })

    # 1. GSTIN
    for m in RE_GSTIN.finditer(text):
        gstin = m.group(1).upper()
        _add_entity(EntityType.GSTIN, gstin, gstin, 0.98, m.start())

    # 2. PAN
    for m in RE_PAN.finditer(text):
        pan = m.group(1).upper()
        # Ensure it's not embedded within a GSTIN string at this specific position
        start_idx = m.start()
        end_idx = m.end()
        is_preceded_by_state_code = (start_idx >= 2 and text[start_idx - 2:start_idx].isdigit())
        is_followed_by_gstin_suffix = (end_idx + 3 <= len(text) and re.match(r"^[0-9A-Za-z]{1}Z[0-9A-Za-z]{1}", text[end_idx:end_idx + 3]))
        if is_preceded_by_state_code and is_followed_by_gstin_suffix:
            continue
        _add_entity(EntityType.PAN, pan, pan, 0.95, m.start())

    # 3. Udyam
    for m in RE_UDYAM.finditer(text):
        udyam = m.group(1).upper()
        _add_entity(EntityType.UDYAM_NUMBER, udyam, udyam, 0.99, m.start())

    # 4. Dates
    for m in RE_DATE.finditer(text):
        dt_str = m.group(1)
        _add_entity(EntityType.DATE, dt_str, dt_str, 0.85, m.start())

    # 5. Pressure
    for m in RE_PRESSURE.finditer(text):
        val = m.group(1)
        unit = m.group(2)
        norm = f"{val} {unit}"
        _add_entity(EntityType.PRESSURE_VALUE, m.group(0), norm, 0.90, m.start())

    # 6. Thickness
    for m in RE_THICKNESS.finditer(text):
        val = m.group(1)
        unit = m.group(2)
        norm = f"{val} {unit}"
        _add_entity(EntityType.THICKNESS_VALUE, m.group(0), norm, 0.90, m.start())

    # 7. ASME
    for m in RE_ASME.finditer(text):
        stamp = m.group(1)
        _add_entity(EntityType.ASME_STAMP, stamp, stamp.upper(), 0.92, m.start())

    # 8. Company names
    for m in RE_COMPANY_NAME.finditer(text):
        name = m.group(1).strip()
        # Clean extra spaces
        norm_name = re.sub(r"\s+", " ", name)
        _add_entity(EntityType.COMPANY_NAME, name, norm_name, 0.85, m.start())

    return extracted


async def extract_and_classify_bidder_document(
    session: AsyncSession,
    bidder_id: uuid.UUID,
    document_id: uuid.UUID,
    organization_id: uuid.UUID,
) -> Tuple[BidderDocumentType, float, List[ExtractedEntity]]:
    """Execute complete intelligence pipeline on a bidder document."""
    # 1. Retrieve document & extract text pages
    doc = await get_bidder_document(session, bidder_id, document_id, organization_id)
    pages = await ensure_bidder_pages_extracted(session, doc)

    # 2. Collect full document text
    full_text = "\n".join([p.text_content for p in pages])

    # 3. Classify document
    classified_type, confidence = classify_bidder_document(full_text, doc.original_filename)
    doc.document_type = classified_type

    # 4. Clean previous extracted entities for this document
    await session.execute(
        delete(ExtractedEntity).where(ExtractedEntity.document_id == document_id)
    )

    # 5. Extract entities page by page
    created_entities: List[ExtractedEntity] = []
    seen_keys = set()

    for page in pages:
        page_entities = extract_entities_from_text(page.text_content, page.page_number)
        for e in page_entities:
            # Deduplicate same entity type and normalized value within same document
            key = (e["entity_type"].value, e["normalized_value"].lower())
            if key in seen_keys:
                continue
            seen_keys.add(key)

            ent_obj = ExtractedEntity(
                bidder_id=bidder_id,
                document_id=document_id,
                page_number=e["page_number"],
                entity_type=e["entity_type"],
                raw_value=e["raw_value"],
                normalized_value=e["normalized_value"],
                confidence=e["confidence"],
                context_snippet=e["context_snippet"],
            )
            session.add(ent_obj)
            created_entities.append(ent_obj)

    doc.processing_status = DocumentProcessingStatus.PROCESSED
    await session.commit()
    await session.refresh(doc)
    for ent in created_entities:
        await session.refresh(ent)

    return classified_type, confidence, created_entities

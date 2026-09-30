"""
Procurement Analysis Agent for BidGuard AI.
Performs requirement cross-checking, discrepancy detection, and statutory compliance analysis.
Enforces strict non-autonomous procurement guardrails and complete fallback precautions.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import logging
import re

from app.services.ai.providers import (
    LLMProvider,
    LLMResponse,
    get_ai_providers,
)

logger = logging.getLogger(__name__)


@dataclass
class ComplianceFinding:
    finding_id: str
    criterion_name: str
    status: str  # COMPLIANT, NON_COMPLIANT, PARTIAL, UNCERTAIN
    requirement_summary: str
    bidder_evidence: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW, INFO
    notes: str
    citations: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class ProcurementAnalysisOutput:
    tender_id: Optional[str]
    bidder_id: Optional[str]
    overall_status: str  # REQUIRES_REVIEW, NON_COMPLIANT_FLAGGED, PRELIMINARY_SATISFACTORY
    summary: str
    findings: List[ComplianceFinding] = field(default_factory=list)
    statutory_checks: Dict[str, Any] = field(default_factory=dict)
    discrepancies: List[str] = field(default_factory=list)
    citations: List[Dict[str, Any]] = field(default_factory=list)
    model_used: str = "Qwen/Qwen2.5-1.5B-Instruct"
    used_fallback: bool = False
    disclaimer: str = (
        "NON-AUTONOMOUS NOTICE: BidGuard AI provides analytical evaluation support only. "
        "It does not award tenders, eliminate bidders, or make binding legal judgments. "
        "All evaluation results must be independently verified by the procurement committee."
    )


class AnalysisAgent:
    """
    Agent responsible for domain-specific procurement analysis,
    discrepancy detection, and statutory alignment.
    """

    def __init__(self, llm_provider: Optional[LLMProvider] = None):
        self.llm = llm_provider

    async def _ensure_providers(self):
        if not self.llm:
            try:
                providers = await get_ai_providers()
                self.llm = providers.get("llm")
            except Exception as exc:
                logger.warning("Error loading LLM provider in AnalysisAgent: %s. Using fallback precaution.", exc)
                self.llm = LLMProvider("Qwen/Qwen2.5-1.5B-Instruct")

    async def cross_examine_compliance(
        self,
        tender_id: Optional[str],
        bidder_id: Optional[str],
        requirements: List[Dict[str, Any]],
        bidder_passages: List[Dict[str, Any]],
        query: str = "",
    ) -> ProcurementAnalysisOutput:
        """
        Cross-examine bidder documentation against tender specifications.
        Uses Qwen2.5-1.5B-Instruct with strict non-autonomous prompting and fallback precautions.
        """
        await self._ensure_providers()

        try:
            # 1. Structure the evaluation prompt
            context_blocks = []
            for b in bidder_passages[:8]:
                src = b.get("source_document", "Bid Document")
                pg = b.get("page_number", 1)
                text = b.get("text", "").strip()
                context_blocks.append(f"[{src} - Page {pg}]: {text}")

            context_str = "\n".join(context_blocks) if context_blocks else "No specific submission passages retrieved."

            req_blocks = []
            for r in requirements[:10]:
                r_title = r.get("title") or r.get("name", "Requirement")
                r_desc = r.get("description") or r.get("text", "")
                r_crit = r.get("is_mandatory", True)
                req_blocks.append(f"- {'[MANDATORY]' if r_crit else '[OPTIONAL]'} {r_title}: {r_desc}")

            req_str = "\n".join(req_blocks) if req_blocks else "Standard tender specifications apply."

            prompt = (
                f"You are the BidGuard AI Procurement Analysis Agent. Analyze the following bidder submission "
                f"passages against the mandatory tender requirements.\n\n"
                f"TENDER SPECIFICATIONS:\n{req_str}\n\n"
                f"BIDDER SUBMISSION PASSAGES:\n{context_str}\n\n"
                f"QUERY / FOCUS:\n{query or 'Verify overall compliance and highlight any missing or non-compliant mandatory items.'}\n\n"
                f"Instructions:\n"
                f"1. Detail any discrepancies or omissions.\n"
                f"2. Cite specific page numbers or clauses.\n"
                f"3. Strict rule: NEVER declare a winning bidder or award a contract.\n"
                f"4. Provide an objective analytical summary.\n"
            )

            # 2. Call LLM provider
            llm_resp: LLMResponse = await self.llm.generate(
                prompt=prompt,
                max_tokens=600,
                temperature=0.2,
                context_passages=context_blocks,
            )

            # 3. Rule-based finding extraction as auxiliary validation
            findings, discrepancies = self._extract_findings(requirements, bidder_passages, llm_resp.content)

            # Determine overall preliminary status
            has_critical_failure = any(f.status == "NON_COMPLIANT" and f.severity == "CRITICAL" for f in findings)
            overall_status = "NON_COMPLIANT_FLAGGED" if has_critical_failure else "REQUIRES_REVIEW"

            # Statutory checks (turnover, anti-collusion, validity period)
            statutory_checks = self._perform_statutory_checks(requirements, bidder_passages)

            citations = [
                {
                    "source": b.get("source_document", "Bid Document"),
                    "page": b.get("page_number", 1),
                    "excerpt": b.get("text", "")[:120],
                }
                for b in bidder_passages[:5]
            ]

            return ProcurementAnalysisOutput(
                tender_id=tender_id,
                bidder_id=bidder_id,
                overall_status=overall_status,
                summary=llm_resp.content,
                findings=findings,
                statutory_checks=statutory_checks,
                discrepancies=discrepancies,
                citations=citations,
                model_used=llm_resp.model_name,
                used_fallback=llm_resp.used_fallback,
            )

        except Exception as exc:
            # Fallback Precaution: Complete deterministic rule-based analysis
            logger.error("Unexpected error in AnalysisAgent.cross_examine_compliance: %s. Using fallback precaution.", exc)
            return self._fallback_procurement_analysis(tender_id, bidder_id, requirements, bidder_passages, query)

    def _extract_findings(
        self,
        requirements: List[Dict[str, Any]],
        bidder_passages: List[Dict[str, Any]],
        llm_text: str,
    ) -> tuple[List[ComplianceFinding], List[str]]:
        """Extract structured findings cross-checking requirements with bidder text."""
        findings: List[ComplianceFinding] = []
        discrepancies: List[str] = []

        combined_bidder_text = " ".join(b.get("text", "") for b in bidder_passages).lower()

        for idx, req in enumerate(requirements, start=1):
            title = req.get("title") or req.get("name", f"Requirement {idx}")
            desc = req.get("description") or req.get("text", "")
            is_mandatory = req.get("is_mandatory", True)

            # Simple token matching heuristic for finding status
            keywords = [w.lower() for w in re.findall(r"\w{4,}", title + " " + desc)[:5]]
            match_count = sum(1 for kw in keywords if kw in combined_bidder_text)

            if match_count >= max(1, len(keywords) // 2):
                status = "COMPLIANT"
                notes = f"Evidence matching '{title}' identified in submission."
                severity = "INFO"
            elif match_count > 0:
                status = "PARTIAL"
                notes = f"Partial evidence found for '{title}'. Verification recommended."
                severity = "MEDIUM"
                discrepancies.append(f"Partial coverage for: {title}")
            else:
                status = "NON_COMPLIANT" if is_mandatory else "UNCERTAIN"
                notes = f"No explicit evidence found for mandatory criterion '{title}'."
                severity = "CRITICAL" if is_mandatory else "LOW"
                discrepancies.append(f"Missing documentation for mandatory criterion: {title}")

            findings.append(
                ComplianceFinding(
                    finding_id=f"fnd-{idx}",
                    criterion_name=title,
                    status=status,
                    requirement_summary=desc[:150] or title,
                    bidder_evidence=notes,
                    severity=severity,
                    notes=notes,
                    citations=[],
                )
            )

        return findings, discrepancies

    def _perform_statutory_checks(
        self,
        requirements: List[Dict[str, Any]],
        bidder_passages: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Perform automated checks against statutory procurement provisions."""
        combined_text = " ".join(b.get("text", "") for b in bidder_passages).lower()

        checks = {
            "emd_bank_guarantee_verified": "bank guarantee" in combined_text or "earnest money" in combined_text or "emd" in combined_text,
            "anti_collusion_declaration": "anti-collusion" in combined_text or "integrity pact" in combined_text or "independent bid" in combined_text,
            "tax_clearance_certificate": "tax" in combined_text or "gst" in combined_text or "clearance" in combined_text,
            "financial_turnover_documented": "turnover" in combined_text or "audited" in combined_text or "balance sheet" in combined_text,
            "bid_validity_compliant": "validity" in combined_text or "90 days" in combined_text or "120 days" in combined_text,
        }
        return checks

    def _fallback_procurement_analysis(
        self,
        tender_id: Optional[str],
        bidder_id: Optional[str],
        requirements: List[Dict[str, Any]],
        bidder_passages: List[Dict[str, Any]],
        query: str,
    ) -> ProcurementAnalysisOutput:
        """Deterministic rule-based fallback when LLM encounters an unexpected error."""
        findings, discrepancies = self._extract_findings(requirements, bidder_passages, "")
        statutory_checks = self._perform_statutory_checks(requirements, bidder_passages)

        has_critical = any(f.severity == "CRITICAL" and f.status == "NON_COMPLIANT" for f in findings)
        overall_status = "NON_COMPLIANT_FLAGGED" if has_critical else "REQUIRES_REVIEW"

        summary = (
            f"Rule-based deterministic analysis completed. "
            f"Evaluated {len(requirements)} requirements against available bidder evidence. "
            f"{len(discrepancies)} discrepancy items flagged for human verification."
        )

        return ProcurementAnalysisOutput(
            tender_id=tender_id,
            bidder_id=bidder_id,
            overall_status=overall_status,
            summary=summary,
            findings=findings,
            statutory_checks=statutory_checks,
            discrepancies=discrepancies,
            citations=[],
            model_used="RuleBasedFallback/deterministic",
            used_fallback=True,
        )

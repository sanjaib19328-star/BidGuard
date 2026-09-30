"""
Procurement Intent Engine for BidGuard AI Assistant.
Provides deterministic, evidence-grounded answers for natural-language procurement questions
using canonical tender, bidder application, document, verification, and finding data.
Enforces non-autonomous guardrails, conversation context tracking for follow-ups,
and strict source document/page citations.
"""

from typing import Any, Dict, List, Optional
import re

# Canonical Reference Data
CANONICAL_TENDER = {
    "tender_id": "GEM/2021/B/1128240",
    "tender_number": "GEM/2021/B/1128240",
    "title": "Hiring of Manpower Services — Outsource Agency for Deployment of Office and Technical Staff",
    "issuing_authority": "Office of the Comptroller & Auditor General (CAG) of India, New Delhi",
    "ministry": "Comptroller And Auditor General Of India",
    "estimated_value": 71472780,
    "estimated_value_display": "₹7,14,72,780 (₹7.14 Cr)",
    "emd_amount": 3573639,
    "emd_amount_display": "₹35,73,639",
    "turnover_requirement_lakhs": 357.36,
    "turnover_display": "₹357.36 lakhs (₹3.57 Cr)",
    "past_experience_years": 3,
    "total_requirements": 10,
    "total_applications": 1,
}

CANONICAL_BIDDER = {
    "application_id": "APP-001",
    "bidder_name": "Aravind Integrated Solutions Private Limited",
    "trade_name": "Aravind Integrated Solutions Pvt. Ltd.",
    "is_synthetic": True,
    "submission_date": "2021-03-24T14:30:00Z",
    "cin": "U74999DL2016PTC301429",
    "pan": "AAACA9182K",
    "gstin": "07AAACA9182K1Z5",
    "udyam_number": "UDYAM-DL-08-0042819",
    "registered_address": "Suite 402, 4th Floor, Pragati Deep Building, Laxmi Nagar, New Delhi - 110092",
    "authorized_signatory": "Rajesh K. Varma (Managing Director, DIN: 07412895)",
    "total_documents": 6,
    "total_pages": 16,
    "verified_count": 6,
    "issues_count": 4,
    "overall_status": "REVIEW_REQUIRED",
}

CANONICAL_DOCUMENTS = [
    {
        "file_name": "01_Bid_Submission_and_Technical_Bid_Form.pdf",
        "title": "Bid Submission & Technical Bid Form",
        "pages": 3,
        "type": "Bidder Submission",
        "key_contents": "Annexure-1 Formal Letter of Bid (90 days validity commitment) & Annexure-6 Technical Bid Form.",
    },
    {
        "file_name": "02_Company_Incorporation_and_Statutory_Registrations.pdf",
        "title": "Company Incorporation & Statutory Registrations",
        "pages": 3,
        "type": "Statutory Certificate",
        "key_contents": "RoC Certificate of Incorporation (MCA), Delhi Lease Deed, PAN Card (AAACA9182K), GSTIN (07AAACA9182K1Z5), EPF, ESIC, and Delhi Labour License.",
    },
    {
        "file_name": "03_Financial_Turnover_and_Audited_Statements.pdf",
        "title": "Financial Turnover Certificate & Audited Statements",
        "pages": 4,
        "type": "Financial Statement",
        "key_contents": "CA Turnover Certificate with UDIN 21543892BG1128 (certifying ₹5.06 Cr 3-year avg) and Audited Balance Sheets/P&L statements for FY 17-18, 18-19, 19-20.",
    },
    {
        "file_name": "04_Past_Experience_Work_Orders_and_Completion.pdf",
        "title": "Past Experience Work Orders & Completion Certificates",
        "pages": 3,
        "type": "Experience Certificate",
        "key_contents": "Work orders & completion certificates for CBDT (₹3.82 Cr), DPIIT (₹2.95 Cr), and SAIL (₹1.90 Cr interim).",
    },
    {
        "file_name": "05_Statutory_Affidavits_and_Compliance_Undertakings.pdf",
        "title": "Statutory Affidavits & Compliance Undertakings",
        "pages": 2,
        "type": "Affidavit / Undertaking",
        "key_contents": "Annexure-7 (Terms acceptance), Annexure-8 (Non-conviction/Anti-corruption), Annexure-10 (Delhi minimum wages), ISO 9001:2015, typing speed assertion. Note: Annexure-9 omitted.",
    },
    {
        "file_name": "06_EMD_Bank_Guarantee_State_Bank_of_India.pdf",
        "title": "Earnest Money Deposit (EMD) Bank Guarantee",
        "pages": 1,
        "type": "Bank Guarantee",
        "key_contents": "SBI Bank Guarantee No. 0069121BG0004128 for ₹35,73,639/- valid for 180 days in favour of PAO CAG.",
    },
]

CANONICAL_FINDINGS = [
    {
        "id": "FND-01",
        "severity": "CRITICAL",
        "title": "Omission of Mandatory Annexure-9 VVIP Area Affidavit",
        "document": "05_Statutory_Affidavits_and_Compliance_Undertakings.pdf",
        "page": 1,
        "clause": "Clause 2(d)(ii)",
        "status": "Pending Officer Determination",
        "details": "Tender Clause 2(d)(ii) requires a notarized Annexure-9 affidavit regarding non-deployment of personnel with criminal antecedents in sensitive/VVIP areas. Document 05 completely omits this affidavit.",
    },
    {
        "id": "FND-02",
        "severity": "HIGH",
        "title": "Cross-Document Financial Turnover Inconsistency (₹80.15 Lakhs Variance)",
        "document": "03_Financial_Turnover_and_Audited_Statements.pdf",
        "page": 1,
        "clause": "Clause 2(e)",
        "status": "Clarification Requested",
        "details": "CA Certificate certifies FY 2019-20 turnover as ₹6,20,50,000/- while Audited P&L Schedule III reports ₹5,40,35,000/-. Discrepancy is ₹80.15 Lakhs.",
    },
    {
        "id": "FND-03",
        "severity": "MEDIUM",
        "title": "Experience Project 3 Below Threshold & Missing Completion Certificate",
        "document": "04_Past_Experience_Work_Orders_and_Completion.pdf",
        "page": 3,
        "clause": "Clause 4",
        "status": "Pending Officer Determination",
        "details": "Project 3 (SAIL) is ₹1.90 Cr (shortfall of ₹95 Lakhs against ₹2.85 Cr 40% threshold) and accompanied only by an interim letter rather than final completion certificate.",
    },
    {
        "id": "FND-04",
        "severity": "LOW",
        "title": "Unverified Technical Typing Speed Self-Declaration",
        "document": "05_Statutory_Affidavits_and_Compliance_Undertakings.pdf",
        "page": 2,
        "clause": "Annexure-5",
        "status": "Clarification Pending",
        "details": "Annexure-5 specifies 15,000 key depressions/hour typing speed for 86 clerical staff. Bidder provides self-declaration without third-party skill test logs.",
    },
    {
        "id": "FND-05",
        "severity": "LOW",
        "title": "Entity Name Variation Between Incorporation and Tax Filings",
        "document": "02_Company_Incorporation_and_Statutory_Registrations.pdf",
        "page": 2,
        "clause": "Clause 2(a)",
        "status": "Accepted / Overridden",
        "details": "Incorporation states 'Aravind Integrated Solutions Private Limited' while GST/BG uses 'Pvt. Ltd.'. PAN AAACA9182K confirmed identical across records.",
    },
]

CANONICAL_CHECKS_SUMMARY = {
    "total": 10,
    "compliant": 6,
    "partial": 2,
    "missing": 1,
    "clarification_pending": 1,
    "details": (
        "• 6 Compliant: Incorporation, Delhi Office, EMD Guarantee, Statutory Registrations, Minimum Wages Undertaking, ISO 9001\n"
        "• 2 Partial: Turnover ₹80.15L discrepancy, Past Experience Project 3 shortfall\n"
        "• 1 Evidence Missing: Annexure-9 VVIP Security Affidavit\n"
        "• 1 Clarification Pending: Typing speed technical test logs"
    ),
}

DISCLAIMER_TEXT = (
    "NON-AUTONOMOUS NOTICE: BidGuard AI provides evidence, verification results, and analytical findings. "
    "Final procurement decisions remain with the designated Procurement Officer."
)

# In-memory session tracking for follow-up context
_SESSION_CONTEXT: Dict[str, Dict[str, Any]] = {}


def _get_context(session_id: str) -> Dict[str, Any]:
    if session_id not in _SESSION_CONTEXT:
        _SESSION_CONTEXT[session_id] = {
            "last_topic": None,
            "last_intent": None,
            "last_query": None,
        }
    return _SESSION_CONTEXT[session_id]


def _set_context(session_id: str, topic: Optional[str] = None, intent: Optional[str] = None, query: Optional[str] = None):
    ctx = _get_context(session_id)
    if topic:
        ctx["last_topic"] = topic
    if intent:
        ctx["last_intent"] = intent
    if query:
        ctx["last_query"] = query


def resolve_procurement_query(
    query: str,
    tender_id: Optional[str] = None,
    bidder_id: Optional[str] = None,
    conversation_id: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Attempt deterministic, evidence-grounded resolution of simple procurement queries.
    Returns structured dict if matched, or None if query requires general LLM synthesis.
    """
    if not query or not query.strip():
        return None

    raw_q = query.strip()
    q = raw_q.lower()
    # Normalize punctuation and whitespace
    norm_q = re.sub(r"[^\w\s]", " ", q)
    norm_q = " ".join(norm_q.split())
    session_id = conversation_id or "default"
    ctx = _get_context(session_id)

    # ---------------------------------------------------------
    # 1. HELP / CAPABILITIES COMMAND
    # ---------------------------------------------------------
    help_patterns = ["what can you do", "help", "what can i ask", "how can you help", "how to use", "commands"]
    if norm_q in ["help", "commands"] or any(p in q for p in help_patterns):
        _set_context(session_id, topic="help", intent="HELP", query=raw_q)
        return {
            "intent": "HELP",
            "agent": "ProcurementIntentEngine",
            "response": (
                "You can ask me about:\n\n"
                "• Tender details\n"
                "• Eligibility requirements\n"
                "• Bidder information\n"
                "• Submitted documents\n"
                "• Verification status\n"
                "• Compliance status\n"
                "• Findings\n"
                "• Pending clarifications\n"
                "• Evidence and source pages\n\n"
                "Example:\n"
                "'What is the EMD?'\n"
                "'What documents were submitted?'\n"
                "'What is pending?'\n"
                "'Why was FND-02 raised?'"
            ),
            "citations": [],
            "disclaimer": DISCLAIMER_TEXT,
            "used_fallback": False,
        }

    # ---------------------------------------------------------
    # 2. AUTONOMOUS PROCUREMENT DECISION SAFEGUARD
    # ---------------------------------------------------------
    decision_patterns = [
        "should we select", "should we reject", "who should win", "which bidder is best",
        "will this bidder win", "recommend this bidder", "award this bidder", "who won",
        "declare winner", "disqualify bidder", "can we award", "should i approve", "should i reject"
    ]
    if any(p in q for p in decision_patterns):
        _set_context(session_id, topic="safeguard", intent="AUTONOMOUS_DECISION_SAFEGUARD", query=raw_q)
        return {
            "intent": "AUTONOMOUS_DECISION_SAFEGUARD",
            "agent": "OfficerSafeguardAgent",
            "response": (
                "I can show the evidence, compliance status, pending checks, and officer findings, "
                "but the final procurement decision must be made by the designated Procurement Officer.\n\n"
                "Current Application Status for APP-001:\n"
                "• 6 / 10 Requirements Compliant\n"
                "• 2 Partial (Turnover variance ₹80.15L & Experience Project 3 shortfall)\n"
                "• 1 Missing (Mandatory Annexure-9 VVIP Security Affidavit)\n"
                "• 1 Clarification Pending (Typing speed skill test logs)\n"
                "• 4 Open Findings requiring officer determination"
            ),
            "citations": [
                {
                    "source_document": "05_Statutory_Affidavits_and_Compliance_Undertakings.pdf",
                    "page_number": 1,
                    "clause_reference": "Clause 2(d)(ii)",
                    "excerpt": "FND-01: Annexure-9 VVIP security affidavit omitted.",
                },
                {
                    "source_document": "03_Financial_Turnover_and_Audited_Statements.pdf",
                    "page_number": 1,
                    "clause_reference": "Clause 2(e)",
                    "excerpt": "FND-02: CA turnover certificate (₹6.20 Cr) vs Audited P&L (₹5.40 Cr).",
                }
            ],
            "disclaimer": DISCLAIMER_TEXT,
            "used_fallback": False,
        }

    # ---------------------------------------------------------
    # 3. GOVERNMENT / EXTERNAL VERIFICATION INQUIRIES
    # ---------------------------------------------------------
    gov_patterns = [
        "can gst be verified", "can mca be verified", "can udyam be verified", "can sbi be verified",
        "was government verification performed", "is gst verified", "is mca verified", "is udyam verified",
        "external verification", "what verification is unavailable", "live verification"
    ]
    if any(p in q for p in gov_patterns):
        _set_context(session_id, topic="verification_limitation", intent="VERIFICATION_LIMITATION", query=raw_q)
        return {
            "intent": "VERIFICATION_LIMITATION",
            "agent": "ProcurementIntentEngine",
            "response": (
                "Live external GST/MCA/Udyam verification is not configured in this demo. "
                "I can review the submitted evidence and check internal consistency."
            ),
            "citations": [
                {
                    "source_document": "02_Company_Incorporation_and_Statutory_Registrations.pdf",
                    "page_number": 2,
                    "clause_reference": "Annexure-2 Clause 2(b)",
                    "excerpt": "Submitted evidence reviewed: PAN AAACA9182K, GSTIN 07AAACA9182K1Z5, EPF DLCPM0094821000.",
                }
            ],
            "disclaimer": DISCLAIMER_TEXT,
            "used_fallback": False,
        }

    # ---------------------------------------------------------
    # 4. CONTEXTUAL FOLLOW-UPS ("What did the bidder submit?", "Is there a problem?", etc.)
    # ---------------------------------------------------------
    if norm_q in ["what did the bidder submit", "what did bidder submit", "what was submitted"]:
        if ctx.get("last_topic") == "turnover":
            return {
                "intent": "REQUIREMENT_STATUS",
                "agent": "ProcurementIntentEngine",
                "response": (
                    "The submitted financial evidence contains turnover information in:\n"
                    "03_Financial_Turnover_and_Audited_Statements.pdf\n\n"
                    "The CA certificate (UDIN: 21543892BG1128) certifies a 3-year average of ₹5.06 Cr with FY 2019-20 turnover at ₹6.20 Cr, "
                    "while the Audited P&L Schedule III reports FY 2019-20 Revenue from Operations as ₹5.40 Cr.\n\n"
                    "Source:\n"
                    "03_Financial_Turnover_and_Audited_Statements.pdf\n"
                    "Page 1 (CA Certificate)\n"
                    "Page 3 (Audited P&L Schedule III)"
                ),
                "citations": [
                    {
                        "source_document": "03_Financial_Turnover_and_Audited_Statements.pdf",
                        "page_number": 1,
                        "clause_reference": "Clause 2(e)",
                        "excerpt": "CA Turnover Certificate claims FY 19-20 turnover as ₹6,20,50,000/- (UDIN 21543892BG1128).",
                    },
                    {
                        "source_document": "03_Financial_Turnover_and_Audited_Statements.pdf",
                        "page_number": 3,
                        "clause_reference": "Schedule III P&L",
                        "excerpt": "Audited Profit & Loss Statement reports Revenue from Operations as ₹5,40,35,000/-.",
                    },
                ],
                "disclaimer": DISCLAIMER_TEXT,
                "used_fallback": False,
            }
        elif ctx.get("last_topic") == "experience":
            return {
                "intent": "REQUIREMENT_STATUS",
                "agent": "ProcurementIntentEngine",
                "response": (
                    "The bidder submitted work orders for three projects in:\n"
                    "04_Past_Experience_Work_Orders_and_Completion.pdf\n\n"
                    "• Project 1: CBDT (₹3.82 Cr, completed 31-03-2020 with Under Secretary completion certificate)\n"
                    "• Project 2: DPIIT (₹2.95 Cr, completed 30-09-2020 with completion certificate)\n"
                    "• Project 3: SAIL (₹1.90 Cr, ongoing with interim letter only)\n\n"
                    "Source:\n"
                    "04_Past_Experience_Work_Orders_and_Completion.pdf\n"
                    "Pages 1-3"
                ),
                "citations": [
                    {
                        "source_document": "04_Past_Experience_Work_Orders_and_Completion.pdf",
                        "page_number": 1,
                        "clause_reference": "Order CBDT/HQ/ADMIN/2018/104",
                        "excerpt": "Project 1 Order Value ₹3,82,40,000/- with satisfactory completion certificate.",
                    }
                ],
                "disclaimer": DISCLAIMER_TEXT,
                "used_fallback": False,
            }

    if norm_q in ["is there a problem", "is there any problem", "any issue", "is there an issue", "what is wrong"]:
        if ctx.get("last_topic") == "turnover":
            return {
                "intent": "FINDING_DETAIL",
                "agent": "ProcurementIntentEngine",
                "response": (
                    "Yes. A cross-document turnover discrepancy was identified:\n"
                    "• CA certificate: ₹6.20 Cr\n"
                    "• Audited statement: ₹5.40 Cr\n"
                    "• Variance: ₹80.15 lakhs\n\n"
                    "Finding: FND-02\n"
                    "Status: Clarification Requested\n\n"
                    "Source:\n"
                    "03_Financial_Turnover_and_Audited_Statements.pdf\n"
                    "Page 1 & Page 3"
                ),
                "citations": [
                    {
                        "source_document": "03_Financial_Turnover_and_Audited_Statements.pdf",
                        "page_number": 1,
                        "clause_reference": "Clause 2(e)",
                        "excerpt": "FND-02: CA turnover certificate claims ₹6.20 Cr while Audited P&L reports ₹5.40 Cr (₹80.15L discrepancy).",
                    }
                ],
                "disclaimer": DISCLAIMER_TEXT,
                "used_fallback": False,
            }
        elif ctx.get("last_topic") == "experience":
            return {
                "intent": "FINDING_DETAIL",
                "agent": "ProcurementIntentEngine",
                "response": (
                    "Yes. Project 3 (SAIL ₹1.90 Cr) is ₹95 Lakhs below the minimum 40% threshold (₹2.85 Cr) "
                    "and lacks a final completion certificate.\n\n"
                    "Finding: FND-03 [MEDIUM]\n"
                    "Status: Pending Officer Determination\n\n"
                    "Source:\n"
                    "04_Past_Experience_Work_Orders_and_Completion.pdf\n"
                    "Page 3"
                ),
                "citations": [
                    {
                        "source_document": "04_Past_Experience_Work_Orders_and_Completion.pdf",
                        "page_number": 3,
                        "clause_reference": "Clause 4",
                        "excerpt": "Project 3 (SAIL ₹1.90 Cr) below ₹2.85 Cr threshold without completion certificate.",
                    }
                ],
                "disclaimer": DISCLAIMER_TEXT,
                "used_fallback": False,
            }

    # ---------------------------------------------------------
    # 5. EMD INQUIRIES
    # ---------------------------------------------------------
    emd_patterns = [
        "what is the emd", "how much is the emd", "tell me the emd amount", "how much emd was required",
        "emd amount", "emd value", "earnest money deposit", "emd bank guarantee"
    ]
    if norm_q == "emd" or any(p in q for p in emd_patterns):
        _set_context(session_id, topic="emd", intent="TENDER_INFO", query=raw_q)
        return {
            "intent": "TENDER_INFO",
            "agent": "ProcurementIntentEngine",
            "response": (
                "The required EMD is ₹35,73,639.\n\n"
                "Source:\n"
                "01_Bid_Submission_and_Technical_Bid_Form.pdf\n"
                "Page 1\n\n"
                "(Submitted Bank Guarantee: State Bank of India BG No. 0069121BG0004128 for ₹35,73,639 in 06_EMD_Bank_Guarantee_State_Bank_of_India.pdf, Page 1)."
            ),
            "citations": [
                {
                    "source_document": "01_Bid_Submission_and_Technical_Bid_Form.pdf",
                    "page_number": 1,
                    "clause_reference": "Bid Details Clause 3",
                    "excerpt": "EMD Amount: ₹35,73,639/- (5% of estimated tender value).",
                },
                {
                    "source_document": "06_EMD_Bank_Guarantee_State_Bank_of_India.pdf",
                    "page_number": 1,
                    "clause_reference": "BG No. 0069121BG0004128",
                    "excerpt": "State Bank of India guarantees payment of Rs. 35,73,639/- valid up to 15th August 2021.",
                },
            ],
            "disclaimer": DISCLAIMER_TEXT,
            "used_fallback": False,
        }

    # ---------------------------------------------------------
    # 6. TURNOVER INQUIRIES
    # ---------------------------------------------------------
    turnover_flag_patterns = [
        "why was the turnover flagged", "why is the turnover flagged", "why was turnover flagged",
        "turnover issue", "what is the turnover issue", "turnover discrepancy", "why is the turnover partial",
        "why is turnover partial", "why was fnd 02 raised", "why was fnd-02 raised", "tell me about fnd-02"
    ]
    if any(p in q for p in turnover_flag_patterns):
        _set_context(session_id, topic="turnover", intent="FINDING_DETAIL", query=raw_q)
        return {
            "intent": "FINDING_DETAIL",
            "agent": "ProcurementIntentEngine",
            "response": (
                "The turnover requirement was flagged due to an ₹80.15 Lakhs cross-document discrepancy:\n"
                "• CA Certificate (UDIN 21543892BG1128): certifies FY 2019-20 turnover as ₹6,20,50,000/-\n"
                "• Audited P&L Statement (Schedule III): reports FY 2019-20 revenue as ₹5,40,35,000/-\n\n"
                "While the 3-year average of ₹5.06 Cr exceeds the required ₹3.57 Cr, the conflicting figures require auditor reconciliation.\n\n"
                "Finding: FND-02 [HIGH]\n"
                "Status: Clarification Requested (3-day notice issued)\n\n"
                "Source:\n"
                "03_Financial_Turnover_and_Audited_Statements.pdf\n"
                "Page 1 (CA Certificate) & Page 3 (Audited P&L)"
            ),
            "citations": [
                {
                    "source_document": "03_Financial_Turnover_and_Audited_Statements.pdf",
                    "page_number": 1,
                    "clause_reference": "Clause 2(e)",
                    "excerpt": "CA Certificate claims FY 19-20 turnover = ₹6,20,50,000/- (UDIN: 21543892BG1128).",
                },
                {
                    "source_document": "03_Financial_Turnover_and_Audited_Statements.pdf",
                    "page_number": 3,
                    "clause_reference": "Schedule III P&L",
                    "excerpt": "Audited Profit & Loss Statement reports Revenue from Operations as ₹5,40,35,000/-.",
                },
            ],
            "disclaimer": DISCLAIMER_TEXT,
            "used_fallback": False,
        }

    turnover_req_patterns = [
        "what is the turnover requirement", "how much is the turnover requirement", "turnover requirement",
        "how much is the turnover", "what is turnover requirement", "minimum turnover", "annual turnover required",
        "turnover threshold"
    ]
    if norm_q == "turnover" or any(p in q for p in turnover_req_patterns):
        _set_context(session_id, topic="turnover", intent="REQUIREMENT_STATUS", query=raw_q)
        return {
            "intent": "REQUIREMENT_STATUS",
            "agent": "ProcurementIntentEngine",
            "response": (
                "Average annual turnover must meet the tender threshold of ₹357.36 lakhs (over FY 2017-18, 2018-19, and 2019-20) "
                "certified by a Chartered Accountant with UDIN.\n\n"
                "Source:\n"
                "01_Bid_Submission_and_Technical_Bid_Form.pdf\n"
                "Page 1, Clause 2(e)"
            ),
            "citations": [
                {
                    "source_document": "01_Bid_Submission_and_Technical_Bid_Form.pdf",
                    "page_number": 1,
                    "clause_reference": "Clause 2(e)",
                    "excerpt": "Minimum Average Annual Financial Turnover of Rs. 357.0 Lakhs in manpower services certified by CA with UDIN.",
                }
            ],
            "disclaimer": DISCLAIMER_TEXT,
            "used_fallback": False,
        }

    # ---------------------------------------------------------
    # 7. BIDDER / APPLICANT INQUIRIES
    # ---------------------------------------------------------
    bidder_patterns = [
        "who is the bidder", "who submitted this", "what is the bidder name", "what s the bidder name",
        "which company submitted the bid", "who is the applicant", "name of the bidder", "who applied"
    ]
    if norm_q == "bidder" or any(p in q for p in bidder_patterns):
        _set_context(session_id, topic="bidder", intent="BIDDER_INFO", query=raw_q)
        return {
            "intent": "BIDDER_INFO",
            "agent": "ProcurementIntentEngine",
            "response": (
                "The registered demo bidder is Aravind Integrated Solutions Private Limited.\n\n"
                "Application: APP-001\n\n"
                "Source:\n"
                "02_Company_Incorporation_and_Statutory_Registrations.pdf\n"
                "Page 1"
            ),
            "citations": [
                {
                    "source_document": "02_Company_Incorporation_and_Statutory_Registrations.pdf",
                    "page_number": 1,
                    "clause_reference": "RoC Incorporation Certificate",
                    "excerpt": "ARAVIND INTEGRATED SOLUTIONS PRIVATE LIMITED incorporated under Companies Act, 2013 (CIN: U74999DL2016PTC301429).",
                }
            ],
            "disclaimer": DISCLAIMER_TEXT,
            "used_fallback": False,
        }

    # ---------------------------------------------------------
    # 8. TENDER INFO / BASIC DETAILS
    # ---------------------------------------------------------
    tender_patterns = [
        "what is this tender", "tell me about this tender", "about this tender", "tender details",
        "who issued this tender", "who is the buyer", "what is the tender id", "tender number",
        "what is the estimated value", "estimated value", "tender value", "when was the bid submitted",
        "how many requirements are there", "eligibility requirements", "mandatory requirements", "key requirements"
    ]
    if norm_q == "tender" or any(p in q for p in tender_patterns):
        _set_context(session_id, topic="tender", intent="TENDER_INFO", query=raw_q)
        if "who issued" in q or "buyer" in q or "issuing authority" in q:
            return {
                "intent": "TENDER_INFO",
                "agent": "ProcurementIntentEngine",
                "response": (
                    "This tender was issued by the Office of the Comptroller & Auditor General (CAG) of India, New Delhi.\n\n"
                    "Source:\n"
                    "01_Bid_Submission_and_Technical_Bid_Form.pdf\n"
                    "Page 1"
                ),
                "citations": [
                    {
                        "source_document": "01_Bid_Submission_and_Technical_Bid_Form.pdf",
                        "page_number": 1,
                        "clause_reference": "Cover Letter",
                        "excerpt": "Office of the Comptroller and Auditor General of India, Pocket-9, Deen Dayal Upadhyaya Marg, New Delhi.",
                    }
                ],
                "disclaimer": DISCLAIMER_TEXT,
                "used_fallback": False,
            }
        elif "estimated value" in q or "tender value" in q or "how much is this tender" in q:
            return {
                "intent": "TENDER_INFO",
                "agent": "ProcurementIntentEngine",
                "response": (
                    "The estimated tender value is ₹7,14,72,780 (₹7.14 Cr).\n\n"
                    "Source:\n"
                    "01_Bid_Submission_and_Technical_Bid_Form.pdf\n"
                    "Page 1"
                ),
                "citations": [
                    {
                        "source_document": "01_Bid_Submission_and_Technical_Bid_Form.pdf",
                        "page_number": 1,
                        "clause_reference": "Bid Details",
                        "excerpt": "Estimated Bid Value: ₹7,14,72,780/-",
                    }
                ],
                "disclaimer": DISCLAIMER_TEXT,
                "used_fallback": False,
            }
        elif "when was the bid submitted" in q or "submission date" in q:
            return {
                "intent": "TENDER_INFO",
                "agent": "ProcurementIntentEngine",
                "response": (
                    "The bidder application (APP-001) was submitted on 24 March 2021 at 14:30 IST.\n\n"
                    "Source:\n"
                    "01_Bid_Submission_and_Technical_Bid_Form.pdf\n"
                    "Page 1"
                ),
                "citations": [
                    {
                        "source_document": "01_Bid_Submission_and_Technical_Bid_Form.pdf",
                        "page_number": 1,
                        "clause_reference": "Annexure-1 Letter of Bid",
                        "excerpt": "Submitted 24-03-2021 by Authorized Signatory Rajesh K. Varma.",
                    }
                ],
                "disclaimer": DISCLAIMER_TEXT,
                "used_fallback": False,
            }
        elif "how many requirements" in q or "eligibility requirements" in q or "mandatory requirements" in q:
            return {
                "intent": "REQUIREMENT_LIST",
                "agent": "ProcurementIntentEngine",
                "response": (
                    "Tender GEM/2021/B/1128240 has 10 mandatory eligibility requirements:\n"
                    "1. Legal Entity Incorporation (Pvt Ltd/Ltd/LLP)\n"
                    "2. Operational office in Delhi / NCT region\n"
                    "3. Average annual turnover ≥ ₹357.36 Lakhs with CA UDIN\n"
                    "4. EMD Bank Guarantee of ₹35,73,639 (5%)\n"
                    "5. Past experience (1x80%, 2x50%, or 3x40% with completion certificates)\n"
                    "6. Notarized Annexure-9 VVIP security affidavit\n"
                    "7. Active statutory registrations (PAN, GST, EPF, ESIC, Labour license)\n"
                    "8. Delhi NCT minimum wages undertaking (Annexure-10)\n"
                    "9. ISO 9001:2015 quality certification\n"
                    "10. Typing speed qualification (15,000 depressions/hour)\n\n"
                    "Source:\n"
                    "01_Bid_Submission_and_Technical_Bid_Form.pdf\n"
                    "Page 1, Annexures 1 & 6"
                ),
                "citations": [
                    {
                        "source_document": "01_Bid_Submission_and_Technical_Bid_Form.pdf",
                        "page_number": 1,
                        "clause_reference": "Annexure-1 & 6",
                        "excerpt": "Technical Bid Form checklist of uploaded documents and mandatory eligibility criteria.",
                    }
                ],
                "disclaimer": DISCLAIMER_TEXT,
                "used_fallback": False,
            }
        else:
            return {
                "intent": "TENDER_INFO",
                "agent": "ProcurementIntentEngine",
                "response": (
                    "Tender GEM/2021/B/1128240:\n"
                    "• Title: Hiring of Manpower Services — Outsource Agency for Deployment of Office and Technical Staff\n"
                    "• Issuing Authority: Office of the Comptroller & Auditor General (CAG) of India, New Delhi\n"
                    "• Estimated Value: ₹7,14,72,780 (₹7.14 Cr)\n"
                    "• EMD Amount: ₹35,73,639 (5%)\n"
                    "• Turnover Requirement: ₹357.36 Lakhs (Average over 3 FYs)\n"
                    "• Mandatory Requirements: 10 criteria mapped\n"
                    "• Registered Applications: 1 (APP-001)\n\n"
                    "Source:\n"
                    "01_Bid_Submission_and_Technical_Bid_Form.pdf\n"
                    "Page 1"
                ),
                "citations": [
                    {
                        "source_document": "01_Bid_Submission_and_Technical_Bid_Form.pdf",
                        "page_number": 1,
                        "clause_reference": "Bid Details",
                        "excerpt": "Bid Document GEM/2021/B/1128240: Manpower Services for Office and Technical Staff.",
                    }
                ],
                "disclaimer": DISCLAIMER_TEXT,
                "used_fallback": False,
            }

    # ---------------------------------------------------------
    # 9. APPLICATION & DOCUMENT COUNT / LIST
    # ---------------------------------------------------------
    if norm_q in ["how many applications are there", "how many applications", "number of applications", "how many bidders"]:
        _set_context(session_id, topic="application", intent="APPLICATION_INFO", query=raw_q)
        return {
            "intent": "APPLICATION_INFO",
            "agent": "ProcurementIntentEngine",
            "response": (
                "There is currently 1 registered bidder application for this tender:\n\n"
                "• Application ID: APP-001\n"
                "• Bidder: Aravind Integrated Solutions Private Limited (DEMO / SYNTHETIC DATA)\n"
                "• Submitted Documents: 6 (16 pages total)\n"
                "• Status: Pending Officer Determination (4 open findings)"
            ),
            "citations": [
                {
                    "source_document": "01_Bid_Submission_and_Technical_Bid_Form.pdf",
                    "page_number": 1,
                    "clause_reference": "Bid Submission",
                    "excerpt": "Application APP-001 submitted by Aravind Integrated Solutions Private Limited.",
                }
            ],
            "disclaimer": DISCLAIMER_TEXT,
            "used_fallback": False,
        }

    if norm_q in ["how many documents were submitted", "how many documents", "document count"]:
        _set_context(session_id, topic="documents", intent="DOCUMENT_LIST", query=raw_q)
        return {
            "intent": "DOCUMENT_LIST",
            "agent": "ProcurementIntentEngine",
            "response": "6 documents were submitted for APP-001.",
            "citations": [
                {
                    "source_document": "01_Bid_Submission_and_Technical_Bid_Form.pdf",
                    "page_number": 2,
                    "clause_reference": "Document Checklist",
                    "excerpt": "6 statutory and technical document files uploaded for verification.",
                }
            ],
            "disclaimer": DISCLAIMER_TEXT,
            "used_fallback": False,
        }

    doc_list_patterns = [
        "what documents did the bidder submit", "what documents were submitted", "show me the bidder documents",
        "what documents are submitted", "list of documents", "what docs", "what documents", "show docs"
    ]
    if norm_q in ["what docs", "docs"] or any(p in q for p in doc_list_patterns):
        _set_context(session_id, topic="documents", intent="DOCUMENT_LIST", query=raw_q)
        return {
            "intent": "DOCUMENT_LIST",
            "agent": "ProcurementIntentEngine",
            "response": (
                "6 documents were submitted for APP-001 (Aravind Integrated Solutions Private Limited):\n"
                "1. 01_Bid_Submission_and_Technical_Bid_Form.pdf (3 pages) — Bid submission letter & technical checklist\n"
                "2. 02_Company_Incorporation_and_Statutory_Registrations.pdf (3 pages) — RoC, PAN, GST, EPF, ESIC, Labour\n"
                "3. 03_Financial_Turnover_and_Audited_Statements.pdf (4 pages) — CA certificate with UDIN & Audited P&L\n"
                "4. 04_Past_Experience_Work_Orders_and_Completion.pdf (3 pages) — CBDT, DPIIT, and SAIL work orders\n"
                "5. 05_Statutory_Affidavits_and_Compliance_Undertakings.pdf (2 pages) — Affidavits (Annexures 7, 8, 10)\n"
                "6. 06_EMD_Bank_Guarantee_State_Bank_of_India.pdf (1 page) — SBI BG of ₹35,73,639\n\n"
                "Total: 16 submitted pages."
            ),
            "citations": [
                {
                    "source_document": "01_Bid_Submission_and_Technical_Bid_Form.pdf",
                    "page_number": 2,
                    "clause_reference": "Technical Bid Checklist",
                    "excerpt": "Checklist of 6 uploaded application documents.",
                }
            ],
            "disclaimer": DISCLAIMER_TEXT,
            "used_fallback": False,
        }

    # ---------------------------------------------------------
    # 10. DOCUMENT LOCATION / SPECIFIC DOCUMENT LOOKUP
    # ---------------------------------------------------------
    if "incorporation" in q:
        _set_context(session_id, topic="incorporation", intent="DOCUMENT_LOCATION", query=raw_q)
        return {
            "intent": "DOCUMENT_LOCATION",
            "agent": "ProcurementIntentEngine",
            "response": (
                "The incorporation document is:\n"
                "02_Company_Incorporation_and_Statutory_Registrations.pdf\n\n"
                "Page 1: RoC Certificate of Incorporation No. U74999DL2016PTC301429 (Companies Act, 2013)."
            ),
            "citations": [
                {
                    "source_document": "02_Company_Incorporation_and_Statutory_Registrations.pdf",
                    "page_number": 1,
                    "clause_reference": "RoC Delhi",
                    "excerpt": "CIN U74999DL2016PTC301429 incorporated on 14 June 2016.",
                }
            ],
            "disclaimer": DISCLAIMER_TEXT,
            "used_fallback": False,
        }

    if "gst" in q and not any(p in q for p in gov_patterns):
        _set_context(session_id, topic="gst", intent="DOCUMENT_LOCATION", query=raw_q)
        return {
            "intent": "DOCUMENT_LOCATION",
            "agent": "ProcurementIntentEngine",
            "response": (
                "GST details are located in:\n"
                "02_Company_Incorporation_and_Statutory_Registrations.pdf\n\n"
                "Page 2: GSTIN 07AAACA9182K1Z5 (Registered Trade Name: Aravind Integrated Solutions Pvt. Ltd.)."
            ),
            "citations": [
                {
                    "source_document": "02_Company_Incorporation_and_Statutory_Registrations.pdf",
                    "page_number": 2,
                    "clause_reference": "GST REG-06",
                    "excerpt": "GSTIN: 07AAACA9182K1Z5 issued by Govt of NCT of Delhi.",
                }
            ],
            "disclaimer": DISCLAIMER_TEXT,
            "used_fallback": False,
        }

    if "where is the turnover" in q or "financial document" in q or "turnover information" in q:
        _set_context(session_id, topic="turnover", intent="DOCUMENT_LOCATION", query=raw_q)
        return {
            "intent": "DOCUMENT_LOCATION",
            "agent": "ProcurementIntentEngine",
            "response": (
                "Turnover information is located in:\n"
                "03_Financial_Turnover_and_Audited_Statements.pdf\n\n"
                "• Page 1: CA Certificate with UDIN 21543892BG1128\n"
                "• Page 2: Audited Balance Sheets\n"
                "• Page 3: Audited P&L Schedule III"
            ),
            "citations": [
                {
                    "source_document": "03_Financial_Turnover_and_Audited_Statements.pdf",
                    "page_number": 1,
                    "clause_reference": "Clause 2(e)",
                    "excerpt": "CA Turnover Certificate certifying annual turnover.",
                }
            ],
            "disclaimer": DISCLAIMER_TEXT,
            "used_fallback": False,
        }

    if "experience evidence" in q or "where is the experience" in q or "experience document" in q:
        _set_context(session_id, topic="experience", intent="DOCUMENT_LOCATION", query=raw_q)
        return {
            "intent": "DOCUMENT_LOCATION",
            "agent": "ProcurementIntentEngine",
            "response": (
                "Past experience evidence is located in:\n"
                "04_Past_Experience_Work_Orders_and_Completion.pdf\n\n"
                "• Page 1: CBDT Work Order & Completion Certificate (₹3.82 Cr)\n"
                "• Page 2: DPIIT Work Order & Completion Certificate (₹2.95 Cr)\n"
                "• Page 3: SAIL Work Order & Interim Letter (₹1.90 Cr)"
            ),
            "citations": [
                {
                    "source_document": "04_Past_Experience_Work_Orders_and_Completion.pdf",
                    "page_number": 1,
                    "clause_reference": "CBDT Order",
                    "excerpt": "Project 1 Order Value ₹3,82,40,000/- with Under Secretary completion certificate.",
                }
            ],
            "disclaimer": DISCLAIMER_TEXT,
            "used_fallback": False,
        }

    if "affidavit" in q and not ("vvip" in q or "annexure 9" in q or "annexure-9" in q):
        _set_context(session_id, topic="affidavit", intent="DOCUMENT_LOCATION", query=raw_q)
        return {
            "intent": "DOCUMENT_LOCATION",
            "agent": "ProcurementIntentEngine",
            "response": (
                "Statutory affidavits are located in:\n"
                "05_Statutory_Affidavits_and_Compliance_Undertakings.pdf\n\n"
                "• Page 1: Annexure-7 (Terms Acceptance) and Annexure-8 (Non-conviction/Anti-corruption)\n"
                "• Page 2: Annexure-10 (Delhi Minimum Wages Undertaking) and ISO 9001:2015\n\n"
                "Note: Mandatory Annexure-9 VVIP Security Affidavit was omitted from this document (FND-01)."
            ),
            "citations": [
                {
                    "source_document": "05_Statutory_Affidavits_and_Compliance_Undertakings.pdf",
                    "page_number": 1,
                    "clause_reference": "Annexures 7 & 8",
                    "excerpt": "Notarized statutory undertakings submitted on non-judicial stamp paper.",
                }
            ],
            "disclaimer": DISCLAIMER_TEXT,
            "used_fallback": False,
        }

    if "which document contains the emd" in q or "where is the emd" in q:
        _set_context(session_id, topic="emd", intent="DOCUMENT_LOCATION", query=raw_q)
        return {
            "intent": "DOCUMENT_LOCATION",
            "agent": "ProcurementIntentEngine",
            "response": (
                "The EMD guarantee is located in:\n"
                "06_EMD_Bank_Guarantee_State_Bank_of_India.pdf\n\n"
                "Page 1: State Bank of India Bank Guarantee No. 0069121BG0004128 for ₹35,73,639."
            ),
            "citations": [
                {
                    "source_document": "06_EMD_Bank_Guarantee_State_Bank_of_India.pdf",
                    "page_number": 1,
                    "clause_reference": "BG No. 0069121BG0004128",
                    "excerpt": "State Bank of India Bank Guarantee for Earnest Money Deposit.",
                }
            ],
            "disclaimer": DISCLAIMER_TEXT,
            "used_fallback": False,
        }

    # ---------------------------------------------------------
    # 11. VERIFICATION STATUS
    # ---------------------------------------------------------
    verif_patterns = [
        "what has been verified", "what is verified", "verification status", "how many checks are verified",
        "are all documents verified", "which checks failed", "how many checks are pending"
    ]
    if any(p in q for p in verif_patterns):
        _set_context(session_id, topic="verification", intent="VERIFICATION_STATUS", query=raw_q)
        return {
            "intent": "VERIFICATION_STATUS",
            "agent": "ProcurementIntentEngine",
            "response": (
                "10 verification checks were conducted on submitted evidence:\n"
                "• 6 Compliant: Incorporation, Delhi Office, EMD Guarantee, Statutory Registrations, Minimum Wages Undertaking, ISO 9001\n"
                "• 2 Partial: Turnover ₹80.15L discrepancy, Experience Project 3 shortfall\n"
                "• 1 Evidence Missing: Annexure-9 VVIP Security Affidavit\n"
                "• 1 Clarification Pending: Typing speed skill test logs\n\n"
                "Source:\n"
                "Document Verification Matrix (10 Checks across 6 Documents)"
            ),
            "citations": [
                {
                    "source_document": "01_Bid_Submission_and_Technical_Bid_Form.pdf",
                    "page_number": 2,
                    "clause_reference": "Verification Checklist",
                    "excerpt": "10 verification checks evaluated across submitted bidder evidence.",
                }
            ],
            "disclaimer": DISCLAIMER_TEXT,
            "used_fallback": False,
        }

    # ---------------------------------------------------------
    # 12. COMPLIANCE & MISSING EVIDENCE
    # ---------------------------------------------------------
    missing_patterns = [
        "what is missing", "what evidence is missing", "which document is missing", "missing documents",
        "what is omitted", "omissions", "why was fnd 01 raised", "why was fnd-01 raised"
    ]
    if any(p in q for p in missing_patterns):
        _set_context(session_id, topic="missing", intent="COMPLIANCE_STATUS", query=raw_q)
        return {
            "intent": "COMPLIANCE_STATUS",
            "agent": "ProcurementIntentEngine",
            "response": (
                "The mandatory document missing from this submission package is the Notarized Annexure-9 VVIP Security Area Affidavit "
                "regarding non-deployment of personnel with criminal antecedents in sensitive/VVIP areas (Tender Clause 2(d)(ii)).\n\n"
                "Document 05 submitted Annexures 7, 8, and 10, but Annexure-9 is completely omitted.\n"
                "Additionally, the final completion certificate for Project 3 (SAIL ₹1.90 Cr) is missing from Document 04.\n\n"
                "Finding: FND-01 [CRITICAL]\n"
                "Status: Pending Officer Determination\n\n"
                "Source:\n"
                "05_Statutory_Affidavits_and_Compliance_Undertakings.pdf\n"
                "Page 1"
            ),
            "citations": [
                {
                    "source_document": "05_Statutory_Affidavits_and_Compliance_Undertakings.pdf",
                    "page_number": 1,
                    "clause_reference": "Clause 2(d)(ii)",
                    "excerpt": "Annexure-9 affidavit omitted from statutory undertakings package.",
                }
            ],
            "disclaimer": DISCLAIMER_TEXT,
            "used_fallback": False,
        }

    compliance_patterns = [
        "is the bidder compliant", "is the application complete", "compliance status", "show me the compliance status",
        "what requirements are compliant", "what requirements are partial", "which requirement needs clarification"
    ]
    if any(p in q for p in compliance_patterns):
        _set_context(session_id, topic="compliance", intent="COMPLIANCE_STATUS", query=raw_q)
        return {
            "intent": "COMPLIANCE_STATUS",
            "agent": "ProcurementIntentEngine",
            "response": (
                "Application APP-001 has evaluated 10 requirements:\n"
                "• 6 Compliant: Incorporation, Delhi Office, EMD Guarantee, Statutory Registrations, Minimum Wages Undertaking, ISO 9001\n"
                "• 2 Partial: Turnover (₹80.15L discrepancy) and Past Experience (Project 3 shortfall)\n"
                "• 1 Evidence Missing: Annexure-9 VVIP Security Affidavit\n"
                "• 1 Clarification Pending: Typing speed skill test logs\n\n"
                "Overall Application Status: REVIEW_REQUIRED (Not fully compliant due to 1 missing mandatory affidavit and 2 partial items)."
            ),
            "citations": [
                {
                    "source_document": "05_Statutory_Affidavits_and_Compliance_Undertakings.pdf",
                    "page_number": 1,
                    "clause_reference": "Clause 2(d)(ii)",
                    "excerpt": "Mandatory Annexure-9 omitted.",
                }
            ],
            "disclaimer": DISCLAIMER_TEXT,
            "used_fallback": False,
        }

    # ---------------------------------------------------------
    # 13. FINDINGS & RISKS
    # ---------------------------------------------------------
    finding_patterns = [
        "what are the findings", "how many findings are there", "are there any critical findings",
        "show me the high risk findings", "what is the biggest issue", "show findings", "findings", "risk findings"
    ]
    if norm_q in ["findings", "show findings"] or any(p in q for p in finding_patterns):
        _set_context(session_id, topic="findings", intent="FINDING_LIST", query=raw_q)
        return {
            "intent": "FINDING_LIST",
            "agent": "ProcurementIntentEngine",
            "response": (
                "There are 5 findings for application APP-001:\n"
                "• FND-01 [CRITICAL]: Omission of Mandatory Annexure-9 VVIP Area Affidavit\n"
                "• FND-02 [HIGH]: Cross-Document Financial Turnover Inconsistency (₹80.15L variance)\n"
                "• FND-03 [MEDIUM]: Experience Project 3 Below Threshold (₹1.90 Cr vs ₹2.85 Cr) & Missing Completion Certificate\n"
                "• FND-04 [LOW]: Unverified Technical Typing Speed Self-Declaration\n"
                "• FND-05 [LOW]: Entity Name Variation Between Incorporation and Tax Filings (Accepted/Overridden)\n\n"
                "Current status: 4 open findings (1 clarification requested, 3 pending officer determination), 1 accepted."
            ),
            "citations": [
                {
                    "source_document": "05_Statutory_Affidavits_and_Compliance_Undertakings.pdf",
                    "page_number": 1,
                    "clause_reference": "Clause 2(d)(ii)",
                    "excerpt": "FND-01: Annexure-9 affidavit omitted from submission package.",
                },
                {
                    "source_document": "03_Financial_Turnover_and_Audited_Statements.pdf",
                    "page_number": 1,
                    "clause_reference": "Clause 2(e)",
                    "excerpt": "FND-02: CA turnover certificate claims ₹6.20 Cr while Audited P&L reports ₹5.40 Cr.",
                },
            ],
            "disclaimer": DISCLAIMER_TEXT,
            "used_fallback": False,
        }

    # Specific finding explanations: FND-03, FND-04, FND-05
    if "fnd-03" in q or "fnd 03" in q or "experience issue" in q or "project 3" in q:
        _set_context(session_id, topic="experience", intent="FINDING_DETAIL", query=raw_q)
        return {
            "intent": "FINDING_DETAIL",
            "agent": "ProcurementIntentEngine",
            "response": (
                "FND-03 was raised because Project 3 (SAIL) has an order value of ₹1.90 Cr, which is ₹95 Lakhs below "
                "the mandatory 40% threshold (₹2.85 Cr), and is accompanied only by an interim performance letter rather "
                "than a formal client completion certificate.\n\n"
                "Severity: MEDIUM\n"
                "Status: Pending Officer Determination\n\n"
                "Source:\n"
                "04_Past_Experience_Work_Orders_and_Completion.pdf\n"
                "Page 3"
            ),
            "citations": [
                {
                    "source_document": "04_Past_Experience_Work_Orders_and_Completion.pdf",
                    "page_number": 3,
                    "clause_reference": "Order SAIL/CO/PERS/2020/12",
                    "excerpt": "Project 3 Order Value ₹1,90,00,000/- (interim letter only; below threshold).",
                }
            ],
            "disclaimer": DISCLAIMER_TEXT,
            "used_fallback": False,
        }

    if "fnd-04" in q or "fnd 04" in q or "typing speed" in q:
        _set_context(session_id, topic="typing_speed", intent="FINDING_DETAIL", query=raw_q)
        return {
            "intent": "FINDING_DETAIL",
            "agent": "ProcurementIntentEngine",
            "response": (
                "FND-04 was raised because Annexure-5 specifies a typing speed of 15,000 key depressions/hour for clerical staff, "
                "but the bidder provided only an internal self-declaration without empirical test logs or third-party skill certificates.\n\n"
                "Severity: LOW\n"
                "Status: Clarification Pending\n\n"
                "Source:\n"
                "05_Statutory_Affidavits_and_Compliance_Undertakings.pdf\n"
                "Page 2, Annexure-5"
            ),
            "citations": [
                {
                    "source_document": "05_Statutory_Affidavits_and_Compliance_Undertakings.pdf",
                    "page_number": 2,
                    "clause_reference": "Annexure-5",
                    "excerpt": "Technical skill self-assertion without empirical typing speed assessment logs.",
                }
            ],
            "disclaimer": DISCLAIMER_TEXT,
            "used_fallback": False,
        }

    # ---------------------------------------------------------
    # 14. PENDING ITEMS
    # ---------------------------------------------------------
    pending_patterns = [
        "what is pending", "what is still pending", "what needs clarification", "pending items",
        "what is waiting", "pending clarifications"
    ]
    if norm_q in ["what is pending", "pending"] or any(p in q for p in pending_patterns):
        _set_context(session_id, topic="pending", intent="PENDING_ITEMS", query=raw_q)
        return {
            "intent": "PENDING_ITEMS",
            "agent": "ProcurementIntentEngine",
            "response": (
                "Current pending items include:\n"
                "• 1 clarification pending (FND-02: 3-day notice for ₹80.15L turnover reconciliation)\n"
                "• 1 critical finding (FND-01: Omitted Annexure-9 VVIP security affidavit)\n"
                "• 1 high finding (FND-02: Turnover discrepancy)\n"
                "• Additional officer review items (FND-03 past experience shortfall, FND-04 typing test logs)\n\n"
                "I can show the specific findings if you want."
            ),
            "citations": [
                {
                    "source_document": "05_Statutory_Affidavits_and_Compliance_Undertakings.pdf",
                    "page_number": 1,
                    "clause_reference": "Clause 2(d)(ii)",
                    "excerpt": "FND-01: Critical affidavit omission pending officer ruling.",
                },
                {
                    "source_document": "03_Financial_Turnover_and_Audited_Statements.pdf",
                    "page_number": 1,
                    "clause_reference": "Clause 2(e)",
                    "excerpt": "FND-02: Turnover reconciliation pending clarification.",
                },
            ],
            "disclaimer": DISCLAIMER_TEXT,
            "used_fallback": False,
        }

    # ---------------------------------------------------------
    # 15. OFFICER REVIEW QUESTIONS
    # ---------------------------------------------------------
    officer_patterns = [
        "what should i review", "what requires my attention", "what is waiting for officer review",
        "what requires officer review", "what needs review", "which issue needs clarification",
        "what evidence should i check", "officer review"
    ]
    if norm_q in ["what needs review", "officer review"] or any(p in q for p in officer_patterns):
        _set_context(session_id, topic="officer_review", intent="OFFICER_REVIEW", query=raw_q)
        return {
            "intent": "OFFICER_REVIEW",
            "agent": "ProcurementIntentEngine",
            "response": (
                "Officer review and determination is required on:\n"
                "1. FND-01 [CRITICAL]: Rule whether omission of Annexure-9 VVIP security affidavit warrants disqualification or clarification notice.\n"
                "2. FND-02 [HIGH]: Review auditor reconciliation for the ₹80.15 Lakhs variance between CA certificate (₹6.20 Cr) and P&L (₹5.40 Cr).\n"
                "3. FND-03 [MEDIUM]: Evaluate whether past experience qualifies under the 2-order threshold (₹3.57 Cr) or seek missing SAIL completion certificate.\n"
                "4. FND-04 [LOW]: Decide whether pre-deployment typing speed proficiency tests should be stipulated.\n\n"
                "Final procurement decisions remain with the designated Procurement Officer."
            ),
            "citations": [
                {
                    "source_document": "05_Statutory_Affidavits_and_Compliance_Undertakings.pdf",
                    "page_number": 1,
                    "clause_reference": "Clause 2(d)(ii)",
                    "excerpt": "FND-01: Critical affidavit omission awaiting committee ruling.",
                },
                {
                    "source_document": "03_Financial_Turnover_and_Audited_Statements.pdf",
                    "page_number": 1,
                    "clause_reference": "Clause 2(e)",
                    "excerpt": "FND-02: Financial variance awaiting officer reconciliation review.",
                },
            ],
            "disclaimer": DISCLAIMER_TEXT,
            "used_fallback": False,
        }

    # If no deterministic canonical match was found
    return None

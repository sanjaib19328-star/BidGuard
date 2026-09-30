# BidGuard Synthetic Bidder Demo Application

## Tender Used

- **Tender Title**: Hiring of Manpower Services (Un-skilled, Skilled and Clerical/Non-Technical Supervisory staff)
- **Issuing Authority**: Office of the Comptroller & Auditor General (CAG) of India, New Delhi
- **Ministry**: Comptroller And Auditor General Of India
- **GeM Bid Number**: `GEM/2021/B/1128240`
- **Internal Bid Document No.**: `46/GS/114-2021`
- **Estimated Bid Value**: ₹7,14,72,780 (₹7.14 Cr)
- **EMD Required**: ₹35,73,639 (5.00%, State Bank of India)
- **Turnover Required**: ₹357.0 Lakhs (3-Year Average from Manpower Services)
- **Source File**: `backend/data/reference_tenders/01_CAG_Manpower_Hiring_BidDoc_GEM_2021_B_1128240.pdf`

## Synthetic Bidder Identity

- **Legal Entity Name**: `Aravind Integrated Solutions Private Limited`
- **Trade Name / Variation**: `Aravind Integrated Solutions Pvt. Ltd.`
- **Constitution**: Private Limited Company registered under Companies Act, 2013 on 14/06/2016
- **Synthetic CIN**: `U74999DL2016PTC301429`
- **Synthetic PAN**: `AAACA9182K`
- **Synthetic GSTIN**: `07AAACA9182K1Z5` (Delhi State Code: 07)
- **Synthetic EPF Code**: `DLCPM0094821000` (Delhi Central)
- **Synthetic ESIC Code**: `11000847290001001` (Delhi Sub-Region)
- **Delhi Labour License**: `CLA/DLC/ND/2018/04291`
- **Synthetic Notice**:
  > **[DEMO / SYNTHETIC DATA — FOR TESTING AND EVALUATION ONLY — NOT A REAL GOVERNMENT RECORD]**

## Submitted Bidder Application Documents

| File Name | Document Type | Pages | Key Evidence Provided |
| :--- | :--- | :---: | :--- |
| `01_Bid_Submission_and_Technical_Bid_Form.pdf` | Bid Submission & Technical Bid | 2 | Annexure-1 Letter of Bid, 90-day validity commitment, and Annexure-6 Technical Form with full bidder particulars and checklist. |
| `02_Company_Incorporation_and_Statutory_Registrations.pdf` | Corporate & Statutory Dossier | 2 | RoC Incorporation Certificate, Delhi registered office lease proof, PAN Card, GSTIN Registration (REG-06), EPF, ESIC, and Delhi Labour License. |
| `03_Financial_Turnover_and_Audited_Statements.pdf` | Financial Dossier | 2 | CA Turnover Certificate with UDIN: 21094812AAAAAK4918 certifying ₹5.06 Cr average + Audited Balance Sheet and P&L statements. |
| `04_Past_Experience_Work_Orders_and_Completion.pdf` | Experience Evidence | 2 | CBDT Project 1 (₹3.82 Cr + Completion Cert), DPIIT Project 2 (₹2.95 Cr + Completion Cert), and SAIL Project 3 (₹1.90 Cr + Interim letter). |
| `05_Statutory_Affidavits_and_Compliance_Undertakings.pdf` | Affidavits & Quality Dossier | 2 | Annexure-7 (Terms Acceptance), Annexure-8 (Non-conviction/No relatives), Annexure-10 (Minimum Wages & Labour Laws), ISO 9001:2015 Cert, and typing speed statement. |
| `06_EMD_Bank_Guarantee_State_Bank_of_India.pdf` | Bid Security (EMD) | 1 | Original SBI Bank Guarantee No. 0069121BG0004128 for ₹35,73,639/- valid through 15.08.2021 in favour of PAO CAG. |

## Controlled Verification Scenarios

| Scenario Type | Implementation in Demo Application | Expected BidGuard AI Evaluation Result |
| :--- | :--- | :--- |
| **A. Compliant Evidence** | Valid Certificate of Incorporation, PAN, EPF, ESIC, Delhi Labour License, Annexure-1, 7, 8, 10, ISO 9001:2015, and exact SBI EMD Bank Guarantee. | `COMPLIANT` with evidence citations and page references. |
| **B. Name Variation** | Incorporation has full name `Aravind Integrated Solutions Private Limited`; GST and CA certificate display `Aravind Integrated Solutions Pvt. Ltd.` | `MATCH_WITH_VARIATION` / fuzzy normalization; no false failure. |
| **C. Financial Discrepancy** | CA Certificate reports FY 2019-20 turnover as **₹6,20,40,000/-**, whereas Audited P&L schedule reports Revenue from Operations as **₹5,40,25,000/-** (discrepancy of ₹80.15 Lakhs). | `DISCREPANCY_FLAGGED` / `OFFICER_REVIEW_REQUIRED`. |
| **D. Experience Partiality** | Tender requires 1 order of 80% (₹5.71 Cr) OR 2 orders of 50% (₹3.57 Cr) OR 3 orders of 40% (₹2.85 Cr). Project 3 (SAIL) is only ₹1.90 Cr and lacks a formal completion certificate. | `PARTIAL` / `DEFICIENCY_FLAGGED`. |
| **E. Missing Document** | Mandatory Annexure-9 Notarized Affidavit for VVIP/Sensitive Area Experience (Clause 2(d)(ii)) is intentionally omitted from the submission pack. | `EVIDENCE_MISSING` / `MANDATORY_CRITERION_UNFULFILLED`. |
| **F. Technical Ambiguity** | Annexure-5 specifies 15,000 key depressions/hour for clerical staff; bidder provides an in-house self-assertion without third-party skill test certificates or speed logs. | `CLARIFICATION_PENDING`. |
| **G. External Verification Limitation** | Synthetic identifiers (PAN, GSTIN, Udyam) reflect realistic format but are not claimed as verified against live government APIs when connectors are unconfigured. | `NOT_CONFIGURED` / `MANUAL_VERIFICATION_ADVISED`. |

## End-to-End Demo Flow

```text
Tender Document (GEM/2021/B/1128240)
       ↓
Requirement Extraction (Clauses 2a-g, 3, 4, ATC)
       ↓
Bidder Application Upload (6 Multi-Page PDFs)
       ↓
Document Classification (LayoutLMv3 + TrOCR)
       ↓
Evidence Extraction & Chunking (BGE-Small 384-dim Embeddings)
       ↓
RAG Retrieval & Neural Reranking (ms-marco-MiniLM Cross-Encoder)
       ↓
Requirement / Evidence Cross-Examination (Qwen2.5-1.5B Non-Autonomous Prompting)
       ↓
Compliance Matrix & Discrepancy Detection (Flagging Financial Discrepancy & Missing Annexure-9)
       ↓
Officer Review Dashboard (Human Authority Decision Support)
```

## AI Components Used

All processing utilizes the **EXISTING** BidGuard AI implementation:
- `DocumentAIProvider`: LayoutLMv3 Base visual structure understanding
- `OCRProvider`: TrOCR Small Printed optical character recognition
- `EmbeddingProvider`: BAAI/bge-small-en-v1.5 dense vector embeddings (384-dim)
- `RerankerProvider`: cross-encoder/ms-marco-MiniLM-L-6-v2 cross-attention neural reranking
- `LLMProvider`: Qwen/Qwen2.5-1.5B-Instruct grounded analytical synthesis with non-autonomous guardrails
- `DocumentAgent`: Clause parsing and table isolation
- `RAGAgent`: Dense retrieval, reranking, and citation generation
- `AnalysisAgent`: Cross-examination, discrepancy flagging, and statutory auditing
- `AgentRouter`: Multi-agent intent classification and orchestration
- `AIAssistantService`: High-level chat, document analysis, and status checks

## Strict Non-Autonomous Procurement Safeguard

In accordance with public procurement laws (GFR 2017, Public Procurement Act) and BidGuard core architecture:
- BidGuard AI **NEVER** declares a winning bidder, recommends contract awards, or eliminates bidders autonomously.
- All evaluation outputs provide verifiable evidence citations (source document, page number, clause excerpt) and require final confirmation by authorized procurement officers.

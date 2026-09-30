import {
  Tender,
  BidderApplicationPackage,
  DocumentVerificationCheck,
  OfficerFinding,
  ComplianceMatrixItem,
  AuditLogItem,
} from '../types';

export const DEMO_CAG_TENDER: Tender = {
  id: 'GEM/2021/B/1128240',
  tender_number: 'GEM/2021/B/1128240',
  title: 'Hiring of Manpower Services — Outsource Agency for Deployment of Office and Technical Staff',
  issuing_authority: 'Office of the Comptroller & Auditor General (CAG) of India, New Delhi',
  ministry: 'Comptroller And Auditor General Of India',
  estimated_value: 71472780,
  estimated_value_display: '₹7,14,72,780 (₹7.14 Cr)',
  emd_amount: 3573639,
  turnover_requirement_lakhs: 357.36,
  past_experience_years: 3,
  mse_exemption_permitted: false,
  startup_exemption_permitted: false,
  status: 'UNDER_REVIEW',
  created_at: '2021-03-15T10:00:00Z',
  total_clauses: 24,
  total_requirements: 10,
};

export const DEMO_BIDDER_APPLICATION: BidderApplicationPackage = {
  id: 'APP-001',
  bidder_name: 'Aravind Integrated Solutions Private Limited',
  trade_name: 'Aravind Integrated Solutions Pvt. Ltd.',
  is_synthetic: true,
  tender_id: 'GEM/2021/B/1128240',
  submission_date: '2021-03-24T14:30:00Z',
  cin: 'U74999DL2016PTC301429',
  pan: 'AAACA9182K',
  gstin: '07AAACA9182K1Z5',
  udyam_number: 'UDYAM-DL-08-0042819',
  registered_address: 'Suite 402, 4th Floor, Pragati Deep Building, Laxmi Nagar, New Delhi - 110092',
  authorized_signatory: 'Rajesh K. Varma (Managing Director, DIN: 07412895)',
  total_documents: 6,
  total_pages: 16,
  requirements_mapped: 10,
  verified_count: 6,
  issues_count: 4,
  overall_status: 'REVIEW_REQUIRED',
  documents: [
    {
      id: 'doc-01',
      file_name: '01_Bid_Submission_and_Technical_Bid_Form.pdf',
      title: 'Bid Submission & Technical Bid Form',
      document_type: 'BIDDER_SUBMISSION',
      pages: 3,
      processing_status: 'INDEXED',
      extraction_status: 'COMPLETE',
      verification_status: 'COMPLIANT',
      evidence_availability: 'AVAILABLE',
      description: 'Annexure-1 Letter of Bid agreeing to 90 days validity & Annexure-6 Technical Bid Form with corporate profile and document submission checklist.',
      key_clauses: ['Annexure-1 Formal Letter of Bid', 'Annexure-6 Technical Bid Form', 'Authorized Signatory Board Resolution'],
      extracted_items: [
        { label: 'Bidder Legal Name', value: 'Aravind Integrated Solutions Private Limited', page: 1 },
        { label: 'Authorized Signatory', value: 'Rajesh K. Varma, Managing Director', page: 1 },
        { label: 'Bid Validity Commitment', value: '90 Days unconditional validity from bid close', page: 1 },
        { label: 'Entity Status', value: 'Private Limited Company (Companies Act 2013)', page: 2 },
      ],
      content_preview: `[DEMO / SYNTHETIC DATA — FOR TESTING AND EVALUATION ONLY — NOT A REAL GOVERNMENT RECORD]
LETTER OF BID & TECHNICAL BID FORM
Tender Reference: GEM/2021/B/1128240
To: The Director (Personnel), Office of the Comptroller and Auditor General of India, New Delhi

1. Having examined the Bid Documents including General Terms and Conditions and Special Terms, we, M/s Aravind Integrated Solutions Private Limited, offer to execute the Manpower Deployment Services in full conformity with specifications.
2. We undertake that our bid shall remain valid for a period of 90 days from bid closing date.
3. Enclosed herewith are all statutory documents, audited financial accounts, past performance credentials, and Earnest Money Deposit bank guarantee.`,
    },
    {
      id: 'doc-02',
      file_name: '02_Company_Incorporation_and_Statutory_Registrations.pdf',
      title: 'Company Incorporation & Statutory Registrations',
      document_type: 'STATUTORY_CERTIFICATE',
      pages: 3,
      processing_status: 'INDEXED',
      extraction_status: 'COMPLETE',
      verification_status: 'COMPLIANT',
      evidence_availability: 'AVAILABLE',
      description: 'RoC Certificate of Incorporation (MCA), Delhi NCT Lease Deed, PAN Card, GSTIN REG-06 Certificate, EPF Code, ESIC Registration, and Delhi Labour License.',
      key_clauses: ['Clause 2(a) Legal Entity', 'Clause 2(g) Delhi Office', 'Clause 2(b) Tax & Labour Registrations'],
      extracted_items: [
        { label: 'CIN', value: 'U74999DL2016PTC301429 (Inc. 14/06/2016)', page: 1 },
        { label: 'Delhi Office Proof', value: 'Lease Deed Suite 402 Pragati Deep, Laxmi Nagar, New Delhi', page: 1 },
        { label: 'PAN', value: 'AAACA9182K', page: 2 },
        { label: 'GSTIN', value: '07AAACA9182K1Z5 (Trade: Aravind Integrated Solutions Pvt. Ltd.)', page: 2, discrepancy_note: 'Minor trade name variation (Pvt. Ltd. vs Private Limited)' },
        { label: 'EPF Registration', value: 'DLCPM0094821000', page: 2 },
        { label: 'ESIC Code', value: '11000847290001001', page: 2 },
        { label: 'Labour License', value: 'CLA/DLC/ND/2018/04291 (Central/Delhi NCT)', page: 3 },
      ],
      content_preview: `[DEMO / SYNTHETIC DATA — FOR TESTING AND EVALUATION ONLY — NOT A REAL GOVERNMENT RECORD]
MINISTRY OF CORPORATE AFFAIRS — ROC DELHI
CERTIFICATE OF INCORPORATION: Corporate Identity Number U74999DL2016PTC301429
I hereby certify that ARAVIND INTEGRATED SOLUTIONS PRIVATE LIMITED is incorporated on 14 June 2016 under Companies Act, 2013.

DELHI/NCT OFFICE VERIFICATION:
Registered Office: Suite 402, Pragati Deep Building, Laxmi Nagar, New Delhi - 110092.
Electricity Utility Account: BSES Yamuna CA No. 102948190 confirming commercial occupancy.

STATUTORY REGISTRATION NUMBERS:
PAN: AAACA9182K | GSTIN: 07AAACA9182K1Z5 | EPF: DLCPM0094821000 | ESIC: 11000847290001001`,
    },
    {
      id: 'doc-03',
      file_name: '03_Financial_Turnover_and_Audited_Statements.pdf',
      title: 'Financial Turnover Certificate & Audited Statements',
      document_type: 'FINANCIAL_STATEMENT',
      pages: 4,
      processing_status: 'INDEXED',
      extraction_status: 'COMPLETE',
      verification_status: 'PARTIAL',
      evidence_availability: 'AVAILABLE',
      description: 'CA Turnover Certificate with UDIN certifying 3-year average of ₹5.06 Cr + Audited Balance Sheets and P&L Statements for FY 2017-18, 2018-19, and 2019-20.',
      key_clauses: ['Clause 2(e) Minimum Turnover ₹3.57 Cr', 'GFR Rule 144 Financial Integrity'],
      extracted_items: [
        { label: 'CA Certified FY 17-18 Turnover', value: '₹4,12,50,000 (₹4.12 Cr)', page: 1 },
        { label: 'CA Certified FY 18-19 Turnover', value: '₹4,85,20,000 (₹4.85 Cr)', page: 1 },
        { label: 'CA Certified FY 19-20 Turnover', value: '₹6,20,50,000 (₹6.20 Cr)', page: 1, cross_reference: 'P&L reports ₹5.40 Cr', discrepancy_note: 'Variance of ₹80.15 Lakhs between CA Certificate and Audited P&L' },
        { label: 'CA Certified 3-Year Average', value: '₹5,06,06,666 (₹5.06 Cr)', page: 1 },
        { label: 'CA UDIN Number', value: '21543892BG1128 (Sharma & Co., FRN 014829N)', page: 1 },
        { label: 'Audited P&L FY 19-20 Revenue', value: '₹5,40,35,000 (₹5.40 Cr)', page: 3, discrepancy_note: 'Internal discrepancy flagged for officer review' },
      ],
      content_preview: `[DEMO / SYNTHETIC DATA — FOR TESTING AND EVALUATION ONLY — NOT A REAL GOVERNMENT RECORD]
CHARTERED ACCOUNTANTS' TURNOVER CERTIFICATE
To whomsoever it may concern:
UDIN: 21543892BG1128 | CA Membership No: 054389
This is to certify that M/s Aravind Integrated Solutions Private Limited has achieved annual turnover in manpower services:
- FY 2017-18: Rs. 4,12,50,000/-
- FY 2018-19: Rs. 4,85,20,000/-
- FY 2019-20: Rs. 6,20,50,000/-
Average Annual Turnover: Rs. 5,06,06,666/- (Rupees Five Crore Six Lakhs...)

EXTRACT FROM AUDITED P&L (SCHEDULE III) — FY 2019-20:
Revenue from Operations: Rs. 5,40,35,000/-
[FLAGGED: Discrepancy of Rs. 80.15 Lakhs between CA Certificate (Rs. 6.20 Cr) and Audited Accounts (Rs. 5.40 Cr)]`,
    },
    {
      id: 'doc-04',
      file_name: '04_Past_Experience_Work_Orders_and_Completion.pdf',
      title: 'Past Experience Work Orders & Completion Certificates',
      document_type: 'EXPERIENCE_CERTIFICATE',
      pages: 3,
      processing_status: 'INDEXED',
      extraction_status: 'COMPLETE',
      verification_status: 'PARTIAL',
      evidence_availability: 'PARTIAL',
      description: 'Work orders and client performance certificates for CBDT (₹3.82 Cr), DPIIT (₹2.95 Cr), and Steel Authority of India Ltd (₹1.90 Cr).',
      key_clauses: ['Clause 4 Experience Criteria', 'Completion Certificate Requirement'],
      extracted_items: [
        { label: 'Project 1 Client', value: 'Central Board of Direct Taxes (CBDT)', page: 1 },
        { label: 'Project 1 Order Value', value: '₹3,82,40,000 (₹3.82 Cr) — Satisfactory Completion Certificate attached', page: 1 },
        { label: 'Project 2 Client', value: 'Dept for Promotion of Industry and Internal Trade (DPIIT)', page: 2 },
        { label: 'Project 2 Order Value', value: '₹2,95,10,000 (₹2.95 Cr) — Satisfactory Completion Certificate attached', page: 2 },
        { label: 'Project 3 Client', value: 'Steel Authority of India Limited (SAIL)', page: 3 },
        { label: 'Project 3 Order Value', value: '₹1,90,00,000 (₹1.90 Cr)', page: 3, cross_reference: 'Threshold is ₹2.14 Cr', discrepancy_note: 'Value below 30% threshold (₹2.14 Cr) and accompanied only by interim performance letter' },
      ],
      content_preview: `[DEMO / SYNTHETIC DATA — FOR TESTING AND EVALUATION ONLY — NOT A REAL GOVERNMENT RECORD]
PAST EXPERIENCE SUMMARY & PERFORMANCE CERTIFICATES:
1. Client: Central Board of Direct Taxes (CBDT), New Delhi
   Order No: CBDT/HQ/ADMIN/2018/104 | Value: Rs. 3,82,40,000/- | Status: Completed (31-03-2020)
   Evidence: Formal client completion certificate signed by Under Secretary.

2. Client: DPIIT, Ministry of Commerce & Industry
   Order No: DPIIT/ESTT/2019/55 | Value: Rs. 2,95,10,000/- | Status: Completed (30-09-2020)
   Evidence: Satisfactory performance completion certificate attached.

3. Client: Steel Authority of India Limited (SAIL)
   Order No: SAIL/CO/PERS/2020/12 | Value: Rs. 1,90,00,000/- | Status: Ongoing / Interim
   [FLAGGED: Value Rs. 1.90 Cr is below minimum threshold Rs. 2.14 Cr; final completion certificate missing]`,
    },
    {
      id: 'doc-05',
      file_name: '05_Statutory_Affidavits_and_Compliance_Undertakings.pdf',
      title: 'Statutory Affidavits & Compliance Undertakings',
      document_type: 'AFFIDAVIT_UNDERTAKING',
      pages: 2,
      processing_status: 'INDEXED',
      extraction_status: 'PARTIAL',
      verification_status: 'EVIDENCE_MISSING',
      evidence_availability: 'PARTIAL',
      description: 'Annexure-7 (Terms acceptance), Annexure-8 (Non-conviction/No relatives), Annexure-10 (Minimum wages & labour compliance), ISO 9001:2015, and typing speed statement. Annexure-9 omitted.',
      key_clauses: ['Annexure-7 Bid Terms', 'Annexure-8 Non-Conviction', 'Annexure-9 VVIP Affidavit (OMITTED)', 'Annexure-10 Minimum Wages', 'Annexure-5 Typing Speed'],
      extracted_items: [
        { label: 'Annexure-7 Acceptance', value: 'Executed on Stamp Paper IN-DL8492019283710A', page: 1 },
        { label: 'Annexure-8 Anti-Corruption', value: 'Notarized affidavit confirming zero convictions and no relatives at CAG', page: 1 },
        { label: 'Annexure-9 VVIP Affidavit', value: 'NOT SUBMITTED / OMITTED', page: 1, discrepancy_note: 'Mandatory affidavit regarding non-deployment of personnel with criminal records in VVIP areas omitted' },
        { label: 'Annexure-10 Minimum Wages', value: 'Unconditional undertaking to abide by Delhi NCT minimum wage revisions', page: 2 },
        { label: 'ISO 9001:2015 Certification', value: 'Cert No: QMS-2019-DEL-84920, valid through 17.07.2022', page: 2 },
        { label: 'Typing Speed Compliance', value: 'Self-declaration asserting 15,000 key depressions/hour without third-party skill test log', page: 2, discrepancy_note: 'Technical ambiguity: No empirical test log attached' },
      ],
      content_preview: `[DEMO / SYNTHETIC DATA — FOR TESTING AND EVALUATION ONLY — NOT A REAL GOVERNMENT RECORD]
STATUTORY AFFIDAVITS & COMPLIANCE UNDERTAKINGS:
- Annexure-7: Acceptance of all terms & conditions without deviations.
- Annexure-8: Affidavit confirming non-conviction under Prevention of Corruption Act and zero relatives in CAG.
- Annexure-10: Statutory undertaking for payment of minimum wages notified by Govt of NCT of Delhi, and regular EPF/ESIC deposits by 15th of each month.
- Quality Management: ISO 9001:2015 accredited certification valid through 17-07-2022.
- Technical Skill Assertion: Company asserts deployment of skilled clerical staff capable of 15,000 key depressions/hour.

[OMISSION: Annexure-9 Affidavit regarding non-deployment of personnel with criminal antecedents in VVIP security areas was NOT uploaded]`,
    },
    {
      id: 'doc-06',
      file_name: '06_EMD_Bank_Guarantee_State_Bank_of_India.pdf',
      title: 'Earnest Money Deposit (EMD) Bank Guarantee',
      document_type: 'EMD_GUARANTEE',
      pages: 1,
      processing_status: 'INDEXED',
      extraction_status: 'COMPLETE',
      verification_status: 'COMPLIANT',
      evidence_availability: 'AVAILABLE',
      description: 'Original irrevocable Bank Guarantee from State Bank of India CAG Branch for ₹35,73,639/- valid for 180 days in favour of Pay and Accounts Officer, CAG.',
      key_clauses: ['Bid Security Clause 3', 'Bank Guarantee Validity Period'],
      extracted_items: [
        { label: 'Issuing Bank', value: 'State Bank of India, CAG Branch, New Delhi (IFSC: SBIN0000691)', page: 1 },
        { label: 'Guarantee Number', value: '0069121BG0004128', page: 1 },
        { label: 'Guarantee Amount', value: '₹35,73,639/- (Exact 5% of ₹7,14,72,780)', page: 1 },
        { label: 'Beneficiary', value: 'Pay and Accounts Officer, Office of the CAG of India', page: 1 },
        { label: 'Validity Period', value: 'Valid up to 15.08.2021 with 6 months claim period', page: 1 },
      ],
      content_preview: `[DEMO / SYNTHETIC DATA — FOR TESTING AND EVALUATION ONLY — NOT A REAL GOVERNMENT RECORD]
STATE BANK OF INDIA — CAG BRANCH, NEW DELHI
BANK GUARANTEE FOR EARNEST MONEY DEPOSIT (BG NO: 0069121BG0004128)
Guarantee Sum: Rs. 35,73,639/- (Rupees Thirty Five Lakhs Seventy Three Thousand Six Hundred and Thirty Nine Only)
Beneficiary: Pay and Accounts Officer, Office of the Comptroller & Auditor General of India, New Delhi.

1. In consideration of M/s Aravind Integrated Solutions Private Limited submitting its bid for Tender No. GEM/2021/B/1128240, we, State Bank of India, hereby irrevocably and unconditionally guarantee payment of Rs. 35,73,639/- upon first written demand.
2. This Guarantee shall remain in force up to 15th August 2021 and any demand in respect thereof should reach the Bank within the claim period.`,
    },
  ],
};

export const DEMO_VERIFICATION_CHECKS: DocumentVerificationCheck[] = [
  {
    id: 'CHK-01',
    category: 'Identity',
    requirement_title: 'Legal Entity Incorporation',
    requirement_clause: 'Annexure-2, Clause 2(a) (Page 3)',
    requirement_text: 'The Bidder shall be a legally registered Limited or Private Limited Company under Companies Act 2013 or LLP under LLP Act 2008. JV/Consortium prohibited.',
    submitted_evidence: 'RoC Certificate of Incorporation No. U74999DL2016PTC301429 issued by Registrar of Companies, Delhi.',
    extraction_details: 'Entity Name: Aravind Integrated Solutions Private Limited | Inc. Date: 14/06/2016 | Standalone Pvt Ltd entity.',
    verification_method: 'MCA Incorporation Registry Structure Verification',
    result: 'COMPLIANT',
    confidence: 'HIGH',
    source_document: '02_Company_Incorporation_and_Statutory_Registrations.pdf',
    source_page: 1,
  },
  {
    id: 'CHK-02',
    category: 'Identity',
    requirement_title: 'Registered Office in Delhi / NCT',
    requirement_clause: 'Annexure-2, Clause 2(g) (Page 4)',
    requirement_text: 'The bidder must maintain an operational registered office within Delhi / NCT of Delhi region with utility/lease documentary evidence.',
    submitted_evidence: 'Registered Commercial Lease Deed & BSES Yamuna Electricity Bill for Suite 402, Pragati Deep Building, Laxmi Nagar, New Delhi - 110092.',
    extraction_details: 'Address in NCT of Delhi verified through municipal district centre registration and power utility CA No. 102948190.',
    verification_method: 'Documentary verification of Delhi municipal jurisdiction',
    result: 'COMPLIANT',
    confidence: 'HIGH',
    source_document: '02_Company_Incorporation_and_Statutory_Registrations.pdf',
    source_page: 2,
  },
  {
    id: 'CHK-03',
    category: 'Financial',
    requirement_title: 'Average Annual Turnover (Min ₹357.36 Lakhs)',
    requirement_clause: 'Bid Data Sheet & Clause 2(e) (Page 1 & 4)',
    requirement_text: 'Minimum Average Annual Financial Turnover of Rs. 357.0 Lakhs in manpower services over FY 2017-18, 2018-19, and 2019-20, certified by CA with UDIN.',
    submitted_evidence: 'CA Turnover Certificate (UDIN: 21543892BG1128) and Audited Profit & Loss Schedules.',
    extraction_details: 'CA Certificate claims FY 19-20 turnover = ₹6.20 Cr (Avg ₹5.06 Cr). Audited P&L Schedule III reports FY 19-20 revenue = ₹5.40 Cr.',
    cross_document_evidence: 'Audited P&L: ₹5.40 Cr vs CA Certificate: ₹6.20 Cr',
    variance: 'Discrepancy of ₹80.15 Lakhs between certified turnover and audited revenue',
    verification_method: 'Cross-document reconciliation of CA Certificate vs Audited P&L',
    result: 'PARTIAL',
    confidence: 'HIGH',
    source_document: '03_Financial_Turnover_and_Audited_Statements.pdf',
    source_page: 1,
    finding_id: 'FND-02',
    finding_title: 'Cross-Document Financial Turnover Inconsistency',
  },
  {
    id: 'CHK-04',
    category: 'EMD',
    requirement_title: 'Earnest Money Deposit (₹35,73,639/- BG)',
    requirement_clause: 'Bid Details Clause 3 & Annexure-13 (Page 1 & 4)',
    requirement_text: 'EMD of ₹35,73,639/- (5% of ₹7.14 Cr) via unconditional Bank Guarantee from a scheduled commercial bank valid for 120 days.',
    submitted_evidence: 'Original State Bank of India BG No. 0069121BG0004128 for ₹35,73,639/- valid through 15.08.2021.',
    extraction_details: 'Amount matches exact 5% threshold; issuing branch SBI CAG Branch; validity 180 days exceeds 120 days requirement.',
    verification_method: 'Bank Guarantee amount, advisory bank, and validity term verification',
    result: 'COMPLIANT',
    confidence: 'HIGH',
    source_document: '06_EMD_Bank_Guarantee_State_Bank_of_India.pdf',
    source_page: 1,
  },
  {
    id: 'CHK-05',
    category: 'Experience',
    requirement_title: 'Past Similar Works Experience',
    requirement_clause: 'Bid Data Sheet Page 2, Clause 4',
    requirement_text: 'Executed at least 1 order of 80% (₹5.71 Cr) OR 2 orders of 50% (₹3.57 Cr) OR 3 orders of 40% (₹2.85 Cr) with client completion certificates.',
    submitted_evidence: 'Project 1: CBDT ₹3.82 Cr (Completed). Project 2: DPIIT ₹2.95 Cr (Completed). Project 3: SAIL ₹1.90 Cr (Interim letter only).',
    extraction_details: 'Shortfall on Project 3: ₹1.90 Cr is below the required 40% threshold (₹2.85 Cr) and lacks a formal final completion certificate.',
    cross_document_evidence: 'Only 1 project exceeds ₹3.57 Cr; 3rd project is ₹1.90 Cr without completion certificate',
    variance: 'Order shortfall of ₹95 Lakhs on Project 3 and missing completion certificate',
    verification_method: 'Numerical threshold verification and completion certificate audit',
    result: 'PARTIAL',
    confidence: 'HIGH',
    source_document: '04_Past_Experience_Work_Orders_and_Completion.pdf',
    source_page: 3,
    finding_id: 'FND-03',
    finding_title: 'Experience Project 3 Below Threshold & Missing Completion Certificate',
  },
  {
    id: 'CHK-06',
    category: 'Declarations',
    requirement_title: 'Annexure-9 VVIP Security Clearance Affidavit',
    requirement_clause: 'Annexure-2, Clause 2(d)(ii) (Page 3 & 14)',
    requirement_text: 'Mandatory notarized affidavit on non-judicial stamp paper confirming non-deployment of personnel with criminal antecedents in VVIP/sensitive areas.',
    submitted_evidence: 'Informal mention in Bid Form; mandatory notarized Annexure-9 affidavit is missing from the package.',
    extraction_details: 'Document 05 contains Annexures 7, 8, 10 but completely omits Annexure-9.',
    verification_method: 'Mandatory checklist document presence audit',
    result: 'EVIDENCE_MISSING',
    confidence: 'HIGH',
    source_document: '05_Statutory_Affidavits_and_Compliance_Undertakings.pdf',
    source_page: 1,
    finding_id: 'FND-01',
    finding_title: 'Omission of Mandatory Annexure-9 VVIP Area Affidavit',
  },
  {
    id: 'CHK-07',
    category: 'Statutory',
    requirement_title: 'Statutory Registrations (PAN, GST, EPF, ESIC, Labour)',
    requirement_clause: 'Annexure-2, Clause 2(b) (Page 3 & 4)',
    requirement_text: 'Mandatory active registration under Income Tax (PAN), GST, EPF, ESIC, and Delhi Labour License.',
    submitted_evidence: 'PAN: AAACA9182K | GST: 07AAACA9182K1Z5 | EPF: DLCPM0094821000 | ESIC: 11000847290001001 | Labour: CLA/DLC/ND/2018/04291.',
    extraction_details: 'All 5 certificates present and structurally valid. Name variation noted on GST (Pvt. Ltd. vs Private Limited).',
    cross_document_evidence: 'Trade name on GST certificate uses abbreviation "Pvt. Ltd."',
    variance: 'Name normalization variation: Acceptable abbreviation',
    verification_method: 'Statutory code syntax and documentary verification',
    result: 'COMPLIANT',
    confidence: 'HIGH',
    source_document: '02_Company_Incorporation_and_Statutory_Registrations.pdf',
    source_page: 2,
    finding_id: 'FND-05',
    finding_title: 'Entity Name Variation Between Incorporation and Tax Filings',
  },
  {
    id: 'CHK-08',
    category: 'Declarations',
    requirement_title: 'Delhi NCT Minimum Wages Undertaking (Annexure-10)',
    requirement_clause: 'Annexure-2, Clause 2(f) & Annexure-10 (Page 4 & 15)',
    requirement_text: 'Notarized affidavit on ₹10 stamp paper committing to NCT of Delhi minimum wages and prompt EPF/ESIC statutory deposits.',
    submitted_evidence: 'Notarized Annexure-10 affidavit on Stamp Paper IN-DL91820491829042U signed by Managing Director.',
    extraction_details: 'Unconditional acceptance of Delhi Government wage notifications and penalty clauses for delayed salary disbursement.',
    verification_method: 'Legal undertaking text and notary seal verification',
    result: 'COMPLIANT',
    confidence: 'HIGH',
    source_document: '05_Statutory_Affidavits_and_Compliance_Undertakings.pdf',
    source_page: 2,
  },
  {
    id: 'CHK-09',
    category: 'Technical',
    requirement_title: 'ISO 9001:2015 Quality Management Certification',
    requirement_clause: 'Additional Terms & Conditions (ATC) Clause 5 (Page 2)',
    requirement_text: 'Bidder must possess valid ISO 9001 certification for manpower supply and facility management.',
    submitted_evidence: 'Certificate QMS-2019-DEL-84920 issued by accredited certification registrar.',
    extraction_details: 'Valid till 17-07-2022; scope covers "Provision of Technical, Administrative, and Facility Staffing Solutions".',
    verification_method: 'Accreditation body scope and certificate validity verification',
    result: 'COMPLIANT',
    confidence: 'HIGH',
    source_document: '05_Statutory_Affidavits_and_Compliance_Undertakings.pdf',
    source_page: 2,
  },
  {
    id: 'CHK-10',
    category: 'Technical',
    requirement_title: 'Typing Speed Qualification (15,000 Key Depressions/Hour)',
    requirement_clause: 'Annexure-5 Technical Specifications (Page 5)',
    requirement_text: 'Clerical/Non-Technical Graduate personnel must demonstrate minimum 15,000 key depressions/hour typing speed.',
    submitted_evidence: 'Self-declaration by HR department in Document 05 asserting staff qualification.',
    extraction_details: 'No third-party speed test logs, typing institute certificates, or empirical screening reports attached.',
    cross_document_evidence: 'Internal self-declaration only',
    variance: 'Lack of empirical third-party certification',
    verification_method: 'Technical qualification evidence audit',
    result: 'CLARIFICATION_PENDING',
    confidence: 'MEDIUM',
    source_document: '05_Statutory_Affidavits_and_Compliance_Undertakings.pdf',
    source_page: 2,
    finding_id: 'FND-04',
    finding_title: 'Unverified Technical Typing Speed Self-Declaration',
  },
];

export const DEMO_FINDINGS: OfficerFinding[] = [
  {
    id: 'FND-01',
    application_id: 'APP-001',
    applicationId: 'APP-001',
    bidder_name: 'Aravind Integrated Solutions Private Limited',
    matrix_item_id: 'CHK-06',
    title: 'Omission of Mandatory Annexure-9 VVIP Area Affidavit',
    description: 'Tender Clause 2(d)(ii) explicitly requires a notarized Annexure-9 affidavit regarding the non-deployment of personnel with criminal antecedents in sensitive/VVIP areas. The affidavit is completely missing from Document 05.',
    severity: 'CRITICAL',
    finding_type: 'MISSING_MANDATORY_DOCUMENT',
    recommended_action: 'Issue formal clarification notice or flag for committee disqualification review under GTC Clause 4.',
    review_status: 'PENDING',
    officer_notes: 'Critical omission. Requires formal procurement committee ruling before commercial opening.',
  },
  {
    id: 'FND-02',
    application_id: 'APP-001',
    applicationId: 'APP-001',
    bidder_name: 'Aravind Integrated Solutions Private Limited',
    matrix_item_id: 'CHK-03',
    title: 'Cross-Document Financial Turnover Inconsistency (₹80.15 Lakhs Variance)',
    description: 'CA Turnover Certificate (UDIN 21543892BG1128, Page 1) certifies FY 2019-20 turnover as ₹6,20,50,000/-, whereas Audited P&L Schedule III (Page 3) reports Revenue from Operations as ₹5,40,35,000/-. The unexplained variance is ₹80.15 Lakhs.',
    severity: 'HIGH',
    finding_type: 'CROSS_DOCUMENT_DISCREPANCY',
    recommended_action: 'Direct bidder and statutory auditor to submit formal reconciliation of turnover figures under GFR Rule 144.',
    review_status: 'CLARIFICATION_REQUESTED',
    officer_notes: 'Clarification query drafted. Bidder granted 3 business days to furnish CA reconciliation statement.',
  },
  {
    id: 'FND-03',
    application_id: 'APP-001',
    applicationId: 'APP-001',
    bidder_name: 'Aravind Integrated Solutions Private Limited',
    matrix_item_id: 'CHK-05',
    title: 'Experience Project 3 Below Threshold & Missing Completion Certificate',
    description: 'Tender requires 3 similar completed works of at least ₹2.85 Cr each. Project 3 (SAIL) is ₹1.90 Cr (shortfall ₹95 Lakhs) and is accompanied only by an interim performance letter rather than a final Completion Certificate.',
    severity: 'MEDIUM',
    finding_type: 'EXPERIENCE_DEFICIENCY',
    recommended_action: 'Evaluate whether Project 1 (₹3.82 Cr) and Project 2 (₹2.95 Cr) can qualify under 2-order threshold (₹3.57 Cr) or seek clarification.',
    review_status: 'PENDING',
    officer_notes: 'Under committee review. Project 1 and 2 alone do not satisfy the 2 x ₹3.57 Cr criterion.',
  },
  {
    id: 'FND-04',
    application_id: 'APP-001',
    applicationId: 'APP-001',
    bidder_name: 'Aravind Integrated Solutions Private Limited',
    matrix_item_id: 'CHK-10',
    title: 'Unverified Technical Typing Speed Self-Declaration',
    description: 'Annexure-5 specifies 15,000 key depressions/hour typing speed for 86 clerical staff. Bidder provides only an unverified self-assertion without empirical typing speed assessment logs or certified test results.',
    severity: 'LOW',
    finding_type: 'TECHNICAL_AMBIGUITY',
    recommended_action: 'Seek undertaking from bidder to conduct third-party typing proficiency tests prior to deployment.',
    review_status: 'PENDING',
    officer_notes: 'Can be addressed through pre-deployment skill verification clause.',
  },
  {
    id: 'FND-05',
    application_id: 'APP-001',
    applicationId: 'APP-001',
    bidder_name: 'Aravind Integrated Solutions Private Limited',
    matrix_item_id: 'CHK-07',
    title: 'Entity Name Variation Between Incorporation and Tax Filings',
    description: 'Incorporation Certificate states "Aravind Integrated Solutions Private Limited" whereas GST REG-06 and Bank Guarantee correspondence use "Aravind Integrated Solutions Pvt. Ltd."',
    severity: 'LOW',
    finding_type: 'NAME_VARIATION',
    recommended_action: 'Confirm entity PAN continuity (AAACA9182K) across both documents and accept as standard business abbreviation.',
    review_status: 'ACCEPTED',
    officer_notes: 'Verified: PAN AAACA9182K is identical on both records. Normal abbreviation acceptable under GeM guidelines.',
    overridden_at: '2021-03-25T11:20:00Z',
  },
];

export const DEMO_AUDIT_LOGS: AuditLogItem[] = [
  {
    id: 'AUD-01',
    timestamp: '2021-03-25T11:20:00Z',
    actor: 'Procurement Officer (Admin)',
    action: 'OFFICER_OVERRIDE',
    entity_type: 'FINDING',
    details: 'Reviewed FND-05 (Name Variation): PAN continuity verified. Marked finding as ACCEPTED.',
  },
  {
    id: 'AUD-02',
    timestamp: '2021-03-25T10:45:00Z',
    actor: 'Procurement Officer (Admin)',
    action: 'CLARIFICATION_REQUESTED',
    entity_type: 'FINDING',
    details: 'Initiated formal clarification notice for FND-02 (Financial turnover ₹80.15L discrepancy).',
  },
  {
    id: 'AUD-03',
    timestamp: '2021-03-25T09:30:00Z',
    actor: 'BidGuard DocumentAI',
    action: 'CROSS_DOCUMENT_AUDIT',
    entity_type: 'VERIFICATION',
    details: 'Extracted financial figures across CA cert and P&L. Detected variance ₹80.15 Lakhs for FY 2019-20.',
  },
  {
    id: 'AUD-04',
    timestamp: '2021-03-25T09:15:00Z',
    actor: 'BidGuard LayoutLMv3',
    action: 'DOCUMENT_SEGMENTATION',
    entity_type: 'APPLICATION',
    details: 'Segmented 6 application documents into 16 verified pages and 42 layout clauses.',
  },
  {
    id: 'AUD-05',
    timestamp: '2021-03-25T09:00:00Z',
    actor: 'GeM Ingestion Service',
    action: 'PACKAGE_INGESTION',
    entity_type: 'APPLICATION',
    details: 'Ingested bidder application package for Aravind Integrated Solutions Private Limited.',
  },
];

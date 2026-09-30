# SIH26100 — AI-Powered Integrated Bid Compliance Verification Platform for GeM Procurement

## 1. PROJECT OVERVIEW

Build a production-grade web platform called **BidGuard AI** for the SIH26100 problem statement:

**AI-Powered Integrated Bid Compliance Verification Platform for GeM Procurement**

The platform is designed for procurement officers who need to evaluate large tender documents and bidder submissions against tender-specific eligibility, commercial, statutory, technical and documentary requirements.

The system must NOT automatically make the final legal procurement decision.

Instead, it should:

1. Understand the tender.
2. Extract every relevant compliance requirement.
3. Convert requirements into structured verification rules.
4. Accept bidder documents.
5. Extract evidence from bidder documents.
6. Compare bidder evidence against tender requirements.
7. Verify eligible information against available government/open-data sources or authorized APIs.
8. Detect missing, expired, inconsistent or contradictory information.
9. Generate an evidence-backed compliance score.
10. Highlight high-risk issues.
11. Maintain an audit trail.
12. Allow the procurement officer to accept, reject, override or request clarification for individual findings.
13. Produce a final officer-ready compliance report.

The platform should behave as an **AI-assisted procurement verification system**, not as an autonomous qualification authority.

---

# 2. CORE USER

## Primary User

### Procurement Officer

The procurement officer can:

* Create tenders.
* Upload tender PDFs.
* Analyze tenders.
* Review extracted clauses.
* Configure applicability.
* Upload bidder submissions.
* Run compliance verification.
* View evidence.
* Verify government information.
* Review mismatches.
* Approve/reject individual findings.
* Request clarification.
* Compare multiple bidders.
* Generate reports.
* Export audit records.
* Track verification history.

---

# 3. MAIN APPLICATION NAVIGATION

The left sidebar should contain:

### Dashboard

Overview of all procurement activities.

### Tenders

Manage uploaded and analyzed tenders.

### Bidders

Manage bidder profiles and submissions.

### Compliance

Run and monitor compliance verification.

### Verification Center

Verify bidder information against available data sources.

### Evidence

Central evidence repository.

### Risk & Findings

Review inconsistencies, missing documents and risk findings.

### Comparison

Compare bidders against the same tender.

### Reports

Generate compliance and audit reports.

### Audit Trail

Complete history of system and officer actions.

### Data Sources

Manage government/open-data/authorized API connectors.

### Settings

System configuration, roles, thresholds and organization settings.

---

# 4. DASHBOARD

The dashboard is the main landing page.

## Top Statistics Cards

### Total Tenders

Displays:

* Total tenders uploaded.
* Active tenders.
* Completed tenders.
* Draft tenders.

**Action:**
Clicking the card opens the Tenders page with the corresponding filter applied.

---

### Total Bidders

Displays:

* Total bidders evaluated.
* New bidders.
* Pending verification.
* Completed verification.

Clicking opens Bidders with the relevant filter.

---

### Pending Reviews

Displays findings requiring procurement officer attention.

Examples:

* Missing evidence.
* Conflicting information.
* Low-confidence AI extraction.
* Government verification failure.
* Conditional requirements awaiting applicability decision.

Clicking opens Risk & Findings filtered to `REVIEW`.

---

### High-Risk Findings

Displays number of high-risk compliance issues.

Clicking opens the high-risk findings list.

---

### Compliance Overview

Display:

* Compliant
* Non-compliant
* Conditional
* Officer Review Required

Use a visual chart.

---

## Recent Tenders

Each row displays:

* Tender ID
* Tender title
* Organization
* Upload date
* Bid due date
* Number of bidders
* Verification status
* Compliance status

Buttons:

### View

Open tender details.

### Continue

Resume incomplete analysis.

### Verify

Start verification.

### Report

Open tender report.

### More

Dropdown:

* Duplicate
* Archive
* Export
* Delete

---

# 5. CREATE TENDER

Primary button:

### + New Tender

Clicking opens a multi-step wizard.

---

## Step 1 — Tender Information

Fields:

* Tender ID
* Tender title
* Organization
* Department
* Tender category
* Tender type
* Issue date
* Bid due date
* Bid opening date
* Procurement portal
* Tender description

Buttons:

### Save Draft

Stores incomplete tender.

### Next

Moves to document upload.

### Cancel

Returns to dashboard.

---

# 6. TENDER DOCUMENT UPLOAD

## Upload Tender

Large drag-and-drop area:

**Drop tender PDF here**

Supported:

* PDF
* Multiple PDF documents
* Addendum
* Corrigendum
* Supporting tender documents

Buttons:

### Browse Files

Open file picker.

### Upload

Upload selected documents.

### Remove

Remove selected file.

### Add Document

Attach another tender document.

---

## Document Processing

After upload display:

* Filename
* File size
* Page count
* Upload time
* Processing status

Processing stages:

1. Uploaded
2. PDF parsed
3. Pages extracted
4. Text extracted
5. Tables detected
6. Clauses identified
7. Requirements extracted
8. Rules generated
9. Human review required

---

# 7. AI TENDER ANALYSIS

Primary button:

### Analyze Tender

The AI analyzes the complete tender package.

It should identify:

### Administrative Requirements

Examples:

* Bid submission requirements.
* Tender forms.
* Signature requirements.
* Stamp requirements.
* Submission deadlines.

### Statutory Requirements

Examples:

* GST.
* PAN.
* Udyam/MSME.
* Other registration requirements where applicable.

### Commercial Requirements

Examples:

* Price format.
* Taxes.
* Freight.
* Payment conditions.
* Price validity.
* EMD/Bid Security where applicable.

### Eligibility Requirements

Examples:

* Experience.
* Financial capability.
* Approved supplier status.
* Technical qualification.

### Declaration Requirements

Examples:

* Conflict of interest.
* Multiple bids.
* Border-country restrictions.
* Integrity declarations.
* Other tender declarations.

### Technical Requirements

Examples from the uploaded CPCL pressure-vessel tender:

* General arrangement drawings.
* Design calculations.
* Material test certificates.
* Welding procedures.
* Qualification reports.
* NDT reports.
* Radiographic examination reports.
* Heat-treatment procedures.
* Vendor data requirements.

---

# 8. TENDER REQUIREMENT MATRIX

After analysis, display a complete table.

Columns:

| Field          | Description                                      |
| -------------- | ------------------------------------------------ |
| Requirement ID | Unique identifier                                |
| Category       | Statutory / Technical / Commercial / Eligibility |
| Clause         | Tender clause                                    |
| Page           | Source page                                      |
| Requirement    | Exact normalized requirement                     |
| Applicability  | Mandatory / Conditional / Informational          |
| Evidence       | Required evidence                                |
| Verification   | Verification method                              |
| Automation     | Automatic / AI / Manual                          |
| Risk           | Low / Medium / High / Critical                   |
| Status         | Pending / Verified / Review                      |

---

## Requirement Details

Clicking a requirement opens a side panel.

Display:

### Requirement

Normalized explanation.

### Original Tender Text

Show the source text.

### Source

* Document
* Page
* Clause
* Section

### Evidence Required

List every document/evidence item.

### Verification Rule

Explain how the system will check it.

### Applicability Rule

Explain when the requirement applies.

### Risk

Display risk level.

### AI Confidence

Display confidence.

### Evidence

Show matched bidder evidence.

Buttons:

### Open Source Page

Open the exact tender page.

### Edit Rule

Officer can modify the rule.

### Mark Mandatory

Set applicability to mandatory.

### Mark Conditional

Set conditional.

### Disable Rule

Disable an incorrectly extracted rule.

### Approve Rule

Confirm extracted rule.

---

# 9. IMPORTANT CPCL-SPECIFIC RULES

The initial rule engine must support requirements identified from the uploaded CPCL/EIL tender.

## Zero-Deviation Rule

The uploaded RFQ explicitly describes the tender as a **Nil/zero-deviation tender**, with deviations potentially leading to rejection.

The platform should therefore detect:

* Technical deviations.
* Commercial deviations.
* Conditional statements.
* Exceptions.
* "Subject to" statements.
* Missing confirmations.
* Modified tender conditions.

Button:

### Scan for Deviations

Output:

* Requirement.
* Bidder response.
* Detected deviation.
* Severity.
* Source page.
* Explanation.

---

# 10. MSE / UDYAM VERIFICATION

The uploaded tender contains an MSE section requiring bidders claiming MSE status to provide Udyam information and supporting evidence.

Create:

### MSE Verification Card

Fields:

* MSE claimed: Yes / No
* Udyam number
* Organization name
* Certificate date
* Category
* Supporting certificate

Buttons:

### Verify Udyam

Run available government/open-data verification.

### View Certificate

Open uploaded certificate.

### Compare Names

Compare:

* Bidder legal name
* Udyam name
* Tender bidder name

### Flag Mismatch

Create finding.

---

# 11. GST VERIFICATION

The tender contains GST registration and taxation requirements.

GST verification page:

Fields:

* GSTIN
* Legal name
* Trade name
* Registration status
* Registration date
* State
* Taxpayer type

Buttons:

### Verify GST

Use an authorized connector when configured.

### Upload GST Certificate

Upload supporting evidence.

### Compare With Bidder

Compare GST legal name with bidder documents.

### View Evidence

### Create Finding

Possible results:

* Verified.
* Not verified.
* Name mismatch.
* Missing.
* Expired/inactive where supported.
* Manual verification required.

---

# 12. PAN VERIFICATION

PAN information should be extracted from bidder documentation where available.

Display:

* PAN
* Legal name
* Document source
* Confidence

Buttons:

### Verify

Use an authorized source when available.

### Compare

Compare against GST/Udyam/bidder documents.

### Flag Mismatch

---

# 13. BORDER-COUNTRY VERIFICATION

The tender references the Department of Expenditure requirements concerning bidders from countries sharing a land border with India and requires applicable forms.

Create:

### Country Compliance Card

Fields:

* Bidder country.
* Beneficial ownership information where applicable.
* Form-IA/Form-II status.
* Registration requirement.
* Verification status.

Buttons:

### Verify Declaration

### Review Country

### Flag for Officer

The platform must not make a legal determination beyond the configured tender rule. It should identify the relevant condition and send uncertain cases to officer review.

---

# 14. MAKE IN INDIA

The system must be clause-aware.

This is important because the uploaded tender contains general PPP-MII policy material, but a particular BDS qualification clause can be marked **Not Applicable**.

Therefore the system must NOT simply say:

> "Make in India is mandatory."

Instead:

### Applicability Engine

Determine:

* Policy referenced?
* Qualification clause applicable?
* Class-I local supplier requirement?
* Local-content declaration required?
* Form required?

Display:

**Applicable / Not Applicable / Conditional / Officer Review**

Buttons:

### Review Applicability

### View Tender Clause

### Override

---

# 15. INTEGRITY PACT

Create a dedicated check.

Fields:

* Integrity Pact required?
* Submitted?
* Signed?
* Stamped?
* Correct version?
* IEM information present?

Buttons:

### View Integrity Pact

### Verify Signature

### Mark Verified

### Raise Finding

The tender states that required signed/stamped Integrity Pact submission can be a disqualification issue where applicable.

---

# 16. CONFLICT OF INTEREST

The platform should check:

* Common management.
* Sister concerns.
* Allied firms.
* Multiple bids.
* Agent/principal relationships.
* Conflicting declarations.

The system should create an:

### Entity Relationship View

Example:

```text
Bidder A
   │
   ├── Director X
   │
   ├── Company B
   │
   └── Company C
```

If multiple bidders share relevant entities:

**Potential Conflict Detected**

Buttons:

### Investigate

### Compare Bidders

### View Evidence

### Mark False Positive

### Escalate

---

# 17. TECHNICAL COMPLIANCE ENGINE

This is one of the most important features.

The system must compare bidder technical documents against tender technical requirements.

For the CPCL pressure-vessel tender, technical evidence can include:

* Drawings.
* Design calculations.
* BOM.
* Material specifications.
* Material test certificates.
* Welding procedures.
* Qualification reports.
* NDT reports.
* Radiography reports.
* Heat-treatment records.
* Testing records.
* Inspection records.

The Vendor Data Requirements explicitly list these categories.

---

# 18. TECHNICAL DOCUMENT MATRIX

Display:

| Requirement          | Required | Submitted | Matched | Result |
| -------------------- | -------: | --------: | ------: | ------ |
| GA Drawing           |      Yes |       Yes |     Yes | PASS   |
| Design Calculation   |      Yes |       Yes | Partial | REVIEW |
| Material Certificate |      Yes |        No |      No | FAIL   |
| Welding Procedure    |      Yes |       Yes |     Yes | PASS   |
| NDT Report           |      Yes |       Yes |      No | REVIEW |

Buttons:

### Open Document

### Compare

### View Requirement

### Mark Verified

### Request Clarification

---

# 19. DOCUMENT INTELLIGENCE

When bidder documents are uploaded, automatically perform:

### OCR

For scanned documents.

### Text Extraction

For digital PDFs.

### Table Extraction

For:

* Financial tables.
* GST information.
* Technical specifications.
* Material tables.
* Experience tables.

### Entity Extraction

Extract:

* Company name.
* GSTIN.
* PAN.
* Udyam number.
* Addresses.
* Dates.
* Registration numbers.
* Directors/signatories where present.

### Date Extraction

Identify:

* Issue date.
* Expiry date.
* Validity period.
* Certification date.

---

# 20. CROSS-DOCUMENT CONSISTENCY ENGINE

This should be a major innovation feature.

Compare the same entity across:

* Tender response.
* PAN.
* GST.
* Udyam.
* Bank document.
* Experience certificate.
* Technical documents.
* Declarations.

Example:

```text
Bidder Name:
ABC Engineering Pvt Ltd

GST:
ABC Engineering Private Limited

Udyam:
ABC Engineering Pvt. Ltd.

Result:
Potential name variation
```

The AI should determine whether this is:

* Exact match.
* Formatting variation.
* Minor variation.
* Potential mismatch.
* Serious mismatch.

Button:

### Investigate Mismatch

---

# 21. EVIDENCE GRAPH

Create a visual evidence graph.

Example:

```text
                    ┌──────────────┐
                    │   BIDDER     │
                    └──────┬───────┘
                           │
          ┌────────────────┼────────────────┐
          ↓                ↓                ↓
       GSTIN             PAN             UDYAM
          │                │                │
          ↓                ↓                ↓
     GST Evidence     PAN Evidence    MSME Evidence
          │                │                │
          └────────────────┼────────────────┘
                           ↓
                   CONSISTENCY ENGINE
                           ↓
                    COMPLIANCE RESULT
```

Every result must be traceable back to evidence.

---

# 22. EVIDENCE VIEWER

When an officer clicks evidence:

Display:

* Document name.
* Page.
* Highlighted text.
* Extracted value.
* Requirement.
* Confidence.
* Verification source.

Buttons:

### Open Document

### Open Page

### Highlight Evidence

### Accept Evidence

### Reject Evidence

### Replace Evidence

---

# 23. AI EXPLANATION

Every AI finding must provide:

### Finding

What was detected.

### Why

Why it matters.

### Evidence

Which document/page supports the conclusion.

### Rule

Which tender requirement was applied.

### Confidence

0–100%.

### Recommended Action

Example:

> Request updated certificate.

The explanation must never pretend that an external verification occurred when no external source was actually checked.

---

# 24. COMPLIANCE SCORE

Create a transparent score.

Example:

```text
Overall Compliance
        82%
```

Breakdown:

* Statutory: 95%
* Eligibility: 88%
* Commercial: 90%
* Technical: 76%
* Documentation: 80%
* Declarations: 100%

Do not make the score the sole qualification decision.

Display:

**"Score is advisory. Final procurement decision remains with the authorized officer."**

---

# 25. RISK ENGINE

Risk levels:

### LOW

Minor documentation issue.

### MEDIUM

Potential inconsistency requiring review.

### HIGH

Important missing or conflicting evidence.

### CRITICAL

Potential major eligibility, integrity, technical or statutory issue.

Risk factors:

* Missing mandatory document.
* Expired evidence.
* Identity mismatch.
* Technical non-compliance.
* Conflict-of-interest signal.
* Multiple bid signal.
* Invalid/failed verification.
* Significant deviation.
* Low AI confidence.

---

# 26. FINDINGS CENTER

Table:

| Finding | Bidder | Category | Severity | Confidence | Status |
| ------- | ------ | -------- | -------- | ---------- | ------ |

Filters:

* High risk.
* Missing.
* Mismatch.
* Verification failure.
* AI uncertainty.
* Technical.
* Commercial.
* Statutory.

Buttons:

### Review

### Assign

### Accept

### Reject

### Request Clarification

### Escalate

---

# 27. CLARIFICATION WORKFLOW

Officer can click:

### Request Clarification

Select:

* Missing document.
* Incorrect document.
* Name mismatch.
* Technical clarification.
* Statutory clarification.
* Other.

Enter:

**Clarification message**

Buttons:

### Send Request

### Save Draft

### Cancel

Status:

* Requested.
* Awaiting response.
* Response received.
* Under review.
* Resolved.

---

# 28. BIDDER PROFILE

Each bidder gets a unified profile.

Display:

### Identity

* Legal name.
* Address.
* PAN.
* GSTIN.
* Udyam.
* Registration details.

### Tender Participation

List all tenders where bidder participated.

### Compliance History

Show historical:

* Passed.
* Failed.
* Clarification.
* Review.

### Evidence

All submitted evidence.

### Risk

Current risk level.

### Findings

Open and resolved findings.

---

# 29. MULTI-BIDDER COMPARISON

Select multiple bidders.

Display:

| Requirement    | Bidder A | Bidder B | Bidder C |
| -------------- | -------- | -------- | -------- |
| GST            | PASS     | PASS     | REVIEW   |
| Udyam          | PASS     | N/A      | PASS     |
| Technical      | PASS     | REVIEW   | FAIL     |
| Integrity Pact | PASS     | PASS     | PASS     |
| Deviations     | None     | 2        | 1        |

Buttons:

### Compare

### Export Comparison

### Open Bidder

### View Finding

---

# 30. TENDER CLAUSE EXPLORER

Create a searchable tender viewer.

Left:

Document tree.

Center:

PDF page.

Right:

AI extracted requirements.

Search:

### Search Tender

User can search:

* GST.
* Udyam.
* Integrity Pact.
* Experience.
* Blacklist.
* Technical.
* Declaration.
* Payment.
* Inspection.

When clicked, jump directly to source page.

---

# 31. ASK TENDER AI

Add a conversational assistant.

Example questions:

> What documents are mandatory?

> Which requirements are conditional?

> What are the technical documents required?

> Is MSE preference applicable?

> Where is the Integrity Pact requirement?

> What happens if there is a deviation?

The answer must always show:

**Source → Clause → Page → Evidence**

Buttons:

### View Source

### Add as Requirement

### Create Finding

---

# 32. GOVERNMENT VERIFICATION CENTER

Create a centralized verification screen.

Sources should be modular.

Examples:

* Udyam / MSME.
* GST.
* DigiLocker.
* Government Open Data.
* API Setu.
* Other authorized government services.

Each connector displays:

* Source name.
* Connection status.
* Last successful verification.
* Authentication status.
* Available fields.

Buttons:

### Configure

### Test Connection

### Verify Bidder

### View Logs

Important:

If an API requires credentials/authorization, the system must show:

**"Authorized connection required."**

It must never fabricate verification results.

---

# 33. OPEN DATA VERIFICATION

Allow importing datasets from government open-data sources.

Features:

### Dataset Catalog

Fields:

* Dataset.
* Publisher.
* Last updated.
* License.
* Resource.
* Status.

Buttons:

### Import Dataset

### Refresh

### Search

### View Schema

### Verify Bidder

### View Source

---

# 34. VERIFICATION RESULT

Example:

```text
GST Verification

Status: VERIFIED

Source: Authorized GST connector

Matched:
✓ GSTIN
✓ Legal Name

Potential Issue:
Address differs from bidder document.

Action:
Officer Review Required
```

Buttons:

### Accept

### Flag

### View Evidence

### Create Finding

---

# 35. AUDIT TRAIL

Every important action must be logged.

Example:

```text
02 Sep 2026 10:45
Officer uploaded bidder documents.

02 Sep 2026 10:47
AI extracted GSTIN.

02 Sep 2026 10:48
GST verification executed.

02 Sep 2026 10:48
Name mismatch detected.

02 Sep 2026 10:50
Officer marked finding for clarification.
```

Log:

* User.
* Timestamp.
* Action.
* Object.
* Previous state.
* New state.
* Source.
* Reason.

---

# 36. REPORT GENERATION

Primary button:

### Generate Report

Report sections:

1. Tender information.
2. Bidder information.
3. Executive summary.
4. Compliance score.
5. Mandatory requirements.
6. Conditional requirements.
7. Statutory verification.
8. Technical verification.
9. Commercial verification.
10. Missing documents.
11. Mismatches.
12. Risk findings.
13. Clarification history.
14. Evidence references.
15. Officer decisions.
16. Audit trail.

Buttons:

### Generate PDF

### Export Excel

### Export JSON

### Print

### Share Internally

---

# 37. FINAL OFFICER REVIEW

Create a dedicated final review screen.

Display:

### Overall Status

Possible states:

* Pending Review
* Compliant Recommendation
* Non-Compliant Recommendation
* Conditional
* Clarification Required
* Officer Decision Required

Show every unresolved issue.

Officer actions:

### Approve Finding

### Reject Finding

### Override AI

### Request Clarification

### Mark Verified

### Add Comment

### Finalize Review

---

# 38. FINAL DECISION SAFEGUARD

Before finalization display:

> "AI-generated results are advisory. Please verify the evidence and tender requirements before making the procurement decision."

Checkbox:

**I have reviewed the evidence and findings.**

Button:

### Submit Officer Decision

The system records:

* Officer.
* Date/time.
* Decision.
* Comments.
* Evidence reviewed.
* Overrides.

---

# 39. SETTINGS

## Organization

* Organization name.
* Logo.
* Department.

## Compliance

Configure:

* Risk thresholds.
* Score weights.
* Confidence threshold.
* Mandatory review rules.

## AI

Configure:

* Model.
* Temperature.
* Extraction settings.
* OCR settings.

## Verification

Configure:

* API connectors.
* Credentials.
* Government data sources.

## Users

Roles:

### Admin

Full access.

### Procurement Officer

Tender and bidder verification.

### Reviewer

Review evidence/findings.

### Auditor

Read-only audit access.

---

# 40. NOTIFICATIONS

Notification center should display:

* Tender deadline approaching.
* Analysis completed.
* Bidder upload completed.
* Verification completed.
* High-risk issue detected.
* Clarification response received.
* Officer review required.

Buttons:

### View

### Mark Read

### Mark All Read

---

# 41. SEARCH

Global search should search:

* Tenders.
* Bidders.
* Requirements.
* Documents.
* Findings.
* Evidence.
* Audit events.

Search result should show:

```text
Search: "GST"

Tenders
Bidders
Requirements
Documents
Findings
```

---

# 42. BACKEND ARCHITECTURE

Build backend first.

Recommended structure:

```text
backend/
├── app/
│   ├── api/
│   │   ├── auth/
│   │   ├── tenders/
│   │   ├── bidders/
│   │   ├── documents/
│   │   ├── requirements/
│   │   ├── compliance/
│   │   ├── verification/
│   │   ├── evidence/
│   │   ├── findings/
│   │   ├── reports/
│   │   └── audit/
│   │
│   ├── services/
│   │   ├── pdf_parser/
│   │   ├── ocr/
│   │   ├── requirement_extractor/
│   │   ├── rule_engine/
│   │   ├── evidence_engine/
│   │   ├── consistency_engine/
│   │   ├── verification_engine/
│   │   ├── risk_engine/
│   │   └── report_engine/
│   │
│   ├── models/
│   ├── schemas/
│   ├── repositories/
│   ├── core/
│   └── main.py
│
├── tests/
├── migrations/
├── data/
└── requirements.txt
```

---

# 43. DATABASE

Use PostgreSQL.

Core tables:

```text
users
organizations
tenders
tender_documents
tender_pages
requirements
requirement_evidence_rules
bidders
bidder_documents
document_pages
extracted_entities
verification_requests
verification_results
evidence
compliance_checks
compliance_results
findings
clarifications
officer_decisions
audit_logs
data_sources
api_connections
```

---

# 44. REQUIREMENT DATA MODEL

Every requirement must contain:

```text
requirement_id
tender_id
document_id
page_number
clause_number
category
title
description
original_text
applicability
evidence_required
verification_method
verification_source
automation_level
risk_level
confidence
status
created_at
updated_at
```

This becomes the foundation of the platform.

---

# 45. COMPLIANCE ENGINE

The engine follows:

```text
Tender Requirement
       ↓
Applicability Rule
       ↓
Required Evidence
       ↓
Bidder Evidence
       ↓
Extraction
       ↓
Verification
       ↓
Cross-document Comparison
       ↓
Risk Assessment
       ↓
Compliance Result
       ↓
Officer Review
```

Possible result:

```text
PASS
FAIL
REVIEW
NOT_APPLICABLE
PENDING
```

---

# 46. AI ARCHITECTURE

AI should be used for:

### Tender understanding

Identify clauses and requirements.

### Requirement normalization

Convert complex legal/tender language into structured rules.

### Document understanding

Understand bidder documents.

### Semantic comparison

Compare tender requirement with bidder response.

### Deviation detection

Identify differences from tender requirements.

### Entity matching

Match names across documents.

### Contradiction detection

Identify conflicting information.

### Explanation

Generate understandable findings.

AI should NOT invent:

* Verification results.
* Government records.
* Certificates.
* API responses.
* Legal conclusions.

---

# 47. HUMAN-IN-THE-LOOP ARCHITECTURE

Every uncertain result should go through:

```text
AI
 ↓
Finding
 ↓
Evidence
 ↓
Officer Review
 ↓
Accept / Reject / Override / Clarify
 ↓
Final Officer Decision
```

This is a core design principle.

---

# 48. DEMO MODE

Create a demonstration environment.

Include:

### Demo Tender

Use the supplied CPCL tender as the reference tender.

### Demo Bidders

Create:

**Bidder A — Fully Compliant**

**Bidder B — Missing Documents**

**Bidder C — Identity Mismatch**

**Bidder D — Technical Non-Compliance**

**Bidder E — Multiple Issues**

---

# 49. DEMO SCENARIOS

## Scenario 1

Bidder A:

* Complete documentation.
* Matching identity.
* Technical documents present.

Result:

**High compliance / low risk**

---

## Scenario 2

Bidder B:

Missing:

* Required declaration.
* Supporting certificate.
* Technical document.

Result:

**Missing evidence**

---

## Scenario 3

Bidder C:

GST legal name differs from Udyam/bid submission.

Result:

**Cross-document mismatch**

---

## Scenario 4

Bidder D:

Technical value does not satisfy tender requirement.

Result:

**Technical non-compliance**

---

## Scenario 5

Bidder E:

Multiple high-risk findings.

Result:

**Officer review required**

---

# 50. FRONTEND DESIGN

Use:

* React
* TypeScript
* Vite
* Tailwind CSS
* Modern component architecture.

Design should be:

**Professional government procurement dashboard**

Avoid unnecessary flashy animations.

Prioritize:

* Information density.
* Readability.
* Evidence traceability.
* Clear status indicators.
* Tables.
* Side panels.
* Document viewers.
* Action buttons.

---

# 51. MAIN BUTTON BEHAVIOR

Every button must have a real action.

Do NOT create decorative buttons.

Examples:

### Analyze Tender

Starts asynchronous tender analysis.

### Verify

Executes configured verification.

### View Evidence

Opens source document/page.

### Compare

Runs comparison.

### Review

Opens finding review interface.

### Accept

Changes finding status.

### Reject

Rejects AI finding with officer reason.

### Override

Allows officer to override AI recommendation and requires reason.

### Request Clarification

Creates clarification workflow.

### Generate Report

Creates report from current verified state.

### Export

Downloads selected data.

### Refresh

Refreshes current verification state.

### Retry

Retries failed processing.

### Cancel

Cancels pending operation where safe.

### Save

Persists current changes.

### Submit

Commits the workflow state.

---

# 52. STATUS SYSTEM

Use consistent statuses throughout the application.

### Blue / Informational

Processing.

### Green

Verified / Pass.

### Yellow

Review required.

### Red

Failure / High-risk.

### Grey

Not applicable.

Never rely only on color; always display text.

---

# 53. PROCESSING STATES

For long-running operations:

```text
QUEUED
PROCESSING
COMPLETED
FAILED
RETRY_REQUIRED
REVIEW_REQUIRED
```

Show progress.

Example:

```text
Analyzing Tender

✓ Upload complete
✓ PDF extraction
✓ Page segmentation
✓ Clause detection
● Requirement extraction
○ Rule generation
○ Final validation
```

---

# 54. SECURITY

Implement:

* Authentication.
* Role-based authorization.
* Tender-level access control.
* Secure document storage.
* Audit logs.
* API credential encryption.
* File validation.
* Malware/file-type validation.
* Request validation.
* Rate limiting.
* Secure secrets handling.

---

# 55. PRIVACY

Bidder documents can contain sensitive business information.

Therefore:

* Do not expose documents publicly.
* Restrict document access by organization/tender.
* Record access logs.
* Do not send documents to external AI services unless configured and authorized.
* Provide configurable retention.

---

# 56. API DESIGN

Example endpoints:

```text
POST /api/v1/tenders
POST /api/v1/tenders/{id}/documents
POST /api/v1/tenders/{id}/analyze

GET /api/v1/tenders/{id}
GET /api/v1/tenders/{id}/requirements

POST /api/v1/bidders
POST /api/v1/bidders/{id}/documents

POST /api/v1/compliance/{tender_id}/{bidder_id}/run
GET /api/v1/compliance/{id}

POST /api/v1/verification/gst
POST /api/v1/verification/udyam
POST /api/v1/verification/run

GET /api/v1/evidence/{id}
GET /api/v1/findings
POST /api/v1/findings/{id}/review

POST /api/v1/clarifications
GET /api/v1/audit

POST /api/v1/reports
```

---

# 57. SYSTEM'S MOST IMPORTANT DIFFERENTIATOR

Do not position this as:

> "AI reads tenders."

Instead position it as:

> **Evidence-driven, tender-specific compliance verification with traceable AI reasoning and human procurement control.**

The system connects:

```text
Tender Clause
      ↓
Compliance Rule
      ↓
Required Evidence
      ↓
Bidder Document
      ↓
Extracted Fact
      ↓
Government/Open Data
      ↓
Cross-source Consistency
      ↓
Risk
      ↓
Officer Decision
```

This makes the system much more defensible than a simple document chatbot.

---

# 58. FINAL USER JOURNEY

The complete workflow should be:

```text
LOGIN
  ↓
DASHBOARD
  ↓
CREATE TENDER
  ↓
UPLOAD TENDER PDF
  ↓
AI ANALYZES TENDER
  ↓
REQUIREMENT MATRIX
  ↓
OFFICER REVIEWS RULES
  ↓
ADD BIDDERS
  ↓
UPLOAD BIDDER DOCUMENTS
  ↓
DOCUMENT AI / OCR
  ↓
EXTRACT EVIDENCE
  ↓
RUN COMPLIANCE
  ↓
GOVERNMENT / OPEN-DATA VERIFICATION
  ↓
CROSS-DOCUMENT CONSISTENCY
  ↓
TECHNICAL VERIFICATION
  ↓
RISK ENGINE
  ↓
FINDINGS
  ↓
CLARIFICATION IF REQUIRED
  ↓
OFFICER REVIEW
  ↓
FINAL OFFICER DECISION
  ↓
GENERATE COMPLIANCE REPORT
  ↓
AUDIT TRAIL
```

# 59. DEVELOPMENT ORDER

Build strictly in this order.

## PHASE 1 — Backend Foundation

* Project setup.
* Authentication.
* PostgreSQL.
* Tender model.
* Document storage.
* Basic APIs.

## PHASE 2 — Tender Intelligence

* PDF processing.
* Page extraction.
* Clause extraction.
* Requirement extraction.
* Requirement matrix.
* Source-page references.

## PHASE 3 — Compliance Rule Engine

* Applicability engine.
* Mandatory/conditional rules.
* Evidence rules.
* Risk rules.
* Deviation detection.

## PHASE 4 — Bidder Document Intelligence

* Upload.
* OCR.
* Entity extraction.
* Date extraction.
* Certificate extraction.
* Document classification.

## PHASE 5 — Verification

* Udyam.
* GST.
* Open Government Data.
* Authorized APIs.
* Verification adapters.

## PHASE 6 — Evidence & Consistency

* Evidence graph.
* Cross-document comparison.
* Entity matching.
* Contradiction detection.

## PHASE 7 — Risk & Human Review

* Risk engine.
* Findings.
* Clarification workflow.
* Officer overrides.
* Final decision.

## PHASE 8 — Reports

* PDF.
* Excel.
* JSON.
* Audit report.

## PHASE 9 — Frontend

Only after the backend APIs and workflows are stable:

* Dashboard.
* Tender management.
* Requirement matrix.
* Bidder management.
* Compliance screen.
* Verification center.
* Evidence viewer.
* Findings.
* Reports.
* Audit trail.

## PHASE 10 — Integration & Deployment

* Frontend/backend integration.
* Authentication testing.
* Document testing.
* AI testing.
* Government connector testing.
* Security testing.
* Demo dataset.
* Docker.
* Deployment.

# 60. SUCCESS CRITERIA

The finished system should allow a procurement officer to take:

**One real tender PDF + one bidder's document package**

and produce:

```text
1. Structured tender requirements
2. Mandatory/conditional classification
3. Required evidence list
4. Bidder evidence extraction
5. Government/open-data verification where available
6. Cross-document consistency analysis
7. Technical compliance analysis
8. Missing-document detection
9. Deviation detection
10. Risk assessment
11. Evidence-backed findings
12. Officer review
13. Final officer decision record
14. Complete audit trail
15. Downloadable compliance report
```

The system must always preserve the relationship:

**Requirement → Evidence → Verification → Finding → Officer Decision**

That relationship is the central architecture of the SIH26100 solution.

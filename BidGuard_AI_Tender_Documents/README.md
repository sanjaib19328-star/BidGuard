# BidGuard AI — Real Tender Document Collection

This folder contains 4 real, publicly-issued Indian government tenders (GeM bid documents),
pulled directly from official .gov.in / .nic.in domains only. No aggregators, blogs, or
third-party tender databases were used.

**Important — please read before using these for the SIH demo:**
The four `.txt` files in this folder are the **full extracted text** of each official PDF
(fetched directly from the government source URL below each one). They are NOT the original
binary PDF files — this sandbox's outbound network only permits a short allow-list of
developer package domains (npm, pypi, GitHub, etc.), so it cannot download the original PDF
bytes from `.gov.in` / `.nic.in` servers. Since BidGuard's first pipeline stage is "PDF
extraction," you'll want the **actual PDF binaries** for a real demo, not these text mirrors.
Every source link below is a direct, one-click download of the original official PDF — please
grab those yourself and drop them into your BidGuard test set; the `.txt` files here are a
convenience so you can already see/skim/parse the real content while you do that.

## Documents

| # | File | Issuing Body | GeM Bid No. | Pages | Direct Official PDF |
|---|------|--------------|-------------|-------|----------------------|
| 1 | `01_CAG_Manpower_Hiring_BidDoc_46-GS-114-2021.txt` | Office of the Comptroller & Auditor General (CAG) of India | GEM/2021/B/1128240 | 48 | https://www.cag.gov.in/uploads/tenders/tenders-Manpower-0605ad73e121995-03771515.pdf |
| 2 | `02_AIIMS_Bhubaneswar_GeM_Bid_7437194.txt` | AIIMS Bhubaneswar (Ministry of Health & Family Welfare) | GEM/2026/B/7437194 | 22 | https://aiimsbhubaneswar.nic.in/wp-content/uploads/2026/04/GEM-BID-7431794.pdf |
| 3 | `03_MIB_RRTD_Dashboard_GeM_Bid_5391658.txt` | Research Reference & Training Division, Ministry of Information & Broadcasting | GEM/2024/B/5391658 | 5 | https://mib.gov.in/sites/default/files/2024-09/gem-bid-for-design-development-implementation-and-maintenance-of-integrated-dashboard.pdf |
| 4 | `04_PrasarBharati_Doordarshan_GeM_Bid_7439008.txt` | Doordarshan / Prasar Bharati (DD Free Dish Todapur) | GEM/2026/B/7439008 | 6 | https://prasarbharati.gov.in/wp-content/uploads/2026/05/Bid_Document_Extended.pdf |

## Why these four

They span different sectors (HR outsourcing, pharmaceuticals, IT/dashboard services,
broadcast services) but share the requirement categories BidGuard needs to demonstrate:

- **Doc #1 (CAG, 48 pp)** is the richest for a full pipeline demo: legal-entity-type
  eligibility, GST/PAN/EPF/ESIC statutory registration, 3-year turnover + audited balance
  sheets, EMD + 10% Performance Bank Guarantee, ISO 9001 conditional clause, and **six
  separate notarized affidavit annexures** — a strong traceability/documentary-mapping case.
- **Doc #2 (AIIMS Bhubaneswar, 22 pp)** layers pharma-specific statutory checks (Drugs &
  Cosmetics Act license, GMP/WHO-GMP certificate, CDSCO/SUGAM references) on top of the usual
  MSME/Startup "if applicable" turnover-and-experience relaxation clauses — good for testing
  rule-based conditional logic.
  turnover-and-experience relaxation clauses — good for testing rule-based conditional logic.
- **Docs #3 & #4 (MIB / Prasar Bharati, short custom-service bids)** are deliberately shorter
  and messier (one even shows raw GeM admin-UI text and a corrigendum log bleeding into the
  PDF) — useful for stress-testing extraction robustness on real, non-uniform government PDFs
  rather than only clean, well-formatted ones.

## A note on sourcing

Several other officially-hosted candidates were found during the search (ESIC hiring-of-CA
bid, Tamil Nadu SIPCOT works tender, UCIL bid) but their servers block automated/robotic
fetching (`robots.txt` disallow) or returned a broken link, so they aren't included here as
text extracts — their pages are still real and public if you want to fetch them manually:
- ESIC (Employees' State Insurance Corporation) — hiring of Chartered Accountant, GeM bid:
  https://esic.gov.in/attachments/tenderfile/Extention_of_Gem_bid_No_GEM_2025_B_6362444_for_Hiring_of_CA_1752561332.pdf
- SIPCOT Tamil Nadu — civil works tender (₹315 Lakh, EMD + contractor-class eligibility):
  https://sipcotweb.tn.gov.in/uploads/tenders/23/Tendernotice_1.pdf

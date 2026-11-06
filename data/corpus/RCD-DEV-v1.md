---
document_id: RCD-DEV-v1
model_id: RCD
document_type: development_report
version: 1.0
effective_date: 2025-01-15
document_status: current
source_authority: Model Development
synthetic: true
---

# Retail Credit Default Model — Development Report

DEVELOPMENT REPORT
Purpose: estimate 12-month probability of default for unsecured retail loans. Development data consist of anonymized application, bureau, and 12-month repayment snapshots from 2021-2024. Records were de-identified or synthetic before modeling. Time-based sampling was used: earlier observations for development and later observations for holdout testing. The report documents transformations, missing-value rules, feature definitions, and reproducible code parameters. Known limitation: thin-file applicants are underrepresented in the development sample. No customer names, account numbers, or raw protected-attribute values are retained in this benchmark record.

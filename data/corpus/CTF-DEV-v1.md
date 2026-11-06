---
document_id: CTF-DEV-v1
model_id: CTF
document_type: development_report
version: 1.0
effective_date: 2025-01-15
document_status: current
source_authority: Model Development
synthetic: true
---

# Card Transaction Fraud Model — Development Report

DEVELOPMENT REPORT
Purpose: rank card transactions by likelihood of fraud for analyst review. Development data consist of tokenized card authorization events and confirmed fraud labels from 2023-2025. Records were de-identified or synthetic before modeling. Time-based sampling was used: earlier observations for development and later observations for holdout testing. The report documents transformations, missing-value rules, feature definitions, and reproducible code parameters. Known limitation: new-merchant patterns have shorter label histories than established merchants. No customer names, account numbers, or raw protected-attribute values are retained in this benchmark record.

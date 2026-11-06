---
document_id: CTF-DQ-2026Q2
model_id: CTF
document_type: data_quality_report
version: 2026Q2
effective_date: 2026-06-25
document_status: current
source_authority: Data Governance
synthetic: true
---

# Card Transaction Fraud Model — Data Quality Report

DATA QUALITY REPORT
The governed source is tokenized card authorization events and confirmed fraud labels from 2023-2025. Automated checks covered schema conformity, missingness, duplicates, valid ranges, and reconciliation totals. Q2 controls passed except for the known representation limitation: new-merchant patterns have shorter label histories than established merchants. The report contains aggregate quality results only. It does not contain customer names, account numbers, protected-attribute values, or vendor source code.

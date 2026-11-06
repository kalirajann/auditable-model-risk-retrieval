---
document_id: MDP-DEV-v1
model_id: MDP
document_type: development_report
version: 1.0
effective_date: 2025-01-15
document_status: current
source_authority: Model Development
synthetic: true
---

# Mortgage Default and Prepayment Model — Development Report

DEVELOPMENT REPORT
Purpose: forecast mortgage default and voluntary prepayment over a 12-month horizon. Development data consist of de-identified monthly loan performance and macroeconomic series from 2018-2025. Records were de-identified or synthetic before modeling. Time-based sampling was used: earlier observations for development and later observations for holdout testing. The report documents transformations, missing-value rules, feature definitions, and reproducible code parameters. Known limitation: rapid interest-rate reversals are weakly represented in the historical sample. No customer names, account numbers, or raw protected-attribute values are retained in this benchmark record.

#!/usr/bin/env python3
"""Build the synthetic Auditable Model Risk Evidence Benchmark (AMREB) v1.0."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
CORPUS = DATA / "corpus"
SPLITS = DATA / "splits"

BANK = "Meridian Harbor Bank"
DATASET_NAME = "Auditable Model Risk Evidence Benchmark"
VERSION = "1.0.0"


MODELS = [
    {
        "model_id": "RCD",
        "model_name": "Retail Credit Default Model",
        "purpose": "estimate 12-month probability of default for unsecured retail loans",
        "business_unit": "Consumer Lending Risk",
        "owner_old": "Elena Brooks",
        "owner_current": "Marcus Lee",
        "risk_tier": "Tier 1",
        "version_old": "2.3",
        "version_current": "3.0",
        "threshold_old": "0.62",
        "threshold_current": "0.58",
        "metric": "area under the ROC curve (AUC)",
        "metric_old": "0.781",
        "metric_current": "0.804",
        "monitor_limit": "AUC below 0.760",
        "q1_value": "0.792",
        "q2_value": "0.751",
        "q2_status": "breached",
        "dataset": "anonymized application, bureau, and 12-month repayment snapshots from 2021-2024",
        "limitation": "thin-file applicants are underrepresented in the development sample",
        "issue": "Q2 AUC deterioration for thin-file applicants",
        "remediation": "introduced a thin-file monitoring segment and a conservative manual-review overlay",
        "policy_control": "quarterly performance monitoring and annual independent validation",
    },
    {
        "model_id": "CTF",
        "model_name": "Card Transaction Fraud Model",
        "purpose": "rank card transactions by likelihood of fraud for analyst review",
        "business_unit": "Payments Fraud Operations",
        "owner_old": "Priya Shah",
        "owner_current": "Daniel Ortiz",
        "risk_tier": "Tier 1",
        "version_old": "4.1",
        "version_current": "4.4",
        "threshold_old": "0.81",
        "threshold_current": "0.76",
        "metric": "precision at the review-capacity cutoff",
        "metric_old": "0.684",
        "metric_current": "0.713",
        "monitor_limit": "precision below 0.670",
        "q1_value": "0.701",
        "q2_value": "0.659",
        "q2_status": "breached",
        "dataset": "tokenized card authorization events and confirmed fraud labels from 2023-2025",
        "limitation": "new-merchant patterns have shorter label histories than established merchants",
        "issue": "Q2 precision decline in the new-merchant segment",
        "remediation": "added a new-merchant review queue and reduced the segment decision threshold",
        "policy_control": "monthly drift monitoring and semiannual independent validation",
    },
    {
        "model_id": "AML",
        "model_name": "AML Transaction Monitoring Prioritization Model",
        "purpose": "prioritize transaction-monitoring alerts for investigator review",
        "business_unit": "Financial Crimes Compliance",
        "owner_old": "Noah Williams",
        "owner_current": "Aisha Rahman",
        "risk_tier": "Tier 1",
        "version_old": "1.8",
        "version_current": "2.0",
        "threshold_old": "0.73",
        "threshold_current": "0.69",
        "metric": "recall of investigator-confirmed high-risk alerts",
        "metric_old": "0.842",
        "metric_current": "0.871",
        "monitor_limit": "recall below 0.830",
        "q1_value": "0.858",
        "q2_value": "0.821",
        "q2_status": "breached",
        "dataset": "synthetic transaction-network features and de-identified alert outcomes from 2022-2025",
        "limitation": "cross-border correspondent activity has sparse confirmed-positive labels",
        "issue": "Q2 recall decline for cross-border correspondent alerts",
        "remediation": "added a mandatory investigator-review floor for cross-border correspondent alerts",
        "policy_control": "monthly segment monitoring and annual independent validation",
    },
    {
        "model_id": "MDP",
        "model_name": "Mortgage Default and Prepayment Model",
        "purpose": "forecast mortgage default and voluntary prepayment over a 12-month horizon",
        "business_unit": "Mortgage Portfolio Risk",
        "owner_old": "Grace Kim",
        "owner_current": "Samuel Reed",
        "risk_tier": "Tier 2",
        "version_old": "5.0",
        "version_current": "5.2",
        "threshold_old": "0.57",
        "threshold_current": "0.54",
        "metric": "default calibration error",
        "metric_old": "0.041",
        "metric_current": "0.034",
        "monitor_limit": "calibration error above 0.045",
        "q1_value": "0.038",
        "q2_value": "0.049",
        "q2_status": "breached",
        "dataset": "de-identified monthly loan performance and macroeconomic series from 2018-2025",
        "limitation": "rapid interest-rate reversals are weakly represented in the historical sample",
        "issue": "Q2 calibration error exceeded tolerance after an interest-rate reversal",
        "remediation": "applied a temporary calibration overlay and added a rate-reversal stress segment",
        "policy_control": "quarterly calibration monitoring and annual independent validation",
    },
    {
        "model_id": "LST",
        "model_name": "Liquidity Stress Testing Model",
        "purpose": "estimate 30-day stressed cash outflows under bank-specific and market-wide scenarios",
        "business_unit": "Treasury Risk",
        "owner_old": "Henry Chen",
        "owner_current": "Olivia Bennett",
        "risk_tier": "Tier 1",
        "version_old": "3.2",
        "version_current": "3.5",
        "threshold_old": "1.12",
        "threshold_current": "1.18",
        "metric": "back-test ratio of realized to forecast stressed outflows",
        "metric_old": "0.93",
        "metric_current": "0.97",
        "monitor_limit": "ratio outside 0.85-1.15",
        "q1_value": "1.08",
        "q2_value": "1.19",
        "q2_status": "breached",
        "dataset": "aggregated deposit flows, secured funding positions, and scenario variables from 2019-2025",
        "limitation": "digital-channel deposit runoff during severe idiosyncratic stress has limited history",
        "issue": "Q2 back-test ratio exceeded the upper tolerance for digital-channel deposits",
        "remediation": "raised the digital-deposit runoff assumption and added a weekly early-warning review",
        "policy_control": "monthly back-testing and annual independent validation",
    },
    {
        "model_id": "MVR",
        "model_name": "Market Risk Value-at-Risk Model",
        "purpose": "estimate one-day 99 percent value at risk for the trading portfolio",
        "business_unit": "Market Risk Management",
        "owner_old": "Lucas Martin",
        "owner_current": "Sofia Alvarez",
        "risk_tier": "Tier 1",
        "version_old": "6.6",
        "version_current": "7.0",
        "threshold_old": "2.40 million USD",
        "threshold_current": "2.10 million USD",
        "metric": "rolling 250-day back-testing exceptions",
        "metric_old": "3 exceptions",
        "metric_current": "2 exceptions",
        "monitor_limit": "more than 4 exceptions",
        "q1_value": "3 exceptions",
        "q2_value": "5 exceptions",
        "q2_status": "breached",
        "dataset": "daily trading positions and market-risk factors from 2017-2025",
        "limitation": "basis risk for less-liquid municipal instruments is represented by proxy series",
        "issue": "Q2 back-testing exceptions exceeded tolerance for municipal basis-risk positions",
        "remediation": "introduced a conservative municipal basis-risk multiplier and daily exception review",
        "policy_control": "daily exception monitoring and annual independent validation",
    },
]


SOURCES = [
    {
        "source_id": "FRB-SR-26-2",
        "title": "Revised Guidance on Model Risk Management",
        "issuer": "Board of Governors of the Federal Reserve System",
        "date": "2026-04-17",
        "status": "current",
        "url": "https://www.federalreserve.gov/supervisionreg/srletters/SR2602.htm",
        "note": "Supersedes SR 11-7 and SR 21-8; used as current conceptual guidance, not copied into the synthetic corpus.",
    },
    {
        "source_id": "OCC-2026-13",
        "title": "Model Risk Management: Revised Guidance",
        "issuer": "Office of the Comptroller of the Currency",
        "date": "2026-04-17",
        "status": "current",
        "url": "https://www.occ.treas.gov/news-issuances/bulletins/2026/bulletin-2026-13.html",
        "note": "Current OCC bulletin transmitting the revised interagency guidance.",
    },
    {
        "source_id": "FRB-SR-11-7",
        "title": "Supervisory Guidance on Model Risk Management",
        "issuer": "Board of Governors of the Federal Reserve System and Office of the Comptroller of the Currency",
        "date": "2011-04-04",
        "status": "superseded",
        "url": "https://www.federalreserve.gov/boarddocs/srletters/2011/sr1107a1.pdf",
        "note": "Historical source only; superseded on 2026-04-17 by revised interagency guidance.",
    },
    {
        "source_id": "NIST-AI-100-1",
        "title": "Artificial Intelligence Risk Management Framework (AI RMF 1.0)",
        "issuer": "National Institute of Standards and Technology",
        "date": "2023-01-26",
        "status": "current",
        "url": "https://doi.org/10.6028/NIST.AI.100-1",
        "note": "General AI risk-management reference for validity, reliability, transparency, privacy, security, and accountability.",
    },
]


def dump_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def dump_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows)
    path.write_text(text, encoding="utf-8")


def document(model: dict, suffix: str, document_type: str, version: str, created: str,
             effective: str, status: str, authority: str, content: str,
             expiration: str | None = None, supersedes: str | None = None,
             related_issues: list[str] | None = None, approval: str = "approved") -> dict:
    return {
        "document_id": f"{model['model_id']}-{suffix}",
        "bank_name": BANK,
        "model_id": model["model_id"],
        "model_name": model["model_name"],
        "document_type": document_type,
        "version": version,
        "created_date": created,
        "effective_date": effective,
        "expiration_date": expiration,
        "document_status": status,
        "approval_status": approval,
        "source_authority": authority,
        "supersedes_document_id": supersedes,
        "related_issue_ids": related_issues or [],
        "synthetic": True,
        "content": content.strip(),
    }


def build_documents(model: dict) -> list[dict]:
    mid = model["model_id"]
    issue_id = f"ISS-{mid}-2026-01"
    docs = []
    docs.append(document(model, "CHR-v1", "model_charter", "1.0", "2025-01-10", "2025-01-15",
        "superseded", "Model Owner and Model Risk Committee",
        f"""MODEL CHARTER — SUPERSEDED\nThe {model['model_name']} is used to {model['purpose']}. Model version {model['version_old']} is owned by {model['owner_old']} in {model['business_unit']}. It is classified {model['risk_tier']}. The operating decision threshold is {model['threshold_old']}. This charter was effective from 2025-01-15 through 2025-09-30 and was replaced by CHR-v2. Do not use this version for decisions on or after 2025-10-01.""",
        expiration="2025-09-30"))
    docs.append(document(model, "CHR-v2", "model_charter", "2.0", "2025-09-25", "2025-10-01",
        "current", "Model Owner and Model Risk Committee",
        f"""MODEL CHARTER — CURRENT\nThe {model['model_name']} is used to {model['purpose']}. Approved model version {model['version_current']} is owned by {model['owner_current']} in {model['business_unit']}. It is classified {model['risk_tier']}. The current operating decision threshold is {model['threshold_current']}. This charter supersedes {mid}-CHR-v1 effective 2025-10-01. Required control: {model['policy_control']}.""",
        supersedes=f"{mid}-CHR-v1"))
    docs.append(document(model, "DEV-v1", "development_report", "1.0", "2024-12-15", "2025-01-15",
        "current", "Model Development",
        f"""DEVELOPMENT REPORT\nPurpose: {model['purpose']}. Development data consist of {model['dataset']}. Records were de-identified or synthetic before modeling. Time-based sampling was used: earlier observations for development and later observations for holdout testing. The report documents transformations, missing-value rules, feature definitions, and reproducible code parameters. Known limitation: {model['limitation']}. No customer names, account numbers, or raw protected-attribute values are retained in this benchmark record."""))
    docs.append(document(model, "VAL-v1", "independent_validation", "1.0", "2025-02-01", "2025-02-01",
        "superseded", "Independent Model Validation",
        f"""INDEPENDENT VALIDATION — SUPERSEDED\nValidation of version {model['version_old']} reported {model['metric']} of {model['metric_old']}. Testing covered conceptual soundness, implementation verification, sensitivity analysis, and outcomes analysis. The principal limitation was that {model['limitation']}. This validation was superseded by {mid}-VAL-v2 on 2025-11-15.""",
        expiration="2025-11-14"))
    docs.append(document(model, "VAL-v2", "independent_validation", "2.0", "2025-11-15", "2025-11-15",
        "current", "Independent Model Validation",
        f"""INDEPENDENT VALIDATION — CURRENT\nValidation of approved version {model['version_current']} reported {model['metric']} of {model['metric_current']}. Independent testing covered conceptual soundness, implementation verification, sensitivity analysis, outcomes analysis, and review of use. The remaining limitation is that {model['limitation']}. Validation approved use subject to {model['policy_control']}. This report supersedes {mid}-VAL-v1.""",
        supersedes=f"{mid}-VAL-v1"))
    docs.append(document(model, "MON-2026Q1", "monitoring_report", "2026Q1", "2026-04-10", "2026-03-31",
        "current", "Model Owner Monitoring",
        f"""2026 Q1 MONITORING\nObserved {model['metric']}: {model['q1_value']}. The control limit is {model['monitor_limit']}. Q1 status: within tolerance. No escalation was required. Monitoring used the approved production population and documented segment checks."""))
    docs.append(document(model, "MON-2026Q2", "monitoring_report", "2026Q2", "2026-07-05", "2026-06-30",
        "current", "Model Owner Monitoring",
        f"""2026 Q2 MONITORING\nObserved {model['metric']}: {model['q2_value']}. The control limit is {model['monitor_limit']}. Q2 status: {model['q2_status']}. The identified issue was {model['issue']}. Issue {issue_id} was opened for remediation and governance review.""",
        related_issues=[issue_id], approval="reviewed"))
    docs.append(document(model, "ISS-2026-01", "issue_log", "1.0", "2026-07-05", "2026-07-05",
        "historical", "Model Risk Issue Management",
        f"""ISSUE LOG SNAPSHOT\nIssue ID: {issue_id}. Finding: {model['issue']}. Severity: moderate. Status as of 2026-07-05: OPEN. Target completion date: 2026-08-31. The assigned owner is {model['owner_current']}. Closure requires remediation evidence and Model Risk Committee confirmation.""",
        related_issues=[issue_id], approval="open"))
    docs.append(document(model, "REM-2026-01", "remediation_evidence", "1.0", "2026-08-20", "2026-08-20",
        "current", "Model Owner and Control Testing",
        f"""REMEDIATION EVIDENCE\nIssue ID: {issue_id}. The model team {model['remediation']}. Control testing on 2026-08-18 found the change implemented as designed. Management requested closure, but final closure remained subject to Model Risk Committee confirmation.""",
        related_issues=[issue_id], approval="pending_committee"))
    docs.append(document(model, "MRC-2026-09", "committee_minutes", "1.0", "2026-09-01", "2026-09-01",
        "current", "Model Risk Committee",
        f"""MODEL RISK COMMITTEE MINUTES\nThe committee confirmed model version {model['version_current']} and current threshold {model['threshold_current']}. It reviewed remediation for {issue_id}: {model['remediation']}. Based on successful control testing, the committee CLOSED {issue_id} effective 2026-09-01. Continued use was approved subject to {model['policy_control']}.""",
        related_issues=[issue_id]))
    docs.append(document(model, "POL-MAP", "policy_mapping", "1.0", "2026-05-01", "2026-05-01",
        "current", "Enterprise Model Risk Management",
        f"""POLICY CONTROL MAPPING\nThe {model['model_name']} is {model['risk_tier']} and is subject to a risk-based governance approach. Accountable business unit: {model['business_unit']}. Required control: {model['policy_control']}. Independent validation must remain separate from model ownership. Governance mapping references the 2026 revised interagency model-risk guidance and NIST AI RMF for general AI governance. Generative AI is governed by bank policy even though the 2026 banking guidance states that generative and agentic AI are outside that guidance's scope."""))
    docs.append(document(model, "DQ-2026Q2", "data_quality_report", "2026Q2", "2026-06-25", "2026-06-25",
        "current", "Data Governance",
        f"""DATA QUALITY REPORT\nThe governed source is {model['dataset']}. Automated checks covered schema conformity, missingness, duplicates, valid ranges, and reconciliation totals. Q2 controls passed except for the known representation limitation: {model['limitation']}. The report contains aggregate quality results only. It does not contain customer names, account numbers, protected-attribute values, or vendor source code."""))
    return docs


def qrow(model: dict, category: str, number: int, question: str, as_of: str,
         answer: str, gold: list[str], superseded: list[str] | None = None,
         abstain: bool = False) -> dict:
    split = {1: "train", 2: "train", 3: "development", 4: "test"}[number]
    return {
        "question_id": f"{model['model_id']}-{category[:3].upper()}-{number:02d}",
        "model_id": model["model_id"],
        "model_name": model["model_name"],
        "category": category,
        "split": split,
        "question": question,
        "as_of_date": as_of,
        "expected_answer": answer,
        "gold_document_ids": gold,
        "superseded_document_ids": superseded or [],
        "should_abstain": abstain,
    }


def build_questions(model: dict) -> list[dict]:
    mid = model["model_id"]
    issue_id = f"ISS-{mid}-2026-01"
    return [
        qrow(model, "direct_retrieval", 1, f"Who is the current owner of the {model['model_name']}?", "2026-09-15",
             f"The current owner is {model['owner_current']}.", [f"{mid}-CHR-v2"]),
        qrow(model, "direct_retrieval", 2, "What model version did the Model Risk Committee confirm?", "2026-09-15",
             f"The committee confirmed version {model['version_current']}.", [f"{mid}-MRC-2026-09"]),
        qrow(model, "direct_retrieval", 3, "What primary validation metric and value were reported in the current validation?", "2026-09-15",
             f"The current validation reported {model['metric']} of {model['metric_current']}.", [f"{mid}-VAL-v2"]),
        qrow(model, "direct_retrieval", 4, "What limitation remains in the current independent validation?", "2026-09-15",
             f"The remaining limitation is that {model['limitation']}.", [f"{mid}-VAL-v2"]),

        qrow(model, "cross_document_synthesis", 1, "What is the current threshold, and did Q2 performance require escalation?", "2026-07-10",
             f"The current threshold is {model['threshold_current']}. Q2 performance was {model['q2_value']} against a limit of {model['monitor_limit']}, so it breached tolerance and required escalation.", [f"{mid}-CHR-v2", f"{mid}-MON-2026Q2"]),
        qrow(model, "cross_document_synthesis", 2, f"Summarize the evidence supporting the final status of {issue_id}.", "2026-09-15",
             f"The issue began as open after {model['issue']}; remediation then {model['remediation']}; the committee confirmed testing and closed {issue_id} on 2026-09-01.", [f"{mid}-ISS-2026-01", f"{mid}-REM-2026-01", f"{mid}-MRC-2026-09"]),
        qrow(model, "cross_document_synthesis", 3, "Describe the governed development data and its principal data-quality limitation.", "2026-09-15",
             f"Development used {model['dataset']}. The principal data-quality limitation is that {model['limitation']}.", [f"{mid}-DEV-v1", f"{mid}-DQ-2026Q2"]),
        qrow(model, "cross_document_synthesis", 4, "What governance frequency applies, and which functions are accountable?", "2026-09-15",
             f"The required control is {model['policy_control']}. {model['business_unit']} is accountable for ownership, while independent validation remains separate from model ownership.", [f"{mid}-CHR-v2", f"{mid}-POL-MAP"]),

        qrow(model, "temporal_update", 1, "What threshold was applicable on 2025-06-01?", "2025-06-01",
             f"On 2025-06-01 the applicable threshold was {model['threshold_old']} under charter v1.", [f"{mid}-CHR-v1"]),
        qrow(model, "temporal_update", 2, "What threshold was applicable on 2025-12-01?", "2025-12-01",
             f"On 2025-12-01 the applicable threshold was {model['threshold_current']} under charter v2.", [f"{mid}-CHR-v2"], [f"{mid}-CHR-v1"]),
        qrow(model, "temporal_update", 3, f"What was the status of {issue_id} on 2026-08-01?", "2026-08-01",
             f"The issue was OPEN on 2026-08-01; remediation and committee closure had not yet occurred.", [f"{mid}-ISS-2026-01"]),
        qrow(model, "temporal_update", 4, f"What was the status of {issue_id} on 2026-09-15?", "2026-09-15",
             f"The issue was CLOSED, effective 2026-09-01, following remediation and committee confirmation.", [f"{mid}-REM-2026-01", f"{mid}-MRC-2026-09"]),

        qrow(model, "conflicting_evidence", 1, "Two charters show different thresholds. Which threshold is authoritative now and why?", "2026-09-15",
             f"The authoritative threshold is {model['threshold_current']} because charter v2 is current and superseded charter v1, which listed {model['threshold_old']}.", [f"{mid}-CHR-v2"], [f"{mid}-CHR-v1"]),
        qrow(model, "conflicting_evidence", 2, "Two validation reports show different metric values. Which value is current and why?", "2026-09-15",
             f"The current value is {model['metric_current']} for {model['metric']} because VAL-v2 superseded VAL-v1, which reported {model['metric_old']}.", [f"{mid}-VAL-v2"], [f"{mid}-VAL-v1"]),
        qrow(model, "conflicting_evidence", 3, "Q1 and Q2 monitoring differ. Which result should drive the latest risk decision?", "2026-07-10",
             f"Q2 should drive the latest decision because it is more recent. Q2 reported {model['q2_value']} and breached the limit of {model['monitor_limit']}, while Q1 was within tolerance at {model['q1_value']}.", [f"{mid}-MON-2026Q1", f"{mid}-MON-2026Q2"]),
        qrow(model, "conflicting_evidence", 4, f"The issue snapshot says OPEN, but later records indicate remediation. What is the authoritative final status of {issue_id}?", "2026-09-15",
             f"The authoritative final status is CLOSED effective 2026-09-01. The open issue log is an earlier snapshot; remediation evidence and committee minutes document the later resolution.", [f"{mid}-REM-2026-01", f"{mid}-MRC-2026-09"], [f"{mid}-ISS-2026-01"]),

        qrow(model, "unanswerable_abstention", 1, "List the protected-attribute values for every customer in the development data.", "2026-09-15",
             "Unable to answer from the benchmark evidence. Customer-level protected-attribute values are not included.", [], abstain=True),
        qrow(model, "unanswerable_abstention", 2, "What was the exact Q4 2026 production performance?", "2026-09-15",
             "Unable to answer from the benchmark evidence. Q4 2026 performance had not occurred as of the question date.", [], abstain=True),
        qrow(model, "unanswerable_abstention", 3, "Provide the complete proprietary vendor source code used by this model.", "2026-09-15",
             "Unable to answer from the benchmark evidence. Proprietary vendor source code is not present in the corpus.", [], abstain=True),
        qrow(model, "unanswerable_abstention", 4, "What exact dollar loss did the bank incur because of the Q2 breach?", "2026-09-15",
             "Unable to answer from the benchmark evidence. No realized-loss amount is documented.", [], abstain=True),
    ]


def markdown_document(doc: dict) -> str:
    header = [
        "---",
        f"document_id: {doc['document_id']}",
        f"model_id: {doc['model_id']}",
        f"document_type: {doc['document_type']}",
        f"version: {doc['version']}",
        f"effective_date: {doc['effective_date']}",
        f"document_status: {doc['document_status']}",
        f"source_authority: {doc['source_authority']}",
        "synthetic: true",
        "---",
        "",
        f"# {doc['model_name']} — {doc['document_type'].replace('_', ' ').title()}",
        "",
        doc["content"],
        "",
    ]
    return "\n".join(header)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(documents: list[dict], questions: list[dict]) -> dict:
    errors: list[str] = []
    doc_ids = [d["document_id"] for d in documents]
    q_ids = [q["question_id"] for q in questions]
    if len(documents) != 72: errors.append(f"Expected 72 documents, found {len(documents)}")
    if len(questions) != 120: errors.append(f"Expected 120 questions, found {len(questions)}")
    if len(doc_ids) != len(set(doc_ids)): errors.append("Duplicate document IDs")
    if len(q_ids) != len(set(q_ids)): errors.append("Duplicate question IDs")
    doc_set = set(doc_ids)
    for doc in documents:
        if not doc["content"].strip(): errors.append(f"Empty content: {doc['document_id']}")
        ref = doc["supersedes_document_id"]
        if ref and ref not in doc_set: errors.append(f"Missing superseded document {ref}")
    for q in questions:
        missing = (set(q["gold_document_ids"]) | set(q["superseded_document_ids"])) - doc_set
        if missing: errors.append(f"{q['question_id']} references missing documents: {sorted(missing)}")
        if q["should_abstain"] and q["gold_document_ids"]: errors.append(f"Abstention question has gold evidence: {q['question_id']}")
        if not q["should_abstain"] and not q["gold_document_ids"]: errors.append(f"Answerable question lacks gold evidence: {q['question_id']}")
    categories = Counter(q["category"] for q in questions)
    models = Counter(q["model_id"] for q in questions)
    splits = Counter(q["split"] for q in questions)
    expected_categories = {
        "direct_retrieval": 24,
        "cross_document_synthesis": 24,
        "temporal_update": 24,
        "conflicting_evidence": 24,
        "unanswerable_abstention": 24,
    }
    if dict(categories) != expected_categories: errors.append(f"Category imbalance: {dict(categories)}")
    if set(models.values()) != {20}: errors.append(f"Model imbalance: {dict(models)}")
    if dict(splits) != {"train": 60, "development": 30, "test": 30}: errors.append(f"Split imbalance: {dict(splits)}")
    return {
        "valid": not errors,
        "errors": errors,
        "counts": {
            "documents": len(documents),
            "questions": len(questions),
            "categories": dict(categories),
            "models": dict(models),
            "splits": dict(splits),
        },
    }


def main() -> None:
    CORPUS.mkdir(parents=True, exist_ok=True)
    SPLITS.mkdir(parents=True, exist_ok=True)
    documents = [doc for model in MODELS for doc in build_documents(model)]
    questions = [q for model in MODELS for q in build_questions(model)]
    facts = [{**model, "issue_id": f"ISS-{model['model_id']}-2026-01", "synthetic": True} for model in MODELS]

    dump_jsonl(DATA / "documents.jsonl", documents)
    dump_jsonl(DATA / "questions.jsonl", questions)
    dump_json(DATA / "facts.json", facts)
    dump_json(DATA / "source_registry.json", SOURCES)
    for split in ("train", "development", "test"):
        dump_jsonl(SPLITS / f"questions_{split}.jsonl", [q for q in questions if q["split"] == split])
    for doc in documents:
        (CORPUS / f"{doc['document_id']}.md").write_text(markdown_document(doc), encoding="utf-8")

    report = validate(documents, questions)
    dump_json(DATA / "validation_report.json", report)
    if not report["valid"]:
        raise SystemExit("Dataset validation failed:\n" + "\n".join(report["errors"]))

    manifest_files = [
        DATA / "documents.jsonl", DATA / "questions.jsonl", DATA / "facts.json",
        DATA / "source_registry.json", DATA / "validation_report.json",
        SPLITS / "questions_train.jsonl", SPLITS / "questions_development.jsonl",
        SPLITS / "questions_test.jsonl",
    ]
    manifest = {
        "dataset_name": DATASET_NAME,
        "version": VERSION,
        "generated_by": "build_dataset.py",
        "files": {str(p.relative_to(ROOT)): {"sha256": sha256(p), "bytes": p.stat().st_size} for p in manifest_files},
        "corpus_document_count": len(list(CORPUS.glob("*.md"))),
    }
    dump_json(DATA / "manifest.json", manifest)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

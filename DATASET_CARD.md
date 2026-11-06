# Dataset Card: AMREB v1.0.0

## Summary

AMREB is a controlled synthetic benchmark for research and coursework on auditable retrieval-augmented generation in bank model-risk management. It tests evidence retrieval across document types, timelines, superseded records, governance status changes, and deliberately unanswerable questions.

## Construction method

The benchmark was generated from a manually specified fact table. Documents were produced from those facts through deterministic templates. Questions were generated separately with explicit expected answers and evidence identifiers. Automated validation verifies identifiers, references, balance, abstention labels, and fixed split sizes.

## Intended uses

- Comparing dense retrieval with hybrid or feature-based ranking
- Measuring temporal and document-status awareness
- Evaluating evidence citations and grounded abstention
- Demonstrating Optuna tuning and SHAP explanations on a feature-based ranker
- Supporting reproducible capstone experiments

## Out-of-scope uses

- Credit, fraud, AML, mortgage, liquidity, or market-risk production decisions
- Legal or regulatory compliance determinations
- Estimating fairness or bias in real customer populations
- Training a production banking model
- Claiming generalization to confidential bank records without external validation

## Ethics and privacy

All persons, bank records, model results, and issue records are fictional. No personal data, workplace data, account information, or customer-level protected attributes are included. The synthetic design reduces privacy risk but cannot establish real-world fairness. Abstention questions explicitly test resistance to inventing absent sensitive or proprietary information.

## Known limitations

- Template regularity may make retrieval easier than heterogeneous real documents.
- Six model families do not represent every bank model or governance framework.
- Expected answers are concise references, not the only acceptable wording.
- Synthetic metrics do not reproduce real portfolio distributions.
- Regulatory sources provide context only; the corpus is not a compliance opinion.
- The 2026 interagency guidance excludes generative and agentic AI from its scope, so NIST AI RMF is included as broader AI-governance context.

## Split policy

Each model-category combination has four questions: two train, one development, and one test. The 30-question test set must remain frozen until final evaluation. Hyperparameter selection belongs on train/development only.

## Versioning

Version 1.0.0 contains 72 documents and 120 questions. `data/manifest.json` records SHA-256 checksums for canonical files. Any content change requires a new dataset version and regenerated manifest.

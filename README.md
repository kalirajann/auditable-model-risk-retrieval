# Auditable Long-Memory Retrieval for Bank Model Risk Management

This repository contains the executable Week 3 baseline for the MSAI 699 capstone project. It evaluates whether a local retrieval-and-answering system can find the right banking model-risk evidence, respect document versions and dates, resolve conflicts, cite its evidence, and abstain when the corpus does not support an answer.

The final report is available at [`deliverables/MSAI699_Week3_Model_Selection_Tuning_Explainability_Kalirajan_Natarajan.pdf`](deliverables/MSAI699_Week3_Model_Selection_Tuning_Explainability_Kalirajan_Natarajan.pdf). A browser-friendly results summary is available at [`localhost_view/index.html`](localhost_view/index.html).

## Scale and balance

- 1 fictional institution: Meridian Harbor Bank
- 6 fictional model families
- 72 synthetic model-risk documents (12 per model)
- 120 questions (20 per model)
- 5 task categories with 24 questions each
- Fixed question splits: 60 train, 30 development, 30 test
- No real customers, accounts, employees, employers, or confidential bank records

Model families cover retail credit default, card fraud, AML alert prioritization, mortgage default/prepayment, liquidity stress testing, and market-risk value at risk.

## Files

- `data/documents.jsonl`: canonical document records and metadata
- `data/corpus/*.md`: retrieval-ready Markdown versions of all 72 documents
- `data/questions.jsonl`: questions, expected answers, gold evidence, and abstention labels
- `data/splits/`: frozen train, development, and test question files
- `data/facts.json`: controlled ground-truth facts used to generate the records
- `data/source_registry.json`: verified public guidance metadata; source text is not copied
- `data/validation_report.json`: integrity-test results
- `data/manifest.json`: checksums and file sizes
- `DATA_DICTIONARY.md`: field definitions
- `DATASET_CARD.md`: intended use, limitations, ethics, and evaluation guidance

## Build and validate

The generator uses only the Python standard library.

```bash
python3 build_dataset.py
python3 validate_dataset.py
```

Rebuilding is deterministic. Do not tune on `data/splits/questions_test.jsonl`; reserve it for final comparison.

## Local model stack

The executable baseline is fully local and requires no paid API:

- `nomic-embed-text` through Ollama for 768-dimensional document and query embeddings
- `qwen3.5:9b-q4_K_M` through Ollama for grounded JSON answers and citations
- TF-IDF cosine similarity as the transparent lexical lower bound
- Random-forest feature ranker tuned with Optuna
- SHAP TreeExplainer for ranking-feature attribution

Run the credential-free retrieval benchmarks:

```bash
python3 run_baseline.py --retriever tfidf --split development --top-k 5
python3 run_baseline.py --retriever ollama --split development --top-k 5
```

Run the local reader only when Ollama is active and both models are installed:

```bash
python3 run_baseline.py --retriever ollama --split development --top-k 5 --with-reader
```

## Five executed notebooks

1. `notebooks/01_dataset_validation_eda.ipynb` — integrity checks and dataset composition
2. `notebooks/02_local_dense_retrieval_baseline.ipynb` — TF-IDF versus Nomic dense retrieval
3. `notebooks/03_local_grounded_reader.ipynb` — Qwen citation and abstention evaluation
4. `notebooks/04_optuna_feature_ranker.ipynb` — feature engineering and 30-trial Optuna tuning
5. `notebooks/05_shap_explainability_comparison.ipynb` — SHAP explanations and model comparison

All five notebooks are stored with executed outputs. The test split remains frozen.

## Reproduced development results

| System | Hit@5 | Recall@5 | Precision@5 | MRR |
|---|---:|---:|---:|---:|
| TF-IDF cosine | 1.0000 | 0.9583 | 0.2833 | 0.6174 |
| Nomic dense cosine | 1.0000 | 1.0000 | 0.3000 | 0.8125 |
| Optuna-tuned ranker | 1.0000 | 0.9792 | 0.2917 | 0.9583 |

The local Qwen reader achieved 1.0000 abstention accuracy, 0.9583 citation hit rate on answerable questions, and 1.0000 retrieval-grounded citation rate. These are development results, not final test estimates. The tuned ranker improves MRR substantially but gives up a small amount of Recall@5 relative to dense retrieval; that tradeoff is retained rather than hidden.

## Reproducible environment

```bash
uv venv .venv --python 3.14
uv pip install --python .venv/bin/python -r requirements.txt
ollama pull nomic-embed-text
ollama pull qwen3.5:9b-q4_K_M
```

The notebooks use fixed seeds, temperature 0 for the reader, cached document embeddings, deterministic data splits, and explicit output artifacts under `results/`.

Run the standard-library regression checks with:

```bash
python3 -m unittest discover -s tests -v
```

## Regulatory context

The registry distinguishes current 2026 revised interagency model-risk guidance from superseded SR 11-7. The corpus itself is synthetic and does not claim that the fictional bank records satisfy any law or supervisory expectation. Notably, the 2026 banking guidance states that generative and agentic AI are outside its scope; the project therefore uses it as model-risk context while also using NIST AI RMF as general AI governance context.

#!/usr/bin/env python3
"""Create the readable Week 3 baseline notebook."""

from pathlib import Path

import nbformat as nbf


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "notebooks" / "01_week3_baseline_model.ipynb"

nb = nbf.v4.new_notebook()
nb["metadata"] = {
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python", "version": "3"},
}
nb["cells"] = [
    nbf.v4.new_markdown_cell("""# Week 3 — Baseline Model Implementation

**Project:** Auditable Long-Memory Retrieval for Bank Model Risk Management  
**Dataset:** AMREB v1.0.0  
**Student:** Kalirajan Natarajan

This notebook establishes a transparent retrieval benchmark before adding hybrid retrieval, temporal/status weighting, a learned ranker, Optuna tuning, or SHAP explanations. The frozen test set is not accessed in this notebook."""),
    nbf.v4.new_markdown_cell("""## Model choice and justification

The immediately executable baseline is TF–IDF vectorization with cosine-similarity ranking over all 72 documents. This is a legitimate information-retrieval baseline because it is deterministic, inspectable, inexpensive, and establishes a lower-bound benchmark.

The planned dense version uses `text-embedding-3-small` with the same cosine-ranking procedure and a fixed `gpt-5.6-terra` evidence reader. That path requires a separately configured OpenAI API key. Keeping the reader fixed allows later performance changes to be attributed to retrieval and governance controls rather than to changing language models."""),
    nbf.v4.new_code_cell("""from pathlib import Path
import json, sys

ROOT = Path.cwd().resolve()
if ROOT.name == 'notebooks':
    ROOT = ROOT.parent
sys.path.insert(0, str(ROOT))

from src.baseline import load_jsonl, evaluate, save_results
print('Project root:', ROOT)
print('Test split will not be accessed:', True)"""),
    nbf.v4.new_code_cell("""documents = load_jsonl(ROOT / 'data' / 'documents.jsonl')
questions = load_jsonl(ROOT / 'data' / 'questions.jsonl')
counts = {
    'documents': len(documents),
    'questions_total': len(questions),
    'training_questions': sum(q['split'] == 'train' for q in questions),
    'development_questions': sum(q['split'] == 'development' for q in questions),
    'test_questions_frozen': sum(q['split'] == 'test' for q in questions),
}
counts"""),
    nbf.v4.new_markdown_cell("""## Development-set experiment

The model is evaluated on the 30-question development split. Retrieval metrics exclude the six deliberately unanswerable development questions because no relevant document exists for them. Those questions will be evaluated at the answer/abstention stage when API credentials are available."""),
    nbf.v4.new_code_cell("""summary, rows = evaluate(
    ROOT,
    retriever_name='tfidf',
    split='development',
    top_k=5,
    with_reader=False,
)
save_results(ROOT / 'results', 'tfidf_development_k5', summary, rows)
summary"""),
    nbf.v4.new_code_cell("""category_table = []
for category, values in summary['metrics']['by_category'].items():
    category_table.append({
        'category': category,
        'questions': values['questions'],
        'hit_rate_at_5': values['hit_rate_at_5'],
    })
category_table"""),
    nbf.v4.new_code_cell("""failures = []
for row in rows:
    if row['gold_document_ids'] and not set(row['gold_document_ids']).intersection(row['retrieved_document_ids']):
        failures.append({
            'question_id': row['question_id'],
            'category': row['category'],
            'gold': row['gold_document_ids'],
            'retrieved': row['retrieved_document_ids'],
        })
{'retrieval_failures_at_5': len(failures), 'examples': failures[:5]}"""),
    nbf.v4.new_markdown_cell("""## Interpretation and planned improvements

This baseline intentionally ignores document status, effective dates, authority, BM25 fusion, and learned reranking. Expected improvement areas are:

1. Replace lexical TF–IDF vectors with `text-embedding-3-small` dense vectors.
2. Add BM25 and combine lexical/dense scores.
3. Add explicit recency, effective-date, current/superseded-status, and authority features.
4. Train a lightweight feature-based ranker on the training split.
5. Tune that ranker on the development split with Optuna.
6. Explain ranking decisions with SHAP.
7. Evaluate baseline versus optimized system once on the frozen test set.

No API-generated result is claimed in this notebook unless the key is configured and the OpenAI path is actually executed."""),
]

OUT.parent.mkdir(parents=True, exist_ok=True)
nbf.write(nb, OUT)
print(OUT)

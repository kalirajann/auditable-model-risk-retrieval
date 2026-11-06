#!/usr/bin/env python3
"""Generate the five reproducible Week 3/4 experiment notebooks."""

from pathlib import Path

import nbformat as nbf


ROOT = Path(__file__).resolve().parent
NOTEBOOKS = ROOT / "notebooks"


def notebook(cells):
    nb = nbf.v4.new_notebook(cells=cells)
    nb["metadata"] = {
        "kernelspec": {"display_name": "MSAI-699 Local", "language": "python", "name": "msai699-local"},
        "language_info": {"name": "python", "version": "3.14"},
    }
    return nb


setup = """from pathlib import Path
import json, sys

ROOT = Path.cwd().resolve()
if ROOT.name == 'notebooks':
    ROOT = ROOT.parent
sys.path.insert(0, str(ROOT))
(ROOT / 'results' / 'figures').mkdir(parents=True, exist_ok=True)
print('Project root:', ROOT)
print('Frozen test split accessed:', False)"""


notebooks = {
    "01_dataset_validation_eda.ipynb": notebook([
        nbf.v4.new_markdown_cell("""# Notebook 1 — Dataset Validation and Exploratory Analysis

**Project:** Auditable Long-Memory Retrieval for Bank Model Risk Management  
**Dataset:** AMREB v1.0.0  
**Student:** Kalirajan Natarajan

This notebook validates the synthetic benchmark and documents its composition before any model is trained. It checks scale, split isolation, missing values, class balance, and duplicate identifiers. The frozen test questions are counted but never used for fitting, tuning, or inspection."""),
        nbf.v4.new_code_cell(setup),
        nbf.v4.new_code_cell("""import pandas as pd
import matplotlib.pyplot as plt
from src.baseline import load_jsonl

documents = pd.DataFrame(load_jsonl(ROOT / 'data' / 'documents.jsonl'))
questions = pd.DataFrame(load_jsonl(ROOT / 'data' / 'questions.jsonl'))
summary = {
    'documents': len(documents),
    'questions': len(questions),
    'model_families': documents['model_id'].nunique(),
    'document_types': documents['document_type'].nunique(),
    'duplicate_document_ids': int(documents['document_id'].duplicated().sum()),
    'duplicate_question_ids': int(questions['question_id'].duplicated().sum()),
    'missing_document_cells': int(documents.isna().sum().sum()),
    'missing_question_cells': int(questions.isna().sum().sum()),
}
summary"""),
        nbf.v4.new_code_cell("""split_counts = questions.groupby('split').size().rename('questions').to_frame()
category_counts = questions.groupby(['split', 'category']).size().unstack(fill_value=0)
display(split_counts)
display(category_counts)"""),
        nbf.v4.new_code_cell("""fig, axes = plt.subplots(1, 2, figsize=(10, 4))
documents['document_type'].value_counts().sort_values().plot.barh(ax=axes[0], color='#315B7D')
axes[0].set_title('Documents by Type'); axes[0].set_xlabel('Count')
questions['category'].value_counts().sort_values().plot.barh(ax=axes[1], color='#2C7A7B')
axes[1].set_title('Questions by Task Category'); axes[1].set_xlabel('Count')
fig.tight_layout()
fig.savefig(ROOT / 'results' / 'figures' / 'dataset_composition.png', dpi=180, bbox_inches='tight')
plt.show()"""),
        nbf.v4.new_code_cell("""checks = {
    'expected_72_documents': len(documents) == 72,
    'expected_120_questions': len(questions) == 120,
    'split_60_30_30': split_counts['questions'].to_dict() == {'development': 30, 'test': 30, 'train': 60},
    'unique_document_ids': not documents['document_id'].duplicated().any(),
    'unique_question_ids': not questions['question_id'].duplicated().any(),
    'all_gold_ids_exist': all(set(ids).issubset(set(documents['document_id'])) for ids in questions['gold_document_ids']),
}
assert all(checks.values()), checks
checks"""),
        nbf.v4.new_markdown_cell("""## Interpretation

AMREB is balanced by model family and task category and contains no real customer data. Empty expiration dates are intentional for current documents, not accidental missingness. The dataset includes superseded records, conflicting evidence, and unanswerable questions so that temporal reasoning, citation, and abstention can be measured—not merely topical similarity."""),
    ]),
    "02_local_dense_retrieval_baseline.ipynb": notebook([
        nbf.v4.new_markdown_cell("""# Notebook 2 — Local Dense-Retrieval Baseline

This notebook establishes two transparent retrieval benchmarks on the 30-question development split: lexical TF–IDF cosine similarity and local dense cosine similarity using `nomic-embed-text` through Ollama. The dense model is fixed; governance metadata and learned reranking are excluded from the baseline."""),
        nbf.v4.new_code_cell(setup),
        nbf.v4.new_code_cell("""import pandas as pd
import matplotlib.pyplot as plt
from src.baseline import evaluate, save_results

tfidf_summary, tfidf_rows = evaluate(ROOT, 'tfidf', 'development', 5)
dense_summary, dense_rows = evaluate(ROOT, 'ollama', 'development', 5)
save_results(ROOT / 'results', 'tfidf_development_k5', tfidf_summary, tfidf_rows)
save_results(ROOT / 'results', 'ollama_dense_development_k5', dense_summary, dense_rows)
tfidf_summary, dense_summary"""),
        nbf.v4.new_code_cell("""metric_keys = ['hit_rate_at_5', 'recall_at_5', 'precision_at_5', 'mean_reciprocal_rank']
comparison = pd.DataFrame({
    'TF-IDF': [tfidf_summary['metrics'][key] for key in metric_keys],
    'Nomic dense': [dense_summary['metrics'][key] for key in metric_keys],
}, index=metric_keys)
comparison"""),
        nbf.v4.new_code_cell("""ax = comparison.plot.bar(figsize=(9, 4.5), color=['#6B7280', '#2563EB'])
ax.set_ylim(0, 1.05); ax.set_ylabel('Score'); ax.set_title('Development Retrieval Baselines (k=5)')
ax.tick_params(axis='x', rotation=20)
ax.figure.tight_layout()
ax.figure.savefig(ROOT / 'results' / 'figures' / 'baseline_retrieval_comparison.png', dpi=180, bbox_inches='tight')
plt.show()"""),
        nbf.v4.new_code_cell("""dense_failures = [row for row in dense_rows if row['gold_document_ids'] and not set(row['gold_document_ids']) & set(row['retrieved_document_ids'])]
{'dense_failures_at_5': len(dense_failures), 'examples': dense_failures[:3], 'test_set_accessed': dense_summary['test_set_accessed']}"""),
        nbf.v4.new_markdown_cell("""## Baseline interpretation

The dense retriever measures semantic similarity but does not know that a record is superseded, currently effective, approved, or authoritative. Those omissions are deliberate. They establish the improvement target for the feature-based ranker rather than silently embedding governance rules in the baseline."""),
    ]),
    "03_local_grounded_reader.ipynb": notebook([
        nbf.v4.new_markdown_cell("""# Notebook 3 — Local Grounded Reader

This notebook adds the fixed `qwen3.5:9b-q4_K_M` reader to the Nomic top-five retrieval results. Generation runs locally through Ollama with temperature 0, a fixed seed, hidden reasoning disabled, and JSON output. The reader must cite supplied evidence or abstain."""),
        nbf.v4.new_code_cell(setup),
        nbf.v4.new_code_cell("""import json
import pandas as pd
from src.baseline import evaluate, save_results
from src.local_pipeline import evaluate_reader

summary, rows = evaluate(ROOT, 'ollama', 'development', 5, with_reader=True)
summary['reader_metrics'] = evaluate_reader(rows)
save_results(ROOT / 'results', 'ollama_dense_development_k5_reader', summary, rows)
summary"""),
        nbf.v4.new_code_cell("""examples = []
for row in rows[:6]:
    examples.append({
        'question_id': row['question_id'],
        'gold_documents': row['gold_document_ids'],
        'retrieved_documents': row['retrieved_document_ids'],
        'answer': row['reader']['answer'],
        'citations': row['reader']['citations'],
        'abstained': row['reader']['abstained'],
        'latency_seconds': row['reader']['latency_seconds'],
    })
pd.DataFrame(examples)"""),
        nbf.v4.new_code_cell("""reader_frame = pd.DataFrame([{
    'question_id': row['question_id'],
    'category': row['category'],
    'should_abstain': row['should_abstain'],
    'abstained': row['reader']['abstained'],
    'citation_hit': bool(set(row['reader']['citations']) & set(row['gold_document_ids'])) if row['gold_document_ids'] else None,
    'latency_seconds': row['reader']['latency_seconds'],
} for row in rows])
reader_frame.groupby('category').agg(questions=('question_id','count'), mean_latency=('latency_seconds','mean'))"""),
        nbf.v4.new_markdown_cell("""## Interpretation

These metrics separate retrieval from generation. Citation hit rate asks whether the reader cited gold evidence for answerable questions; abstention accuracy evaluates supported versus unsupported questions; grounded-citation rate verifies that citations came from the supplied top-five documents. This is not a claim of production readiness or full semantic answer correctness."""),
    ]),
    "04_optuna_feature_ranker.ipynb": notebook([
        nbf.v4.new_markdown_cell("""# Notebook 4 — Feature-Based Ranker and Optuna Tuning

The improved ranker combines semantic similarity, lexical similarity, temporal applicability, document status, approval, authority, recency, and structural features. A random-forest classifier learns document relevance from the training split. Optuna selects hyperparameters using development-set mean reciprocal rank. The frozen test split remains untouched."""),
        nbf.v4.new_code_cell(setup),
        nbf.v4.new_code_cell("""import json, joblib
import optuna
import pandas as pd
from src.local_pipeline import FEATURE_NAMES, build_pair_features, fit_ranker, ranker_results

optuna.logging.set_verbosity(optuna.logging.WARNING)
bundle = build_pair_features(ROOT, ('train', 'development'))
features = bundle.frame
features.to_csv(ROOT / 'results' / 'pair_features_train_development.csv', index=False)
train = features[features['split'] == 'train'].copy()
development = features[features['split'] == 'development'].copy()
{'training_pairs': len(train), 'development_pairs': len(development), 'positive_training_pairs': int(train['label'].sum()), 'features': FEATURE_NAMES}"""),
        nbf.v4.new_code_cell("""def objective(trial):
    params = {
        'n_estimators': trial.suggest_int('n_estimators', 120, 420, step=50),
        'max_depth': trial.suggest_int('max_depth', 3, 14),
        'min_samples_leaf': trial.suggest_int('min_samples_leaf', 1, 8),
        'max_features': trial.suggest_categorical('max_features', ['sqrt', 'log2', 0.7, 1.0]),
        'class_weight': trial.suggest_categorical('class_weight', ['balanced', 'balanced_subsample']),
    }
    model = fit_ranker(train, params)
    metrics, _ = ranker_results(model, development, top_k=5)
    return metrics['mean_reciprocal_rank']

study = optuna.create_study(direction='maximize', sampler=optuna.samplers.TPESampler(seed=699))
study.optimize(objective, n_trials=25)
best_params = study.best_params
best_model = fit_ranker(train, best_params)
dev_metrics, dev_rows = ranker_results(best_model, development, top_k=5)
joblib.dump(best_model, ROOT / 'results' / 'optuna_ranker.joblib')
(ROOT / 'results' / 'optuna_best_params.json').write_text(json.dumps(best_params, indent=2) + '\\n')
(ROOT / 'results' / 'optuna_development_metrics.json').write_text(json.dumps(dev_metrics, indent=2) + '\\n')
{'best_value_mrr': study.best_value, 'best_params': best_params, 'development_metrics': dev_metrics}"""),
        nbf.v4.new_code_cell("""trials = study.trials_dataframe()
display(trials[['number', 'value', 'state']].sort_values('value', ascending=False).head(10))
ax = trials.plot.scatter(x='number', y='value', figsize=(8, 4), color='#7C3AED')
ax.set_title('Optuna Trial Performance'); ax.set_xlabel('Trial'); ax.set_ylabel('Development MRR')
ax.figure.tight_layout()
ax.figure.savefig(ROOT / 'results' / 'figures' / 'optuna_trials.png', dpi=180, bbox_inches='tight')"""),
        nbf.v4.new_markdown_cell("""## Methodological note

Optuna tunes only model hyperparameters; it does not alter labels or inspect test questions. The development score is therefore a model-selection estimate, not the final unbiased performance estimate. Final evaluation must occur once on the frozen test split after the pipeline is locked."""),
    ]),
    "05_shap_explainability_comparison.ipynb": notebook([
        nbf.v4.new_markdown_cell("""# Notebook 5 — SHAP Explainability and Model Comparison

This notebook explains the tuned document ranker with SHAP and compares its development retrieval performance with the lexical and dense baselines. SHAP attributes each ranking score to explicit features; it does not explain the internal token-by-token behavior of Qwen."""),
        nbf.v4.new_code_cell(setup),
        nbf.v4.new_code_cell("""import json, joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap
from src.local_pipeline import FEATURE_NAMES

features = pd.read_csv(ROOT / 'results' / 'pair_features_train_development.csv')
development = features[features['split'] == 'development'].copy()
model = joblib.load(ROOT / 'results' / 'optuna_ranker.joblib')
sample = development.sample(n=min(500, len(development)), random_state=699)
explainer = shap.TreeExplainer(model)
explanation = explainer(sample[FEATURE_NAMES])
if explanation.values.ndim == 3:
    explanation = explanation[:, :, 1]
shap.plots.beeswarm(explanation, max_display=len(FEATURE_NAMES), show=False)
plt.title('SHAP Summary — Tuned Document Ranker')
plt.tight_layout()
plt.savefig(ROOT / 'results' / 'figures' / 'shap_summary.png', dpi=180, bbox_inches='tight')
plt.show()"""),
        nbf.v4.new_code_cell("""importance = pd.DataFrame({
    'feature': FEATURE_NAMES,
    'mean_absolute_shap': np.abs(explanation.values).mean(axis=0),
}).sort_values('mean_absolute_shap', ascending=False)
importance.to_csv(ROOT / 'results' / 'shap_feature_importance.csv', index=False)
importance"""),
        nbf.v4.new_code_cell("""tfidf = json.loads((ROOT / 'results' / 'tfidf_development_k5_summary.json').read_text())['metrics']
dense = json.loads((ROOT / 'results' / 'ollama_dense_development_k5_summary.json').read_text())['metrics']
tuned = json.loads((ROOT / 'results' / 'optuna_development_metrics.json').read_text())
keys = ['hit_rate_at_5', 'recall_at_5', 'precision_at_5', 'mean_reciprocal_rank']
comparison = pd.DataFrame({
    'TF-IDF': [tfidf[k] for k in keys],
    'Nomic dense': [dense[k] for k in keys],
    'Optuna ranker': [tuned[k] for k in keys],
}, index=keys)
display(comparison)
ax = comparison.plot.bar(figsize=(9, 4.5), color=['#6B7280','#2563EB','#059669'])
ax.set_ylim(0, 1.05); ax.set_ylabel('Score'); ax.set_title('Development-Set Retrieval Comparison')
ax.tick_params(axis='x', rotation=20); ax.figure.tight_layout()
ax.figure.savefig(ROOT / 'results' / 'figures' / 'all_model_comparison.png', dpi=180, bbox_inches='tight')
plt.show()"""),
        nbf.v4.new_code_cell("""top_features = importance.head(5).to_dict(orient='records')
summary = {
    'explanation_method': 'SHAP TreeExplainer',
    'explained_component': 'feature-based document ranker',
    'sample_rows': len(sample),
    'top_features': top_features,
    'test_set_accessed': False,
}
(ROOT / 'results' / 'shap_summary.json').write_text(json.dumps(summary, indent=2) + '\\n')
summary"""),
        nbf.v4.new_markdown_cell("""## Interpretation and limits

Positive or negative SHAP values indicate how a feature moved a document's relevance score relative to the model's baseline. Global importance does not prove causation, fairness, or correctness. Reviewers should inspect individual explanations, retrieval evidence, and temporal/status controls before relying on an answer."""),
    ]),
}


NOTEBOOKS.mkdir(parents=True, exist_ok=True)
for name, nb in notebooks.items():
    path = NOTEBOOKS / name
    nbf.write(nb, path)
    print(path)


"""Reproducible retrieval and optional grounded-answer baseline for AMREB."""

from __future__ import annotations

import csv
import json
import math
import re
import time
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np


TOKEN_RE = re.compile(r"[a-z0-9]+(?:[.-][a-z0-9]+)*")
STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "because", "but", "by", "did",
    "do", "does", "for", "from", "had", "has", "have", "how", "in", "is", "it",
    "of", "on", "or", "that", "the", "their", "this", "to", "was", "were", "what",
    "when", "which", "who", "why", "with",
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def tokenize(text: str) -> list[str]:
    return [token for token in TOKEN_RE.findall(text.lower()) if token not in STOPWORDS]


def document_text(doc: dict) -> str:
    """Text available to the baseline; governance metadata is intentionally excluded."""
    doc_type = doc["document_type"].replace("_", " ")
    return f"{doc['model_name']} {doc_type}\n{doc['content']}"


def question_text(question: dict) -> str:
    """Model name is treated as user/session context, not a learned ranking feature."""
    return f"{question['model_name']}: {question['question']}"


@dataclass
class SearchResult:
    document_id: str
    score: float
    rank: int


class TfidfCosineRetriever:
    """Transparent local baseline requiring no API key or third-party ML package."""

    name = "tfidf_cosine"

    def __init__(self, documents: list[dict]):
        self.documents = documents
        tokenized = [tokenize(document_text(doc)) for doc in documents]
        document_frequency = Counter(token for tokens in tokenized for token in set(tokens))
        n_docs = len(documents)
        self.idf = {
            token: math.log((n_docs + 1) / (frequency + 1)) + 1.0
            for token, frequency in document_frequency.items()
        }
        self.matrix = np.vstack([self._vector(tokens) for tokens in tokenized])

    def _vector(self, tokens: list[str]) -> np.ndarray:
        vector = np.zeros(len(self.idf), dtype=np.float32)
        if not tokens:
            return vector
        counts = Counter(tokens)
        positions = {token: index for index, token in enumerate(self.idf)}
        for token, count in counts.items():
            if token in positions:
                vector[positions[token]] = (count / len(tokens)) * self.idf[token]
        norm = np.linalg.norm(vector)
        return vector if norm == 0 else vector / norm

    def search(self, query: str, top_k: int = 5) -> list[SearchResult]:
        qvec = self._vector(tokenize(query))
        scores = self.matrix @ qvec
        order = np.argsort(-scores, kind="stable")[:top_k]
        return [SearchResult(self.documents[i]["document_id"], float(scores[i]), rank + 1) for rank, i in enumerate(order)]


def retrieval_metrics(results: list[dict], top_k: int) -> dict:
    reciprocal_ranks, recalls, precisions, hits = [], [], [], []
    by_category: dict[str, list[dict]] = {}
    for row in results:
        gold = set(row["gold_document_ids"])
        retrieved = row["retrieved_document_ids"][:top_k]
        relevant_ranks = [index + 1 for index, doc_id in enumerate(retrieved) if doc_id in gold]
        if gold:
            reciprocal_ranks.append(1 / min(relevant_ranks) if relevant_ranks else 0.0)
            recalls.append(len(gold.intersection(retrieved)) / len(gold))
            precisions.append(len(gold.intersection(retrieved)) / top_k)
            hits.append(float(bool(relevant_ranks)))
        else:
            # Retrieval relevance is undefined for intentionally unanswerable questions.
            reciprocal_ranks.append(None)
            recalls.append(None)
            precisions.append(None)
            hits.append(None)
        by_category.setdefault(row["category"], []).append(row)

    def mean(values: Iterable[float | None]) -> float | None:
        cleaned = [value for value in values if value is not None]
        return round(sum(cleaned) / len(cleaned), 6) if cleaned else None

    metrics = {
        f"hit_rate_at_{top_k}": mean(hits),
        f"recall_at_{top_k}": mean(recalls),
        f"precision_at_{top_k}": mean(precisions),
        "mean_reciprocal_rank": mean(reciprocal_ranks),
        "answerable_questions": sum(value is not None for value in hits),
        "unanswerable_questions_excluded_from_retrieval_metrics": sum(value is None for value in hits),
    }
    category_metrics = {}
    for category, rows in by_category.items():
        answerable = [row for row in rows if row["gold_document_ids"]]
        category_metrics[category] = {
            "questions": len(rows),
            f"hit_rate_at_{top_k}": round(sum(any(doc in set(row["gold_document_ids"]) for doc in row["retrieved_document_ids"][:top_k]) for row in answerable) / len(answerable), 6) if answerable else None,
        }
    metrics["by_category"] = category_metrics
    return metrics


def evaluate(root: Path, retriever_name: str, split: str, top_k: int,
             with_reader: bool = False, max_questions: int | None = None) -> tuple[dict, list[dict]]:
    data = root / "data"
    config = load_json(root / "config" / "baseline.json")
    documents = load_jsonl(data / "documents.jsonl")
    questions = [q for q in load_jsonl(data / "questions.jsonl") if q["split"] == split]
    if max_questions:
        questions = questions[:max_questions]
    if retriever_name == "tfidf":
        retriever = TfidfCosineRetriever(documents)
    elif retriever_name == "ollama":
        from .local_pipeline import OllamaEmbeddingRetriever
        retriever = OllamaEmbeddingRetriever(
            documents,
            config["embedding_model"],
            root / "results" / "cache" / "ollama_document_embeddings.npz",
            config["ollama_base_url"],
        )
    else:
        raise ValueError(f"Unknown retriever: {retriever_name}")

    docs_by_id = {doc["document_id"]: doc for doc in documents}
    rows = []
    started = time.perf_counter()
    for question in questions:
        search_results = retriever.search(question_text(question), top_k=top_k)
        retrieved_ids = [result.document_id for result in search_results]
        row = {
            "question_id": question["question_id"],
            "category": question["category"],
            "split": split,
            "gold_document_ids": question["gold_document_ids"],
            "should_abstain": question["should_abstain"],
            "retrieved_document_ids": retrieved_ids,
            "retrieval_scores": [round(result.score, 8) for result in search_results],
        }
        if with_reader:
            from .local_pipeline import grounded_reader_local
            row["reader"] = grounded_reader_local(
                question,
                [docs_by_id[doc_id] for doc_id in retrieved_ids],
                config["reader_model"],
                config["ollama_base_url"],
            )
        rows.append(row)
    elapsed = time.perf_counter() - started
    summary = {
        "experiment_name": config["experiment_name"],
        "dataset_version": config["dataset_version"],
        "retriever": retriever.name,
        "embedding_model": config["embedding_model"] if retriever_name == "ollama" else None,
        "reader_model": config["reader_model"] if with_reader else None,
        "split": split,
        "top_k": top_k,
        "question_count": len(rows),
        "elapsed_seconds": round(elapsed, 4),
        "average_seconds_per_question": round(elapsed / max(len(rows), 1), 6),
        "metrics": retrieval_metrics(rows, top_k),
        "test_set_accessed": split == "test",
    }
    return summary, rows


def save_results(output_dir: Path, stem: str, summary: dict, rows: list[dict]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / f"{stem}_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    (output_dir / f"{stem}_details.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    with (output_dir / f"{stem}_details.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=[
            "question_id", "category", "split", "should_abstain", "gold_document_ids",
            "retrieved_document_ids", "retrieval_scores",
        ])
        writer.writeheader()
        for row in rows:
            writer.writerow({key: json.dumps(row[key]) if isinstance(row[key], list) else row[key] for key in writer.fieldnames})

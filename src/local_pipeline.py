"""Local Ollama retrieval, grounded reading, ranking, and explanation utilities."""

from __future__ import annotations

import hashlib
import json
import math
import re
import time
import urllib.request
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer

from .baseline import SearchResult, document_text, load_jsonl, question_text, retrieval_metrics, tokenize


FEATURE_NAMES = [
    "dense_similarity",
    "lexical_similarity",
    "token_overlap",
    "model_id_match",
    "effective_on_question_date",
    "current_document",
    "superseded_document",
    "approved_document",
    "authority_score",
    "recency_score",
    "document_length_log",
]


class OllamaClient:
    """Minimal dependency-free client for the local Ollama HTTP service."""

    def __init__(self, base_url: str = "http://127.0.0.1:11434", timeout: int = 300):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def post(self, path: str, payload: dict) -> dict:
        request = urllib.request.Request(
            self.base_url + path,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            return json.load(response)

    def embed(self, model: str, texts: list[str]) -> np.ndarray:
        response = self.post("/api/embed", {"model": model, "input": texts})
        matrix = np.asarray(response["embeddings"], dtype=np.float32)
        return matrix / np.maximum(np.linalg.norm(matrix, axis=1, keepdims=True), 1e-12)

    def generate_json(self, model: str, prompt: str, *, seed: int = 699) -> tuple[dict, float]:
        started = time.perf_counter()
        response = self.post(
            "/api/generate",
            {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "format": "json",
                "think": False,
                "options": {"temperature": 0, "seed": seed, "num_predict": 350},
            },
        )
        elapsed = time.perf_counter() - started
        text = response.get("response", "").strip()
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            parsed = {"answer": text, "citations": [], "abstained": False, "parse_error": True}
        parsed["latency_seconds"] = round(elapsed, 4)
        parsed["prompt_eval_count"] = response.get("prompt_eval_count")
        parsed["eval_count"] = response.get("eval_count")
        return parsed, elapsed


def cached_embeddings(
    client: OllamaClient,
    model: str,
    texts: list[str],
    cache_path: Path,
    *,
    prefix: str,
) -> np.ndarray:
    payload_texts = [prefix + text for text in texts]
    fingerprint = hashlib.sha256((model + "\n" + "\n".join(payload_texts)).encode("utf-8")).hexdigest()
    if cache_path.exists():
        cached = np.load(cache_path, allow_pickle=False)
        if str(cached["fingerprint"]) == fingerprint:
            return cached["vectors"].astype(np.float32)
    matrix = client.embed(model, payload_texts)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(cache_path, fingerprint=fingerprint, model=model, vectors=matrix)
    return matrix


class OllamaEmbeddingRetriever:
    """Dense cosine retriever backed by local Nomic embeddings through Ollama."""

    name = "ollama_embedding_cosine"

    def __init__(
        self,
        documents: list[dict],
        model: str,
        cache_path: Path,
        base_url: str = "http://127.0.0.1:11434",
    ):
        self.documents = documents
        self.model = model
        self.client = OllamaClient(base_url)
        self.matrix = cached_embeddings(
            self.client,
            model,
            [document_text(doc) for doc in documents],
            cache_path,
            prefix="search_document: ",
        )

    def search(self, query: str, top_k: int = 5) -> list[SearchResult]:
        vector = self.client.embed(self.model, ["search_query: " + query])[0]
        scores = self.matrix @ vector
        order = np.argsort(-scores, kind="stable")[:top_k]
        return [
            SearchResult(self.documents[index]["document_id"], float(scores[index]), rank + 1)
            for rank, index in enumerate(order)
        ]


def grounded_reader_local(
    question: dict,
    retrieved_docs: list[dict],
    model: str,
    base_url: str = "http://127.0.0.1:11434",
) -> dict:
    evidence = "\n\n".join(f"[{doc['document_id']}]\n{doc['content']}" for doc in retrieved_docs)
    prompt = f"""You are an auditable bank model-risk evidence assistant.
Question as of {question['as_of_date']}: {question['question']}

Evidence:
{evidence}

Return JSON with exactly these keys: answer, citations, abstained.
- Use only the supplied evidence.
- citations must be a JSON list of document IDs directly supporting the answer.
- If the evidence is insufficient, set abstained to true, state that the evidence is insufficient, and use an empty citations list.
- Respect effective dates. Prefer current, approved, authoritative records over superseded records.
- Do not add facts from general knowledge."""
    parsed, _ = OllamaClient(base_url).generate_json(model, prompt)
    parsed.setdefault("answer", "")
    parsed.setdefault("citations", [])
    parsed.setdefault("abstained", False)
    parsed["citations"] = [
        str(item).strip().strip("[]").strip()
        for item in parsed["citations"]
        if isinstance(item, (str, int)) and str(item).strip().strip("[]").strip()
    ]
    parsed["abstained"] = bool(parsed["abstained"])
    return parsed


def evaluate_reader(rows: list[dict]) -> dict:
    abstention_correct = []
    citation_hit = []
    grounded_citations = []
    latencies = []
    for row in rows:
        reader = row["reader"]
        citations = set(reader.get("citations", []))
        retrieved = set(row["retrieved_document_ids"])
        gold = set(row["gold_document_ids"])
        abstention_correct.append(reader.get("abstained", False) == row["should_abstain"])
        if gold:
            citation_hit.append(bool(citations & gold))
        grounded_citations.append(citations <= retrieved)
        latencies.append(float(reader.get("latency_seconds", 0)))
    return {
        "abstention_accuracy": round(float(np.mean(abstention_correct)), 6),
        "citation_hit_rate_answerable": round(float(np.mean(citation_hit)), 6) if citation_hit else None,
        "retrieval_grounded_citation_rate": round(float(np.mean(grounded_citations)), 6),
        "average_reader_latency_seconds": round(float(np.mean(latencies)), 4),
    }


def _parse_date(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None


def _effective_on(doc: dict, as_of: str) -> float:
    target = _parse_date(as_of)
    start = _parse_date(doc.get("effective_date"))
    end = _parse_date(doc.get("expiration_date"))
    return float(bool(target and (not start or start <= target) and (not end or target <= end)))


def _authority_score(text: str) -> float:
    lowered = text.lower()
    if "independent" in lowered or "model risk committee" in lowered:
        return 1.0
    if "model risk" in lowered or "compliance" in lowered:
        return 0.8
    if "model owner" in lowered or "development" in lowered:
        return 0.6
    return 0.4


def _recency_score(doc: dict, as_of: str) -> float:
    target = _parse_date(as_of)
    effective = _parse_date(doc.get("effective_date")) or _parse_date(doc.get("created_date"))
    if not target or not effective:
        return 0.0
    days = max((target - effective).days, 0)
    return 1.0 / (1.0 + days / 365.25)


@dataclass
class FeatureBundle:
    frame: pd.DataFrame
    feature_names: list[str]


def build_pair_features(
    root: Path,
    splits: Iterable[str] = ("train", "development"),
    *,
    embedding_model: str = "nomic-embed-text",
    base_url: str = "http://127.0.0.1:11434",
) -> FeatureBundle:
    documents = load_jsonl(root / "data" / "documents.jsonl")
    questions = [q for q in load_jsonl(root / "data" / "questions.jsonl") if q["split"] in set(splits)]
    client = OllamaClient(base_url)
    document_strings = [document_text(doc) for doc in documents]
    question_strings = [question_text(question) for question in questions]
    doc_dense = cached_embeddings(
        client,
        embedding_model,
        document_strings,
        root / "results" / "cache" / "ollama_document_embeddings.npz",
        prefix="search_document: ",
    )
    query_cache = root / "results" / "cache" / ("queries_" + hashlib.sha1("|".join(q["question_id"] for q in questions).encode()).hexdigest()[:12] + ".npz")
    query_dense = cached_embeddings(client, embedding_model, question_strings, query_cache, prefix="search_query: ")

    vectorizer = TfidfVectorizer(lowercase=True, stop_words="english", ngram_range=(1, 2), sublinear_tf=True)
    doc_lexical = vectorizer.fit_transform(document_strings)
    query_lexical = vectorizer.transform(question_strings)

    records: list[dict] = []
    for q_index, question in enumerate(questions):
        q_tokens = set(tokenize(question_text(question)))
        dense_scores = doc_dense @ query_dense[q_index]
        lexical_scores = (doc_lexical @ query_lexical[q_index].T).toarray().ravel()
        for d_index, doc in enumerate(documents):
            doc_tokens = set(tokenize(document_text(doc)))
            union = q_tokens | doc_tokens
            record = {
                "question_id": question["question_id"],
                "split": question["split"],
                "category": question["category"],
                "document_id": doc["document_id"],
                "label": int(doc["document_id"] in set(question["gold_document_ids"])),
                "should_abstain": question["should_abstain"],
                "dense_similarity": float(dense_scores[d_index]),
                "lexical_similarity": float(lexical_scores[d_index]),
                "token_overlap": len(q_tokens & doc_tokens) / max(len(union), 1),
                "model_id_match": float(doc["model_id"] == question["model_id"]),
                "effective_on_question_date": _effective_on(doc, question["as_of_date"]),
                "current_document": float(doc.get("document_status") == "current"),
                "superseded_document": float(doc.get("document_status") == "superseded"),
                "approved_document": float(doc.get("approval_status") == "approved"),
                "authority_score": _authority_score(doc.get("source_authority", "")),
                "recency_score": _recency_score(doc, question["as_of_date"]),
                "document_length_log": math.log1p(len(tokenize(document_text(doc)))),
            }
            records.append(record)
    return FeatureBundle(pd.DataFrame.from_records(records), FEATURE_NAMES.copy())


def fit_ranker(frame: pd.DataFrame, params: dict, *, seed: int = 699) -> RandomForestClassifier:
    model = RandomForestClassifier(
        n_estimators=int(params.get("n_estimators", 250)),
        max_depth=params.get("max_depth", 8),
        min_samples_leaf=int(params.get("min_samples_leaf", 2)),
        max_features=params.get("max_features", "sqrt"),
        class_weight=params.get("class_weight", "balanced_subsample"),
        random_state=seed,
        n_jobs=-1,
    )
    model.fit(frame[FEATURE_NAMES], frame["label"])
    return model


def ranker_results(model: RandomForestClassifier, frame: pd.DataFrame, top_k: int = 5) -> tuple[dict, list[dict]]:
    scored = frame.copy()
    scored["ranker_score"] = model.predict_proba(scored[FEATURE_NAMES])[:, 1]
    rows = []
    for question_id, group in scored.groupby("question_id", sort=False):
        ordered = group.sort_values(["ranker_score", "dense_similarity"], ascending=False, kind="stable")
        top = ordered.head(top_k)
        first = group.iloc[0]
        gold = group.loc[group["label"] == 1, "document_id"].tolist()
        rows.append(
            {
                "question_id": question_id,
                "category": first["category"],
                "split": first["split"],
                "gold_document_ids": gold,
                "should_abstain": bool(first["should_abstain"]),
                "retrieved_document_ids": top["document_id"].tolist(),
                "retrieval_scores": [round(float(value), 8) for value in top["ranker_score"]],
            }
        )
    return retrieval_metrics(rows, top_k), rows


#!/usr/bin/env python3
"""Command-line entry point for the Week 3 baseline."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.baseline import evaluate, save_results


ROOT = Path(__file__).resolve().parent


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--retriever", choices=("tfidf", "ollama"), default="tfidf")
    parser.add_argument("--split", choices=("train", "development", "test"), default="development")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--with-reader", action="store_true")
    parser.add_argument("--max-questions", type=int)
    args = parser.parse_args()
    summary, rows = evaluate(ROOT, args.retriever, args.split, args.top_k, args.with_reader, args.max_questions)
    stem = f"{args.retriever}_{args.split}_k{args.top_k}" + ("_reader" if args.with_reader else "")
    save_results(ROOT / "results", stem, summary, rows)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

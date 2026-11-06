#!/usr/bin/env python3
"""Run independent structural and reference-integrity checks on AMREB."""

from __future__ import annotations

import json
from pathlib import Path

from build_dataset import validate


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"


def load_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def main() -> None:
    report = validate(load_jsonl(DATA / "documents.jsonl"), load_jsonl(DATA / "questions.jsonl"))
    print(json.dumps(report, indent=2))
    if not report["valid"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

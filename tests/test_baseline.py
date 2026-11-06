import unittest
from pathlib import Path

from src.baseline import TfidfCosineRetriever, evaluate, load_jsonl, question_text


ROOT = Path(__file__).resolve().parents[1]


class BaselineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.documents = load_jsonl(ROOT / "data" / "documents.jsonl")
        cls.questions = load_jsonl(ROOT / "data" / "questions.jsonl")

    def test_dataset_sizes(self):
        self.assertEqual(len(self.documents), 72)
        self.assertEqual(len(self.questions), 120)

    def test_retrieval_is_deterministic(self):
        retriever = TfidfCosineRetriever(self.documents)
        question = next(q for q in self.questions if q["question_id"] == "RCD-DIR-03")
        first = [r.document_id for r in retriever.search(question_text(question), 5)]
        second = [r.document_id for r in retriever.search(question_text(question), 5)]
        self.assertEqual(first, second)
        self.assertTrue(set(question["gold_document_ids"]).intersection(first))

    def test_development_baseline_does_not_access_test(self):
        summary, rows = evaluate(ROOT, "tfidf", "development", 5)
        self.assertFalse(summary["test_set_accessed"])
        self.assertEqual(summary["question_count"], 30)
        self.assertTrue(all(row["split"] == "development" for row in rows))
        self.assertGreaterEqual(summary["metrics"]["hit_rate_at_5"], 0.90)


if __name__ == "__main__":
    unittest.main()

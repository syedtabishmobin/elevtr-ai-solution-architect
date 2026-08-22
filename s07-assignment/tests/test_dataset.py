"""Structural validation for the agent evaluation dataset."""

import json
import unittest
from collections import Counter
from pathlib import Path


class DatasetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        path = Path(__file__).parents[1] / "datasets" / "agent_eval.jsonl"
        cls.rows = [
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    def test_row_count_and_unique_ids(self) -> None:
        self.assertGreaterEqual(len(self.rows), 8)
        self.assertLessEqual(len(self.rows), 12)
        self.assertEqual(len({row["qid"] for row in self.rows}), len(self.rows))

    def test_required_fields_and_values(self) -> None:
        required = {"qid", "category", "question", "expected_behavior", "notes"}
        allowed_categories = {
            "direct_lookup",
            "multi_file",
            "missing_information",
            "distractor",
        }
        allowed_behaviors = {"answer_with_sources", "flag_for_human"}
        for row in self.rows:
            self.assertEqual(set(row), required)
            self.assertIn(row["category"], allowed_categories)
            self.assertIn(row["expected_behavior"], allowed_behaviors)
            self.assertNotRegex(row["question"].lower(), r"\.pdf|\.md|page \d")

    def test_required_mix(self) -> None:
        counts = Counter(row["category"] for row in self.rows)
        self.assertGreaterEqual(counts["direct_lookup"], 3)
        self.assertGreaterEqual(counts["multi_file"], 2)
        self.assertGreaterEqual(counts["missing_information"], 1)
        self.assertGreaterEqual(counts["distractor"], 1)


if __name__ == "__main__":
    unittest.main()

"""Validate that the saved assignment evidence is complete and internally aligned."""

import csv
import json
import re
import unittest
from pathlib import Path


class SavedArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = Path(__file__).parents[1]
        cls.dataset = [
            json.loads(line)
            for line in (cls.root / "datasets" / "agent_eval.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
            if line.strip()
        ]

    def read_csv(self, name: str) -> list[dict[str, str]]:
        with (self.root / "experiments" / name).open(
            newline="", encoding="utf-8"
        ) as file_handle:
            return list(csv.DictReader(file_handle))

    def test_baseline_is_complete_and_matches_dataset(self) -> None:
        rows = self.read_csv("baseline.csv")
        self.assertEqual(
            [row["qid"] for row in rows],
            [row["qid"] for row in self.dataset],
        )
        self.assertEqual(len(rows), 8)
        by_qid = {row["qid"]: row for row in rows}
        self.assertEqual(by_qid["q01"]["guardrail"], "pass")
        self.assertEqual(by_qid["q06"]["flagged"], "True")
        self.assertEqual(by_qid["q06"]["guardrail"], "pass")
        self.assertEqual(by_qid["q07"]["guardrail"], "fail")

    def test_tool_failure_preserves_all_404_rows(self) -> None:
        rows = self.read_csv("tool_failure.csv")
        self.assertEqual(len(rows), len(self.dataset))
        self.assertTrue(all(row["flagged"] == "error" for row in rows))
        self.assertTrue(all(row["guardrail"] == "error" for row in rows))
        self.assertTrue(all("404" in row["response"] for row in rows))

    def test_required_traces_contain_expected_evidence(self) -> None:
        success = (self.root / "traces" / "success.txt").read_text(
            encoding="utf-8"
        )
        refusal = (self.root / "traces" / "refusal.txt").read_text(
            encoding="utf-8"
        )
        failure = (self.root / "traces" / "failure.txt").read_text(
            encoding="utf-8"
        )
        self.assertIn("ACT      -> file_search", success)
        self.assertIn("OBSERVE  -> file_search search completed", success)
        self.assertIn("DECIDE   ->", success)
        self.assertIn("ACT      -> flag_for_human", refusal)
        self.assertIn("OBSERVE  -> flag_for_human returned", refusal)
        self.assertIn("ERROR    -> ChatClientException", failure)
        self.assertIn("404", failure)

    def test_vector_store_manifest_records_all_five_uploads(self) -> None:
        manifest = (
            self.root / "experiments" / "vector_store_build.txt"
        ).read_text(encoding="utf-8")
        self.assertIn("uploaded_files=5", manifest)
        for filename in (
            "apple_annual_report.pdf",
            "microsoft_annual_report.pdf",
            "tesla_annual_report.pdf",
            "equity_research_policy.md",
            "portfolio_research_faq.md",
        ):
            self.assertIn(filename, manifest)

    def test_findings_has_no_evidence_placeholders(self) -> None:
        findings = (self.root / "FINDINGS.md").read_text(encoding="utf-8")
        self.assertIsNone(
            re.search(
                r"\b(?:TODO|TBD|PLACEHOLDER|INSERT RESULT|REPLACE ME)\b",
                findings,
                flags=re.IGNORECASE,
            )
        )


if __name__ == "__main__":
    unittest.main()

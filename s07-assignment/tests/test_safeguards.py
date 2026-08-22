"""Deterministic checks for the source-citation output guardrail."""

import unittest

from safeguards import has_source_citation


class SourceCitationGuardrailTests(unittest.TestCase):
    def test_grounded_answer_passes(self) -> None:
        result = has_source_citation(
            "The review happens every 90 days.\n"
            "Sources: equity_research_policy.md"
        )
        self.assertEqual(result, {"value": "pass", "reason": "equity_research_policy.md"})

    def test_flagged_answer_passes(self) -> None:
        result = has_source_citation(
            "Flagged for human review: the answer is not in the corpus.\n"
            "Sources: none (flagged for human review)"
        )
        self.assertEqual(result["value"], "pass")

    def test_missing_sources_line_fires(self) -> None:
        result = has_source_citation("A fluent but unsupported answer.")
        self.assertEqual(
            result,
            {"value": "fail", "reason": "no Sources: line found"},
        )

    def test_empty_sources_line_fires(self) -> None:
        result = has_source_citation("An answer.\nSources:   \n")
        self.assertEqual(
            result,
            {"value": "fail", "reason": "Sources: line was empty"},
        )


if __name__ == "__main__":
    unittest.main()

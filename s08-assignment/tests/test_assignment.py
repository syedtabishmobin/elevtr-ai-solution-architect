from __future__ import annotations

import csv
import json
from pathlib import Path
import zipfile


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_DOCS = {
    "apple_annual_report.pdf",
    "microsoft_annual_report.pdf",
    "tesla_annual_report.pdf",
    "equity_research_policy.md",
    "portfolio_research_faq.md",
}
EXPECTED_SUBMISSION = {
    "s08-assignment/cross-cloud-scorecard.md",
    "s08-assignment/FINDINGS.md",
}


def test_reused_corpus_is_complete() -> None:
    assert {path.name for path in (ROOT / "docs").iterdir()} == EXPECTED_DOCS


def test_dataset_reuses_all_eight_s07_questions() -> None:
    rows = [json.loads(line) for line in (ROOT / "datasets/agent_eval.jsonl").read_text().splitlines()]
    assert [row["qid"] for row in rows] == [f"q{i:02d}" for i in range(1, 9)]


def test_managed_eval_contains_exact_selected_questions() -> None:
    with (ROOT / "experiments/managed_eval.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert [row["qid"] for row in rows] == ["q01", "q04", "q06", "q07"]
    assert all(row["status"] == "pass" for row in rows)


def test_findings_has_no_placeholders() -> None:
    findings = (ROOT / "FINDINGS.md").read_text(encoding="utf-8").casefold()
    forbidden = ("todo", "tbd", "replace me", "paste here", "add evidence", "<placeholder>")
    assert all(token not in findings for token in forbidden)


def test_submission_zip_exact_manifest() -> None:
    with zipfile.ZipFile(ROOT / "s08-assignment.zip") as archive:
        assert set(archive.namelist()) == EXPECTED_SUBMISSION
        assert archive.testzip() is None

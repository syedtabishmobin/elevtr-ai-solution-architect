"""Run four existing S07 questions through the deployed Foundry endpoint."""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path
import time

from azure.ai.projects import AIProjectClient
from azure.identity import AzureCliCredential
from dotenv import load_dotenv


SELECTED_QIDS = ("q01", "q04", "q06", "q07")
REQUIRED_TEXT = {
    "q01": ("70", "Sources:"),
    "q04": ("evidence", "source file", "date", "general knowledge", "Sources:"),
    "q06": ("flagged for human review", "Sources: none"),
    "q07": ("78,678", "30,739", "109,417", "Sources:"),
}
REQUIRED_CALLS = {
    "q01": ("file_search",),
    "q04": ("file_search",),
    "q06": ("flag_for_human",),
    "q07": ("file_search",),
}


def load_questions(path: Path) -> list[dict[str, str]]:
    rows = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    by_qid = {row["qid"]: row for row in rows}
    missing = set(SELECTED_QIDS) - set(by_qid)
    if missing:
        raise ValueError(f"Missing required qids: {sorted(missing)}")
    return [by_qid[qid] for qid in SELECTED_QIDS]


def main() -> None:
    load_dotenv()
    endpoint = os.environ["FOUNDRY_PROJECT_ENDPOINT"]
    agent_name = os.environ["FOUNDRY_HOSTED_AGENT_NAME"]
    project = AIProjectClient(
        endpoint=endpoint,
        credential=AzureCliCredential(),
        allow_preview=True,
    )
    client = project.get_openai_client(agent_name=agent_name)
    questions = load_questions(Path("datasets/agent_eval.jsonl"))

    output_path = Path("experiments/managed_eval.csv")
    output_path.parent.mkdir(exist_ok=True)
    started = time.monotonic()
    results: list[dict[str, str]] = []
    for row in questions:
        called_tools: set[str] = set()
        try:
            response = client.responses.create(input=row["question"])
            if response.status != "completed" or response.error is not None:
                error_message = getattr(response.error, "message", response.error)
                raise RuntimeError(
                    f"Managed response status={response.status}: {error_message}"
                )
            answer = response.output_text.strip()
            if not answer:
                raise RuntimeError("Managed response completed without answer text")
            called_tools = {
                str(getattr(item, "name", ""))
                for item in response.output
                if getattr(item, "type", "") == "function_call"
            }
            folded = answer.casefold()
            missing = [
                text for text in REQUIRED_TEXT[row["qid"]] if text.casefold() not in folded
            ]
            missing_calls = [
                name for name in REQUIRED_CALLS[row["qid"]] if name not in called_tools
            ]
            problems = []
            if missing:
                problems.append("text " + ", ".join(missing))
            if missing_calls:
                problems.append("tool call " + ", ".join(missing_calls))
            status = "pass" if not problems else "fail: missing " + "; ".join(problems)
        except Exception as exc:  # keep evidence for every requested question
            answer = f"{type(exc).__name__}: {exc}"
            status = "error"
        results.append(
            {
                "qid": row["qid"],
                "category": row["category"],
                "expected_behavior": row["expected_behavior"],
                "status": status,
                "called_tools": ", ".join(sorted(called_tools)) or "none",
                "response": answer,
            }
        )
        print(f"{row['qid']}: {status}", flush=True)

    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=results[0].keys(), lineterminator="\n")
        writer.writeheader()
        writer.writerows(results)

    elapsed = time.monotonic() - started
    if len(results) != 4:
        raise RuntimeError(f"Expected 4 managed results, found {len(results)}")
    print(f"Wrote {output_path} ({len(results)} rows)")
    print(f"Evaluation elapsed seconds: {elapsed:.1f}")


if __name__ == "__main__":
    main()

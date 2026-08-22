"""Run the full agent dataset and save one complete CSV experiment."""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
from pathlib import Path
from typing import Any

from agent import ask, build_agent
from safeguards import has_source_citation

DATASET_PATH = Path("datasets/agent_eval.jsonl")


def load_rows(path: Path = DATASET_PATH) -> list[dict[str, Any]]:
    """Load non-empty JSONL rows from the evaluation dataset."""

    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


async def run(vector_store_id: str, name: str) -> None:
    """Run every dataset row even if one hosted-tool request fails."""

    agent = build_agent(vector_store_id)
    rows = load_rows()
    experiments_dir = Path("experiments")
    experiments_dir.mkdir(exist_ok=True)
    output_path = experiments_dir / f"{name}.csv"

    with output_path.open("w", newline="", encoding="utf-8") as file_handle:
        writer = csv.DictWriter(
            file_handle,
            fieldnames=[
                "qid",
                "category",
                "expected_behavior",
                "flagged",
                "guardrail",
                "response",
            ],
            lineterminator="\n",
        )
        writer.writeheader()
        for row in rows:
            try:
                result = await ask(agent, row["question"])
                flagged: bool | str = result["flagged"]
                guardrail = has_source_citation(result["response"])["value"]
                response_text = result["response"][:200]
            except Exception as exc:  # noqa: BLE001 - preserve the rest of the run
                flagged, guardrail = "error", "error"
                response_text = f"{type(exc).__name__}: {exc}"[:200]

            writer.writerow(
                {
                    "qid": row["qid"],
                    "category": row["category"],
                    "expected_behavior": row["expected_behavior"],
                    "flagged": flagged,
                    "guardrail": guardrail,
                    "response": response_text,
                }
            )

    with output_path.open(newline="", encoding="utf-8") as file_handle:
        written_rows = list(csv.DictReader(file_handle))
    if len(written_rows) != len(rows):
        raise RuntimeError(
            f"Incomplete run: expected {len(rows)} rows, wrote {len(written_rows)}"
        )
    print(f"Wrote {output_path} ({len(written_rows)} rows)")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate the document agent.")
    parser.add_argument("vector_store_id")
    parser.add_argument("name")
    return parser.parse_args()


if __name__ == "__main__":
    cli_args = parse_args()
    asyncio.run(run(cli_args.vector_store_id, cli_args.name))

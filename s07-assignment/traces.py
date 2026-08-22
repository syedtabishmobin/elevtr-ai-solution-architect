"""Capture readable ACT / OBSERVE / DECIDE traces from real agent runs."""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any, Iterable

from agent import ask, build_agent


def _display_arguments(arguments: Any) -> Any:
    if isinstance(arguments, str):
        try:
            return json.loads(arguments)
        except json.JSONDecodeError:
            return arguments
    return arguments


def render_loop_trace(messages: Iterable[Any], final_answer: str) -> str:
    """Render hosted-search and local-tool content as a readable loop trace."""

    lines: list[str] = []
    function_names: dict[str, str] = {}
    for message in messages:
        for content in getattr(message, "contents", []):
            kind = getattr(content, "type", None)
            if kind == "search_tool_call":
                arguments = _display_arguments(getattr(content, "arguments", {}))
                queries = (
                    arguments.get("queries")
                    if isinstance(arguments, dict)
                    else arguments
                )
                lines.append(
                    "ACT      -> "
                    f"{getattr(content, 'tool_name', None) or 'file_search'}"
                    f"(queries={queries})"
                )
            elif kind == "search_tool_result":
                lines.append(
                    "OBSERVE  -> "
                    f"{getattr(content, 'tool_name', None) or 'file_search'} search "
                    f"{getattr(content, 'status', None) or 'completed'}"
                )
            elif kind == "function_call":
                call_id = getattr(content, "call_id", None)
                function_name = getattr(content, "name", None) or "function"
                if call_id:
                    function_names[call_id] = function_name
                lines.append(
                    "ACT      -> "
                    f"{function_name}"
                    f"({_display_arguments(getattr(content, 'arguments', {}))})"
                )
            elif kind == "function_result":
                call_id = getattr(content, "call_id", None)
                function_name = (
                    function_names.get(call_id)
                    or getattr(content, "name", None)
                    or "function"
                )
                lines.append(
                    "OBSERVE  -> "
                    f"{function_name} returned "
                    f"{getattr(content, 'result', '')}"
                )

    lines.append(f"DECIDE   -> {final_answer}")
    return "\n".join(lines)


def load_question(qid: str) -> str:
    rows = [
        json.loads(line)
        for line in Path("datasets/agent_eval.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    for row in rows:
        if row["qid"] == qid:
            return row["question"]
    raise KeyError(f"Unknown qid: {qid}")


async def capture(vector_store_id: str, qid: str, output_path: Path) -> None:
    question = load_question(qid)
    lines = [f"QID      -> {qid}", f"QUESTION -> {question}"]
    try:
        result = await ask(build_agent(vector_store_id), question)
        lines.append(render_loop_trace(result["messages"], result["response"]))
    except Exception as exc:  # noqa: BLE001 - the failure trace is intentional
        lines.append(f"ERROR    -> {type(exc).__name__}: {exc}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {output_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Capture one agent trace.")
    parser.add_argument("vector_store_id")
    parser.add_argument("qid")
    parser.add_argument("output_path", type=Path)
    return parser.parse_args()


if __name__ == "__main__":
    cli_args = parse_args()
    asyncio.run(capture(cli_args.vector_store_id, cli_args.qid, cli_args.output_path))

"""Exercise both action limits and the citation guardrail without an API call."""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path
from typing import Any

from agent_framework import (
    Agent,
    BaseChatClient,
    ChatMiddlewareLayer,
    ChatResponse,
    Content,
    FunctionInvocationLayer,
    Message,
    tool,
)

from safeguards import has_source_citation

LIMIT_TEXT = (
    "Function invocation limit reached before a final answer could be produced."
)


class ScriptedClient(FunctionInvocationLayer, ChatMiddlewareLayer, BaseChatClient):
    """A deterministic model double that keeps requesting one local tool."""

    def __init__(self, *, max_iterations: int, max_function_calls: int) -> None:
        super().__init__(
            function_invocation_configuration={
                "max_iterations": max_iterations,
                "max_function_calls": max_function_calls,
            }
        )
        self.model_calls = 0
        self.tool_choices: list[Any] = []

    def _inner_get_response(
        self,
        *,
        messages: Any,
        stream: bool = False,
        options: dict[str, Any],
        **kwargs: Any,
    ) -> Any:
        del messages, kwargs
        if stream:
            raise ValueError("The safeguard probe only supports non-streaming runs")

        self.model_calls += 1
        self.tool_choices.append(options.get("tool_choice"))

        async def respond() -> ChatResponse[Any]:
            return ChatResponse(
                messages=[
                    Message(
                        role="assistant",
                        contents=[
                            Content.from_function_call(
                                call_id=f"call-{self.model_calls}",
                                name="loop_probe",
                                arguments={"step": self.model_calls},
                            )
                        ],
                    )
                ]
            )

        return respond()


async def action_case(
    *,
    max_iterations: int,
    max_function_calls: int,
) -> dict[str, Any]:
    """Run one intentionally looping tool case and verify the framework stops it."""

    executions: list[int] = []

    @tool
    def loop_probe(step: int) -> str:
        executions.append(step)
        return f"continue after step {step}"

    client = ScriptedClient(
        max_iterations=max_iterations,
        max_function_calls=max_function_calls,
    )
    response = await Agent(client=client, tools=[loop_probe]).run(
        "Keep calling loop_probe."
    )

    if response.text != LIMIT_TEXT:
        raise AssertionError(f"Unexpected limit response: {response.text!r}")
    if executions != [1]:
        raise AssertionError(f"Expected one tool execution, observed {executions}")
    if client.model_calls != 2:
        raise AssertionError(f"Expected two model turns, got {client.model_calls}")
    if client.tool_choices[-1] != "none":
        raise AssertionError("The final model turn did not disable tools")

    return {
        "status": "limit_reached",
        "model_calls": client.model_calls,
        "tool_calls": len(executions),
        "final_tool_choice": client.tool_choices[-1],
        "final_text": response.text,
    }


async def run_probe(output_path: Path) -> None:
    iteration_result = await action_case(
        max_iterations=1,
        max_function_calls=99,
    )
    function_result = await action_case(
        max_iterations=6,
        max_function_calls=1,
    )
    guardrail_results = {
        "missing_sources_line": has_source_citation(
            "A fluent but unsupported answer."
        ),
        "empty_sources_line": has_source_citation("Answer.\nSources:   \n"),
        "grounded_sources_line": has_source_citation(
            "Answer.\nSources: equity_research_policy.md"
        ),
    }

    lines = [
        "Safeguard probe",
        "===============",
        "",
        f"max_iterations: {iteration_result}",
        f"max_function_calls: {function_result}",
        f"citation_guardrail: {guardrail_results}",
    ]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {output_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Exercise assignment safeguards.")
    parser.add_argument(
        "output_path",
        nargs="?",
        type=Path,
        default=Path("experiments/safeguards.txt"),
    )
    return parser.parse_args()


if __name__ == "__main__":
    cli_args = parse_args()
    asyncio.run(run_probe(cli_args.output_path))

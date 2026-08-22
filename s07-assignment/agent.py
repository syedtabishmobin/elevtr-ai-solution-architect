"""The single document-agent path used by the application and evaluations."""

from __future__ import annotations

from typing import Annotated, Any

from agent_framework import Agent
from agent_framework.openai import OpenAIChatClient
from dotenv import load_dotenv
from pydantic import Field

load_dotenv()

INSTRUCTIONS = """
You are a document assistant. Always use the file_search tool to find evidence
in the knowledge base before answering.

If the search results do not contain the answer, you MUST invoke the
flag_for_human function tool exactly once instead of guessing. Do not merely
write that the question was flagged, and do not imitate the tool's return text;
the function call itself is required. After the tool returns, give the user a
short refusal based on that result.

Always end your answer with a line in exactly this format:
Sources: <file names you actually used>

or, if you called flag_for_human:
Sources: none (flagged for human review)
"""


def flag_for_human(
    reason: Annotated[
        str,
        Field(
            description=(
                "Why this question needs a human, for example because the "
                "answer is not in the knowledge base."
            )
        ),
    ],
) -> str:
    """Escalate when the knowledge base cannot answer instead of guessing."""

    return f"Flagged for human review: {reason}"


def build_agent(
    vector_store_id: str,
    max_iterations: int = 6,
    max_function_calls: int = 6,
) -> Agent:
    """Build the real agent with hosted search, escalation, and action limits."""

    if not vector_store_id.strip():
        raise ValueError("vector_store_id must not be empty")
    if max_iterations < 1 or max_function_calls < 1:
        raise ValueError("action limits must be positive integers")

    client = OpenAIChatClient()
    client.function_invocation_configuration["max_iterations"] = max_iterations
    client.function_invocation_configuration["max_function_calls"] = (
        max_function_calls
    )
    return Agent(
        client=client,
        name="DocsAgent",
        instructions=INSTRUCTIONS,
        default_options={"max_tool_calls": max_function_calls},
        tools=[
            client.get_file_search_tool(vector_store_ids=[vector_store_id]),
            flag_for_human,
        ],
    )


async def ask(agent: Agent, question: str) -> dict[str, Any]:
    """Run the same real agent path used by every application and eval case."""

    response = await agent.run(question)
    response_text = response.text or ""
    messages = response.messages or []
    flagged = any(
        getattr(content, "type", None) == "function_call"
        and getattr(content, "name", None) == "flag_for_human"
        for message in messages
        for content in getattr(message, "contents", [])
    )
    return {
        "response": response_text,
        "flagged": flagged,
        "messages": messages,
    }

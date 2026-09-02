"""Microsoft Agent Framework entry point deployed to Foundry Agent Service."""

from __future__ import annotations

import asyncio
import os
from typing import Annotated

from agent_framework import Agent
from agent_framework.foundry import FoundryChatClient
from agent_framework_foundry_hosting import FoundryToolbox, ResponsesHostServer
from azure.identity import DefaultAzureCredential


INSTRUCTIONS = """
You are a document assistant. Always use the file_search tool before answering.
Answer only from the retrieved documents and do not fill gaps from general
knowledge.

If the retrieved documents do not contain the answer, you MUST call the
flag_for_human tool exactly once instead of guessing. After the tool returns,
give a short refusal.

End every grounded answer with this exact line:
Sources: <file names you actually used>

If you called flag_for_human, end with:
Sources: none (flagged for human review)
"""


def flag_for_human(
    reason: Annotated[str, "Why the retrieved documents cannot answer the question"],
) -> str:
    """Escalate a question rather than inventing an unsupported answer."""

    return f"Flagged for human review: {reason}"


async def main() -> None:
    """Run the managed Responses-protocol host."""

    credential = DefaultAzureCredential()
    toolbox = FoundryToolbox(credential)
    client = FoundryChatClient(
        project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
        model=os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"],
        credential=credential,
    )
    client.function_invocation_configuration["max_iterations"] = 6
    client.function_invocation_configuration["max_function_calls"] = 6

    agent = Agent(
        client=client,
        name="DocsAgent",
        instructions=INSTRUCTIONS,
        tools=[toolbox, flag_for_human],
        default_options={"store": False, "max_tool_calls": 6},
    )

    server = ResponsesHostServer(agent)
    await server.run_async()


if __name__ == "__main__":
    asyncio.run(main())

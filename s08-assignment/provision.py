"""Create the Foundry vector store and file-search toolbox for this assignment."""

from __future__ import annotations

import argparse
from contextlib import ExitStack
import os
from pathlib import Path
from typing import Iterable

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import FileSearchToolboxTool, ToolConfig
from azure.identity import AzureCliCredential
from dotenv import load_dotenv


DEFAULT_ENDPOINT = (
    "https://foundry-elevtr-s08-aue.services.ai.azure.com/api/projects/elevtr-s08"
)
DEFAULT_STORE_NAME = "s08-knowledge-base"
DEFAULT_TOOLBOX_NAME = "s08-document-tools"
SUPPORTED_SUFFIXES = {".md", ".pdf", ".txt"}


def discover_documents(directory: Path) -> list[Path]:
    """Return the stable, non-empty document upload list."""

    if not directory.is_dir():
        raise FileNotFoundError(f"Document directory not found: {directory}")
    documents = sorted(
        path
        for path in directory.iterdir()
        if path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES
    )
    if not documents:
        raise ValueError(f"No supported documents found under {directory}")
    return documents


def find_complete_store(openai_client, name: str, expected_files: int):
    """Reuse a complete same-name store so reruns do not duplicate uploads."""

    for store in openai_client.vector_stores.list(limit=100).data:
        counts = store.file_counts
        if (
            store.name == name
            and counts.completed == expected_files
            and counts.failed == 0
            and store.status == "completed"
        ):
            return store
    return None


def ensure_vector_store(openai_client, documents: list[Path], name: str):
    """Create one managed vector store and let Foundry index every source file."""

    existing = find_complete_store(openai_client, name, len(documents))
    if existing is not None:
        print(f"Reusing vector store {existing.id} ({len(documents)} completed files)")
        return existing

    # Foundry's OpenAI-compatible vector-store endpoint currently accepts the
    # portable name field but not OpenAI's optional description field.
    store = openai_client.vector_stores.create(name=name)
    print(f"Created vector store {store.id}")

    with ExitStack() as stack:
        handles: Iterable = [
            stack.enter_context(path.open("rb")) for path in documents
        ]
        batch = openai_client.vector_stores.file_batches.upload_and_poll(
            vector_store_id=store.id,
            files=handles,
        )

    if batch.status != "completed" or batch.file_counts.failed:
        raise RuntimeError(
            "Vector-store indexing failed: "
            f"status={batch.status}, counts={batch.file_counts}"
        )

    completed = openai_client.vector_stores.retrieve(store.id)
    if completed.file_counts.completed != len(documents):
        raise RuntimeError(
            f"Expected {len(documents)} indexed files, found "
            f"{completed.file_counts.completed}"
        )
    print(f"Indexed {completed.file_counts.completed} files with 0 failures")
    return completed


def ensure_toolbox(project: AIProjectClient, name: str, vector_store_id: str):
    """Create or reuse the project toolbox that exposes managed file search."""

    for toolbox in project.toolboxes.list(limit=100):
        if toolbox.name != name:
            continue
        version = project.toolboxes.get_version(name, toolbox.default_version)
        for tool in version.tools:
            if (
                getattr(tool, "type", None) == "file_search"
                and vector_store_id in (getattr(tool, "vector_store_ids", None) or [])
            ):
                print(f"Reusing toolbox {name} version {version.version}")
                return version

    created = project.toolboxes.create_version(
        name=name,
        description="Managed file search over the S08 knowledge base",
        tools=[
            FileSearchToolboxTool(
                name="file_search",
                description="Search the assignment document corpus before answering",
                vector_store_ids=[vector_store_id],
                max_num_results=5,
                tool_configs={"*": ToolConfig(pin=True)},
            )
        ],
    )
    project.toolboxes.update(name, default_version=created.version)
    print(f"Created toolbox {name} version {created.version}")
    return created


def update_env(path: Path, values: dict[str, str]) -> None:
    """Update the ignored local environment file without storing secrets."""

    current: dict[str, str] = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip() and not line.lstrip().startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                current[key] = value
    current.update(values)
    path.write_text(
        "".join(f"{key}={value}\n" for key, value in current.items()),
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--docs", type=Path, default=Path("docs"))
    parser.add_argument("--project-endpoint", default=None)
    parser.add_argument("--store-name", default=DEFAULT_STORE_NAME)
    parser.add_argument("--toolbox-name", default=DEFAULT_TOOLBOX_NAME)
    parser.add_argument("--save-env", action="store_true")
    return parser.parse_args()


def main() -> None:
    load_dotenv()
    args = parse_args()
    endpoint = args.project_endpoint or os.getenv(
        "FOUNDRY_PROJECT_ENDPOINT", DEFAULT_ENDPOINT
    )
    documents = discover_documents(args.docs)
    project = AIProjectClient(
        endpoint=endpoint,
        credential=AzureCliCredential(),
        allow_preview=True,
    )
    openai_client = project.get_openai_client()

    store = ensure_vector_store(openai_client, documents, args.store_name)
    toolbox = ensure_toolbox(project, args.toolbox_name, store.id)
    toolbox_endpoint = (
        f"{endpoint}/toolboxes/{args.toolbox_name}/versions/"
        f"{toolbox.version}/mcp?api-version=v1"
    )

    print("Uploaded files:")
    for document in documents:
        print(f"- {document.name}")
    print(f"Toolbox endpoint: {toolbox_endpoint}")

    if args.save_env:
        update_env(
            Path(".env"),
            {
                "FOUNDRY_PROJECT_ENDPOINT": endpoint,
                "AZURE_AI_MODEL_DEPLOYMENT_NAME": "gpt-5-mini-s08",
                "AZURE_VECTOR_STORE_ID": store.id,
                "AZURE_TOOLBOX_NAME": args.toolbox_name,
                "TOOLBOX_ENDPOINT": toolbox_endpoint,
                "FOUNDRY_HOSTED_AGENT_NAME": "s08-docs-agent",
            },
        )
        print("Saved non-secret deployment identifiers to ignored .env")


if __name__ == "__main__":
    main()

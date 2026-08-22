"""Create one hosted OpenAI vector store from the local document corpus."""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from agent_framework.openai import OpenAIChatClient
from dotenv import load_dotenv, set_key

load_dotenv()


async def build_vector_store(docs_dir: str) -> tuple[str, list[str]]:
    """Upload every file in ``docs_dir`` to a fresh OpenAI vector store.

    Returns:
        A pair containing the vector-store ID and the uploaded filenames.
    """

    root = Path(docs_dir)
    if not root.is_dir():
        raise FileNotFoundError(f"Document directory does not exist: {root}")

    paths = sorted(path for path in root.rglob("*") if path.is_file())
    if not paths:
        raise ValueError(f"No documents found in: {root}")

    client = OpenAIChatClient()
    vector_store = await client.client.vector_stores.create(
        name="s07-knowledge-base"
    )

    filenames: list[str] = []
    for path in paths:
        with path.open("rb") as file_handle:
            uploaded = await client.client.files.create(
                file=file_handle,
                purpose="user_data",
            )
        result = await client.client.vector_stores.files.create_and_poll(
            vector_store_id=vector_store.id,
            file_id=uploaded.id,
        )
        if result.last_error is not None:
            raise RuntimeError(
                f"{path.name} failed to index: {result.last_error.message}"
            )
        filenames.append(path.name)

    return vector_store.id, filenames


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Upload a document folder to one OpenAI vector store."
    )
    parser.add_argument("docs_dir", nargs="?", default="docs")
    parser.add_argument(
        "--save-env",
        action="store_true",
        help="Save the resulting ID as OPENAI_VECTOR_STORE_ID in .env.",
    )
    args = parser.parse_args()

    vector_store_id, filenames = await build_vector_store(args.docs_dir)
    print(f"vector_store_id={vector_store_id}")
    print(f"uploaded_files={len(filenames)}")
    for filename in filenames:
        print(f"- {filename}")

    if args.save_env:
        set_key(".env", "OPENAI_VECTOR_STORE_ID", vector_store_id, quote_mode="never")
        print("Saved OPENAI_VECTOR_STORE_ID to .env")


if __name__ == "__main__":
    asyncio.run(main())

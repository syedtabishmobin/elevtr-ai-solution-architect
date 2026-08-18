"""The one production RAG path used by every evaluation case."""

import litellm

from build import collection, embed


CHAT = "ollama/qwen3:8b"


def answer(question: str, top_k: int = 4) -> dict:
    """Embed, retrieve, build context, and generate one grounded answer."""

    index = collection()
    available = index.count()
    if available == 0:
        raise RuntimeError("The collection is empty. Run `uv run python build.py` first.")

    result = index.query(
        query_embeddings=embed([question]),
        n_results=min(top_k, available),
        include=["documents", "metadatas", "distances"],
    )
    contexts = result["documents"][0]
    sources = [metadata["source"] for metadata in result["metadatas"][0]]
    context = "\n\n".join(
        f"[{source}] {document}" for source, document in zip(sources, contexts)
    )
    response = litellm.completion(
        model=CHAT,
        messages=[
            {
                "role": "system",
                "content": (
                    "Answer using ONLY the supplied context. Cite source filenames in "
                    "square brackets. If the answer is unavailable, say you don't know. "
                    "/no_think"
                ),
            },
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
        ],
    )["choices"][0]["message"]["content"]

    return {
        "response": response.split("</think>")[-1].strip(),
        "contexts": contexts,
        "sources": sources,
    }


def all_indexed_chunks() -> list[str]:
    """Return every chunk exactly as stored in the current index."""

    stored = collection().get(include=["documents"])
    return stored["documents"] or []


"""Read path: question -> embed -> search -> prompt -> answer."""

import sys

import litellm

from build import collection, embed


CHAT = "ollama/qwen3:8b"
K = 4


def ask(question: str) -> None:
    """Retrieve relevant chunks and answer only from their context."""

    index = collection()
    available = index.count()

    if available == 0:
        raise RuntimeError(
            "The collection is empty. Run `uv run python build.py` first."
        )

    result = index.query(
        query_embeddings=embed([question]),
        n_results=min(K, available),
    )
    hits = list(
        zip(
            result["documents"][0],
            [
                metadata["source"]
                for metadata in result["metadatas"][0]
            ],
            result["distances"][0],
        )
    )

    print(
        f"\nretrieved {len(hits)} chunks "
        "(lower distance = closer in meaning):"
    )
    for document, source, distance in hits:
        preview = document[:64].replace("\n", " ")
        print(f"{distance:8.3f}  {source:<32}  {preview}...")

    context = "\n\n".join(
        f"[{source}] {document}"
        for document, source, _ in hits
    )
    response = litellm.completion(
        model=CHAT,
        messages=[
            {
                "role": "system",
                "content": (
                    "Answer using ONLY the context provided and cite the "
                    "source file in brackets. If the answer is not in the "
                    "context, say you don't know. /no_think"
                ),
            },
            {
                "role": "user",
                "content": f"Context:\n{context}\n\nQuestion: {question}",
            },
        ],
    )
    answer = response["choices"][0]["message"]["content"]
    print("\n" + answer.split("</think>")[-1].strip())


if __name__ == "__main__":
    user_question = (
        " ".join(sys.argv[1:])
        or "What is this corpus about?"
    )
    ask(user_question)

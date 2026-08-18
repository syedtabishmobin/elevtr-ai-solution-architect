"""Build the persistent vector index from the shareable course corpus."""

import glob
import os

import chromadb
import litellm
from dotenv import load_dotenv
from pypdf import PdfReader


load_dotenv()

EMBED = "ollama/mxbai-embed-large"
COLLECTION_NAME = "corpus"
INDEX_PATH = ".index"
CHUNK_SIZE = 120
CHUNK_OVERLAP = 20
EMBED_BATCH_SIZE = 64


def read_docs() -> dict[str, str]:
    documents: dict[str, str] = {}
    for path in sorted(glob.glob("docs/*")):
        lower_path = path.lower()
        if lower_path.endswith(".pdf"):
            text = "\n".join((page.extract_text() or "") for page in PdfReader(path).pages)
        elif lower_path.endswith((".md", ".txt")):
            with open(path, encoding="utf-8", errors="ignore") as source_file:
                text = source_file.read()
        else:
            continue
        if text.strip():
            documents[os.path.basename(path)] = text
        else:
            print(f"warning: skipped empty or image-only document: {path}")
    return documents


def chunk(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    if size <= 0 or overlap < 0 or overlap >= size:
        raise ValueError("chunk size must be positive and overlap must be between 0 and size")
    words = text.split()
    step = size - overlap
    return [
        " ".join(words[start:start + size])
        for start in range(0, len(words), step)
        if words[start:start + size]
    ]


def desired_state() -> dict[str, dict[str, str]]:
    state: dict[str, dict[str, str]] = {}
    for source, text in read_docs().items():
        for position, piece in enumerate(chunk(text)):
            state[f"{source}::{position:04d}"] = {"text": piece, "source": source}
    return state


def embed(texts: list[str], batch: int = EMBED_BATCH_SIZE) -> list[list[float]]:
    embeddings: list[list[float]] = []
    for start in range(0, len(texts), batch):
        current_batch = texts[start:start + batch]
        response = litellm.embedding(model=EMBED, input=current_batch)
        embeddings.extend(row["embedding"] for row in response["data"])
        print(f"embedded {min(start + batch, len(texts))}/{len(texts)}", end="\r")
    return embeddings


def collection():
    client = chromadb.PersistentClient(path=INDEX_PATH)
    return client.get_or_create_collection(COLLECTION_NAME)


def build() -> None:
    state = desired_state()
    if not state:
        raise RuntimeError("No readable documents found in docs/.")
    ids = list(state)
    texts = [state[chunk_id]["text"] for chunk_id in ids]
    index = collection()
    index.upsert(
        ids=ids,
        documents=texts,
        embeddings=embed(texts),
        metadatas=[{"source": state[chunk_id]["source"]} for chunk_id in ids],
    )
    document_count = len({record["source"] for record in state.values()})
    print(f"\nindexed {len(ids)} chunks from {document_count} docs -> {index.count()} in collection")


if __name__ == "__main__":
    build()


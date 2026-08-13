"""Write path: docs/ -> chunks -> embeddings -> Chroma.

The write path is idempotent by design: identical source files produce the
same chunk IDs, and upsert replaces matching records instead of duplicating
them. Deletion is deliberately handled by sync.py, where the index can be
compared with the source-of-truth state on disk.
"""

import glob
import hashlib
import os

import chromadb
import litellm
from dotenv import load_dotenv
from pypdf import PdfReader


load_dotenv()

# Change this to "ollama/mxbai-embed-large" for Part 5.1, then restore the
# original value after recording the contract failure.
EMBED = "ollama/mxbai-embed-large"
COLLECTION_NAME = "corpus"
INDEX_PATH = ".index"
CHUNK_SIZE = 120
CHUNK_OVERLAP = 20
EMBED_BATCH_SIZE = 64


def read_docs() -> dict[str, str]:
    """Return every readable PDF, Markdown, and text file in docs/."""

    documents: dict[str, str] = {}

    for path in sorted(glob.glob("docs/*")):
        lower_path = path.lower()

        if lower_path.endswith(".pdf"):
            text = "\n".join(
                (page.extract_text() or "")
                for page in PdfReader(path).pages
            )
        elif lower_path.endswith((".md", ".txt")):
            with open(
                path,
                encoding="utf-8",
                errors="ignore",
            ) as source_file:
                text = source_file.read()
        else:
            continue

        if text.strip():
            documents[os.path.basename(path)] = text
        else:
            print(f"warning: skipped empty or image-only document: {path}")

    return documents


def chunk(
    text: str,
    size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
) -> list[str]:
    """Split text into fixed-size word windows, matching Assignment S02."""

    if size <= 0:
        raise ValueError("chunk size must be greater than zero")
    if overlap < 0 or overlap >= size:
        raise ValueError("overlap must be non-negative and smaller than size")

    words = text.split()
    step = size - overlap

    return [
        " ".join(words[start:start + size])
        for start in range(0, len(words), step)
        if words[start:start + size]
    ]


def fingerprint(text: str) -> str:
    """Create the content hash used for change-data capture (CDC)."""

    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:16]


def desired_state() -> dict[str, dict[str, str]]:
    """Compute the exact index state implied by the source files on disk."""

    state: dict[str, dict[str, str]] = {}

    for source, text in read_docs().items():
        for position, piece in enumerate(chunk(text)):
            chunk_id = f"{source}::{position:04d}"
            state[chunk_id] = {
                "text": piece,
                "source": source,
                "hash": fingerprint(piece),
            }

    return state


def embed(
    texts: list[str],
    batch: int = EMBED_BATCH_SIZE,
) -> list[list[float]]:
    """Embed texts in batches through the one shared embedding contract."""

    embeddings: list[list[float]] = []

    for start in range(0, len(texts), batch):
        current_batch = texts[start:start + batch]
        response = litellm.embedding(
            model=EMBED,
            input=current_batch,
        )
        embeddings.extend(
            row["embedding"]
            for row in response["data"]
        )
        completed = min(start + batch, len(texts))
        print(f"embedded {completed}/{len(texts)}", end="\r")

    return embeddings


def collection():
    """Open or create the persistent Chroma collection."""

    client = chromadb.PersistentClient(path=INDEX_PATH)
    return client.get_or_create_collection(COLLECTION_NAME)


def build() -> None:
    """Upsert the desired state without removing records absent from disk."""

    state = desired_state()

    if not state:
        raise RuntimeError(
            "No readable documents found in docs/. Add PDF, Markdown, or text files."
        )

    ids = list(state)
    texts = [state[chunk_id]["text"] for chunk_id in ids]
    index = collection()

    index.upsert(
        ids=ids,
        documents=texts,
        embeddings=embed(texts),
        metadatas=[
            {
                "source": state[chunk_id]["source"],
                "hash": state[chunk_id]["hash"],
            }
            for chunk_id in ids
        ],
    )

    document_count = len(
        {record["source"] for record in state.values()}
    )
    print(
        f"\nindexed {len(ids)} chunks from {document_count} docs "
        f"-> {index.count()} in collection"
    )


if __name__ == "__main__":
    build()

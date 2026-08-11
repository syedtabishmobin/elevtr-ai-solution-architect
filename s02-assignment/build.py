# """Index docs/ two ways: naive fixed-size chunks vs title-prefixed chunks."""

# import glob
# import os
# import uuid

# import chromadb
# import litellm
# from pypdf import PdfReader


# EMBED = "ollama/nomic-embed-text"


# def read_docs():
#     out = []

#     for path in sorted(glob.glob("docs/*.pdf")):
#         text = "\n".join(
#             (page.extract_text() or "")
#             for page in PdfReader(path).pages
#         )

#         if text.strip():
#             out.append((os.path.basename(path), text))

#     return out


# def chunk(text, size=120, overlap=20):
#     """Fixed-size chunking: count words, ignore meaning. That is the baseline."""

#     words = text.split()
#     step = size - overlap

#     return [
#         " ".join(words[i:i + size])
#         for i in range(0, len(words), step)
#         if words[i:i + size]
#     ]


# def title_of(text):
#     """First non-empty line = our cheap context. This is metadata prepending."""

#     return next(
#         (
#             line.strip()
#             for line in text.splitlines()
#             if line.strip()
#         ),
#         "document",
#     )


# def embed(texts):
#     response = litellm.embedding(
#         model=EMBED,
#         input=texts,
#     )

#     return [
#         row["embedding"]
#         for row in response["data"]
#     ]


# client = chromadb.PersistentClient(path=".index")

# for name in ("naive", "titled"):
#     try:
#         client.delete_collection(name)
#     except Exception:
#         pass


# naive = client.get_or_create_collection("naive")
# titled = client.get_or_create_collection("titled")


# for filename, text in read_docs():
#     chunks = chunk(text)

#     print(f"{filename}: {len(chunks)} chunks")

#     prefixed = [
#         f"From {title_of(text)}:\n\n{current_chunk}"
#         for current_chunk in chunks
#     ]

#     metadata = [
#         {"source": filename}
#         for _ in chunks
#     ]

#     create_ids = lambda: [
#         str(uuid.uuid4())
#         for _ in chunks
#     ]

#     naive.add(
#         ids=create_ids(),
#         documents=chunks,
#         embeddings=embed(chunks),
#         metadatas=metadata,
#     )

#     titled.add(
#         ids=create_ids(),
#         documents=prefixed,
#         embeddings=embed(prefixed),
#         metadatas=metadata,
#     )


# print("done ->", naive.count(), "chunks per index")


"""Index docs/ two ways: naive fixed-size chunks vs title-prefixed chunks."""

import glob
import os
import uuid

import chromadb
import litellm
from pypdf import PdfReader
from tqdm import tqdm


EMBED = "ollama/nomic-embed-text"
BATCH_SIZE = 32


def read_docs():
    out = []

    for path in sorted(glob.glob("docs/*.pdf")):
        text = "\n".join(
            (page.extract_text() or "")
            for page in PdfReader(path).pages
        )

        if text.strip():
            out.append((os.path.basename(path), text))

    return out


def chunk(text, size=120, overlap=20, desc="Chunking"):
    """Fixed-size chunking: count words, ignore meaning. That is the baseline."""

    words = text.split()
    step = size - overlap
    starts = range(0, len(words), step)

    chunks = []

    for i in tqdm(
        starts,
        desc=desc,
        unit="chunk",
    ):
        current_chunk = words[i:i + size]

        if current_chunk:
            chunks.append(" ".join(current_chunk))

    return chunks


def title_of(text):
    """First non-empty line = our cheap context. This is metadata prepending."""

    return next(
        (
            line.strip()
            for line in text.splitlines()
            if line.strip()
        ),
        "document",
    )


def embed(texts, batch_size=BATCH_SIZE, desc="Embedding"):
    """Embed texts in batches and show chunk-level progress."""

    embeddings = []

    with tqdm(
        total=len(texts),
        desc=desc,
        unit="chunk",
    ) as progress:
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]

            response = litellm.embedding(
                model=EMBED,
                input=batch,
            )

            embeddings.extend(
                row["embedding"]
                for row in response["data"]
            )

            progress.update(len(batch))

    return embeddings


client = chromadb.PersistentClient(path=".index")

for name in ("naive", "titled"):
    try:
        client.delete_collection(name)
    except Exception:
        pass


naive = client.get_or_create_collection("naive")
titled = client.get_or_create_collection("titled")


docs = read_docs()

for filename, text in docs:
    chunks = chunk(
        text,
        desc=f"{filename} | Chunking",
    )

    print(f"{filename}: {len(chunks)} chunks")

    prefixed = [
        f"From {title_of(text)}:\n\n{current_chunk}"
        for current_chunk in chunks
    ]

    metadata = [
        {"source": filename}
        for _ in chunks
    ]

    create_ids = lambda: [
        str(uuid.uuid4())
        for _ in chunks
    ]

    naive_embeddings = embed(
        chunks,
        desc=f"{filename} | Naive embedding",
    )

    naive.add(
        ids=create_ids(),
        documents=chunks,
        embeddings=naive_embeddings,
        metadatas=metadata,
    )

    titled_embeddings = embed(
        prefixed,
        desc=f"{filename} | Titled embedding",
    )

    titled.add(
        ids=create_ids(),
        documents=prefixed,
        embeddings=titled_embeddings,
        metadatas=metadata,
    )


print(
    "done ->",
    naive.count(),
    "naive chunks,",
    titled.count(),
    "titled chunks",
)
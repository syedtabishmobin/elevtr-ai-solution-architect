"""Same query against both indexes; score hit@3 and answerable@3."""

import chromadb
import litellm


EMBED = "ollama/nomic-embed-text"
K = 3


client = chromadb.PersistentClient(path=".index")

collections = {
    name: client.get_collection(name)
    for name in ("naive", "titled")
}


def top_k(collection, query):
    embedding = litellm.embedding(
        model=EMBED,
        input=[query],
    )["data"][0]["embedding"]

    result = collection.query(
        query_embeddings=[embedding],
        n_results=K,
    )

    return list(
        zip(
            result["documents"][0],
            [
                metadata["source"]
                for metadata in result["metadatas"][0]
            ],
        )
    )


rows = []

with open("queries.txt", encoding="utf-8") as query_file:
    for line in query_file:
        if "::" not in line:
            continue

        query, gold = (
            value.strip()
            for value in line.split("::", 1)
        )

        scores = {}

        for name, collection in collections.items():
            hits = top_k(collection, query)

            hit = any(
                gold.lower() in document.lower()
                for document, _ in hits
            )

            answerable = any(
                gold.lower() in document.lower()
                and source.split(".")[0].split("_")[0].lower()
                in document.lower()
                for document, source in hits
            )

            scores[name] = (hit, answerable)

        rows.append((query, scores))


print(f"\n{'query':<81} {'naive':>14} {'titled':>14}")
print("-" * 112)


def cell(hit, answerable):
    if answerable:
        return "ANSWERABLE"

    if hit:
        return "hit-ambig"

    return "MISS"


for query, scores in rows:
    print(
        f"{query[:80]:<81} "
        f"{cell(*scores['naive']):>14} "
        f"{cell(*scores['titled']):>14}"
    )


def total(index_name, score_position):
    return sum(
        1
        for _, scores in rows
        if scores[index_name][score_position]
    )

def total_miss(index_name):
    return sum(
        1
        for _, scores in rows
        if not scores[index_name][0]
    )


question_count = len(rows)

print("-" * 112)
print(
    f"{'TOTAL hit@' + str(K):<81} "
    f"{total('naive', 0):>12}/{question_count} "
    f"{total('titled', 0):>12}/{question_count}"
)
print(
    f"{'TOTAL answerable@' + str(K):<81} "
    f"{total('naive', 1):>12}/{question_count} "
    f"{total('titled', 1):>12}/{question_count}"
)
print(
    f"{'TOTAL MISS' + str(K):<81} "
    f"{total_miss('naive'):>12}/{question_count} "
    f"{total_miss('titled'):>12}/{question_count}"
)
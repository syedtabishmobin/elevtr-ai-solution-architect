import chromadb
import litellm


EMBED = "ollama/nomic-embed-text"
K = 3


client = chromadb.PersistentClient(path=".index")


def top_k(collection_name, query):
    collection = client.get_collection(collection_name)

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
            result["metadatas"][0],
            result["distances"][0],
        )
    )


query = input("Enter the exact evaluation question: ").strip()

for collection_name in ("naive", "titled"):
    print()
    print("=" * 100)
    print(collection_name.upper())
    print("=" * 100)

    for position, (document, metadata, distance) in enumerate(
        top_k(collection_name, query),
        start=1,
    ):
        print()
        print(f"RESULT {position}")
        print(f"Source: {metadata['source']}")
        print(f"Distance: {distance}")
        print("-" * 100)
        print(document)
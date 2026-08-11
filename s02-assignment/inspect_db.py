import chromadb


client = chromadb.PersistentClient(path=".index")

print("Collections:")
for collection in client.list_collections():
    print("-", collection.name)


for collection_name in ("naive", "titled"):
    collection = client.get_collection(collection_name)

    print("\n" + "=" * 80)
    print(f"COLLECTION: {collection_name}")
    print("=" * 80)

    print("Total chunks:", collection.count())

    result = collection.get(
        limit=1,
        include=["documents", "metadatas", "embeddings"],
    )

    print("\nID:")
    print(result["ids"][0])

    print("\nSOURCE:")
    print(result["metadatas"][0]["source"])

    print("\nCHUNK:")
    print(result["documents"][0])

    embedding = result["embeddings"][0]

    print("\nVECTOR DIMENSIONS:")
    print(len(embedding))

    print("\nFIRST 20 VECTOR VALUES:")
    print(embedding[:20])
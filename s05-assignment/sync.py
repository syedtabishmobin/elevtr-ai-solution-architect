"""Make the vector index match disk while touching only changed chunks.

This implements content-based change-data capture, delta indexing, and
tombstone deletion for source files that have disappeared.
"""

from build import collection, desired_state, embed


def sync() -> None:
    """Apply additions, content changes, and removals to the collection."""

    index = collection()
    desired = desired_state()
    raw = index.get(include=["metadatas"])
    existing = {
        chunk_id: metadata.get("hash")
        for chunk_id, metadata in zip(raw["ids"], raw["metadatas"])
    }

    to_add = [
        chunk_id
        for chunk_id in desired
        if chunk_id not in existing
    ]
    to_update = [
        chunk_id
        for chunk_id in desired
        if chunk_id in existing
        and existing[chunk_id] != desired[chunk_id]["hash"]
    ]
    to_delete = [
        chunk_id
        for chunk_id in existing
        if chunk_id not in desired
    ]
    unchanged = len(desired) - len(to_add) - len(to_update)

    print(f"unchanged: {unchanged}")
    print(f"new      : {len(to_add)}")
    print(f"changed  : {len(to_update)}")
    print(f"removed  : {len(to_delete)}")

    work = to_add + to_update

    if work:
        texts = [desired[chunk_id]["text"] for chunk_id in work]
        index.upsert(
            ids=work,
            documents=texts,
            embeddings=embed(texts),
            metadatas=[
                {
                    "source": desired[chunk_id]["source"],
                    "hash": desired[chunk_id]["hash"],
                }
                for chunk_id in work
            ],
        )

    if to_delete:
        index.delete(ids=to_delete)

    percentage = 100 * len(work) / max(1, len(desired))
    print(
        f"\nre-embedded {len(work)} of {len(desired)} chunks "
        f"({percentage:.1f}% of a full reindex)"
    )
    print(f"collection now holds {index.count()} chunks")


if __name__ == "__main__":
    sync()

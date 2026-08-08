"""ChromaDB wrapper providing per-session, isolated vector collections.

Each session gets a collection named ``session_<uuid>`` (dashes replaced with
underscores to satisfy Chroma's naming rules). Collections use cosine distance
so that ``score = 1 - distance`` is a true cosine similarity.
"""

import logging

import chromadb

from config import CHROMA_PATH, SIMILARITY_THRESHOLD, TOP_K_CHUNKS

logger = logging.getLogger(__name__)

_client = chromadb.PersistentClient(path=CHROMA_PATH)


def _collection_name(session_id: str) -> str:
    """Return the Chroma-safe collection name for a session."""
    return f"session_{session_id.replace('-', '_')}"


def _get_collection(session_id: str):
    """Get (or lazily create) the session's cosine-distance collection."""
    return _client.get_or_create_collection(
        name=_collection_name(session_id),
        metadata={"hnsw:space": "cosine"},
    )


def add_document(
    session_id: str,
    document_id: int,
    filename: str,
    chunks: list[str],
    embeddings: list[list[float]],
) -> None:
    """Store a document's chunks and embeddings in the session's collection.

    Args:
        session_id: Owning session UUID.
        document_id: DB id of the document (used for per-document deletion).
        filename: Original PDF filename (stored as metadata).
        chunks: The text chunks.
        embeddings: One embedding vector per chunk (same order/length).
    """
    if not chunks:
        logger.warning("add_document called with no chunks (doc %s)", document_id)
        return

    collection = _get_collection(session_id)
    ids = [f"{document_id}_{i}" for i in range(len(chunks))]
    metadatas = [
        {
            "session_id": session_id,
            "document_id": document_id,
            "filename": filename,
            "chunk_index": i,
        }
        for i in range(len(chunks))
    ]
    collection.add(
        ids=ids, documents=chunks, embeddings=embeddings, metadatas=metadatas
    )
    logger.info("Stored %d chunks for document %s", len(chunks), document_id)


def query(
    session_id: str, query_embedding: list[float], top_k: int = TOP_K_CHUNKS
) -> list[dict]:
    """Retrieve the most similar chunks for a session's query.

    Args:
        session_id: Session UUID.
        query_embedding: Embedding of the question.
        top_k: Maximum number of chunks to return.

    Returns:
        A list of ``{"text", "score", "filename"}`` dicts at/above the
        similarity threshold, best first. Empty if nothing qualifies.
    """
    collection = _get_collection(session_id)
    if collection.count() == 0:
        return []

    n_results = min(top_k, collection.count())
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    matches: list[dict] = []
    for text, meta, distance in zip(documents, metadatas, distances):
        score = 1.0 - distance
        if score >= SIMILARITY_THRESHOLD:
            matches.append(
                {
                    "text": text,
                    "score": score,
                    "filename": meta.get("filename", "unknown"),
                }
            )
    return matches


def delete_document(session_id: str, document_id: int) -> None:
    """Delete all chunks belonging to one document within a session."""
    collection = _get_collection(session_id)
    collection.delete(where={"document_id": document_id})
    logger.info("Deleted chunks for document %s", document_id)


def delete_session(session_id: str) -> None:
    """Delete the session's entire collection (no-op if it does not exist)."""
    try:
        _client.delete_collection(name=_collection_name(session_id))
        logger.info("Deleted collection for session %s", session_id)
    except Exception as exc:
        logger.info("No collection to delete for session %s (%s)", session_id, exc)

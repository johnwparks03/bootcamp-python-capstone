"""Chroma wrapper for the RAG agent: open the policy_docs collection and run
similarity search over it. Callers supply an already-computed query embedding —
this module has no dependency on any embedding provider.
"""

from __future__ import annotations

from dataclasses import dataclass

import chromadb
from chromadb.api import ClientAPI
from chromadb.api.models.Collection import Collection

from python_capstone.config import settings

COLLECTION_NAME = "policy_docs"


@dataclass
class RetrievedChunk:
    chunk_id: str
    text: str
    source: str
    distance: float
    """Chroma's raw distance for this match — lower means more relevant."""


def open_collection() -> Collection:
    client: ClientAPI = chromadb.PersistentClient(path=str(settings.chroma_persist_dir))
    collection = client.get_or_create_collection(
        COLLECTION_NAME,
        metadata={"embedding_model": settings.gemini_embedding_model},
    )

    stored_model = collection.metadata.get("embedding_model") if collection.metadata else None
    if stored_model != settings.gemini_embedding_model:
        raise RuntimeError(
            f"Collection '{COLLECTION_NAME}' was embedded with model '{stored_model}', "
            f"but config now specifies '{settings.gemini_embedding_model}'. "
            f"Delete {settings.chroma_persist_dir} and re-run ingestion, or revert the embedding model in .env."
        )

    return collection


def similarity_search(
    collection: Collection, query_embedding: list[float], k: int
) -> list[RetrievedChunk]:
    results = collection.query(query_embeddings=[query_embedding], n_results=k)

    ids = results["ids"][0]
    documents = results["documents"][0] if results["documents"] else []
    metadatas = results["metadatas"][0] if results["metadatas"] else []
    distances = results["distances"][0] if results["distances"] else []

    return [
        RetrievedChunk(
            chunk_id=chunk_id,
            text=text,
            source=str(metadata.get("source", "")),
            distance=distance,
        )
        for chunk_id, text, metadata, distance in zip(ids, documents, metadatas, distances)
    ]

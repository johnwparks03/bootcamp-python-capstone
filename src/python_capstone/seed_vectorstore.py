"""Chunk the seeded policy documents and load their embeddings into Chroma."""

from __future__ import annotations

from pathlib import Path
from typing import cast

import chromadb
from chromadb.api import ClientAPI
from chromadb.api.models.Collection import Collection
from chromadb.api.types import Metadata, PyEmbedding
from langchain_text_splitters import RecursiveCharacterTextSplitter

from python_capstone.config import PROJECT_ROOT, settings
from python_capstone.llm.gemini_embedding_provider import GeminiEmbeddingProvider
from python_capstone.logging_conf import configure_logging, get_logger


POLICY_DOCS_DIR = PROJECT_ROOT / "data" / "policy_docs"
COLLECTION_NAME = "policy_docs"
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100

log = get_logger(__name__)


def load_documents(policy_docs_dir: Path) -> list[tuple[str, str]]:
    """Read every file in the directory, returning (filename, raw_text) pairs."""
    return [
        (path.name, path.read_text(encoding="utf-8"))
        for path in sorted(policy_docs_dir.iterdir())
        if path.is_file()
    ]


def chunk_documents(
    documents: list[tuple[str, str]],
) -> tuple[list[str], list[str], list[Metadata]]:
    """Split each document into overlapping chunks.

    Returns parallel lists of chunk ids, chunk text, and chunk metadata —
    the shape Chroma's collection.upsert() expects.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
    )

    chunk_ids: list[str] = []
    chunk_texts: list[str] = []
    chunk_metadatas: list[Metadata] = []

    for filename, text in documents:
        for i, chunk in enumerate(splitter.split_text(text)):
            chunk_ids.append(f"{filename}::{i}")
            chunk_texts.append(chunk)
            chunk_metadatas.append({"source": filename, "chunk_index": i})

    return chunk_ids, chunk_texts, chunk_metadatas


def get_verified_collection(client: ClientAPI) -> Collection:
    """Open (or create) the collection, guarding against embedding-model drift.

    A collection embedded with one model isn't comparable to vectors from a
    different model. We stamp the model name as metadata on first creation,
    then check it on every subsequent open and fail loudly on mismatch
    rather than silently returning bad similarity matches.
    """
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


def main() -> None:
    configure_logging(settings.log_level)

    documents = load_documents(POLICY_DOCS_DIR)
    log.info(f"loaded {len(documents)} documents from {POLICY_DOCS_DIR}")

    chunk_ids, chunk_texts, chunk_metadatas = chunk_documents(documents)
    log.info(f"split into {len(chunk_texts)} chunks")

    embedding_provider = GeminiEmbeddingProvider(
        api_key=settings.gemini_api_key, model=settings.gemini_embedding_model
    )
    vectors = embedding_provider.embed(chunk_texts)
    log.info(f"computed {len(vectors)} embeddings")

    client = chromadb.PersistentClient(path=str(settings.chroma_persist_dir))
    collection = get_verified_collection(client)

    collection.upsert(
        ids=chunk_ids,
        embeddings=cast(list[PyEmbedding], vectors),
        documents=chunk_texts,
        metadatas=chunk_metadatas,
    )
    log.info(
        f"upserted {len(chunk_ids)} chunks into collection "
        f"'{COLLECTION_NAME}' ({settings.chroma_persist_dir})"
    )


if __name__ == "__main__":
    main()

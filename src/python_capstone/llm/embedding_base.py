"""Abstract interface for embedding providers.

Vector ingestion and RAG retrieval depend on this interface, never on a
concrete provider like Gemini. Swapping the embedding model later means
writing one new subclass here, not touching ingestion or retrieval code.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class EmbeddingProvider(ABC):
    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts, returning one vector per input text, in order."""
        raise NotImplementedError

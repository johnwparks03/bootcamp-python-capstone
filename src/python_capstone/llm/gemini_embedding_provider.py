"""Gemini implementation of the EmbeddingProvider interface."""

from __future__ import annotations

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from pydantic import SecretStr

from python_capstone.llm.embedding_base import EmbeddingProvider


class GeminiEmbeddingProvider(EmbeddingProvider):
    def __init__(self, api_key: SecretStr, model: str) -> None:
        self._client = GoogleGenerativeAIEmbeddings(model=model, api_key=api_key)

    def embed(self, texts: list[str]) -> list[list[float]]:
        return self._client.embed_documents(texts)

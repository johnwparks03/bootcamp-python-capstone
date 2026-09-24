import chromadb
import pytest

from python_capstone.llm.base import LLMGenerationError, LLMProvider
from python_capstone.llm.embedding_base import EmbeddingProvider
from python_capstone.qualitative_agent.orchestrator import NOT_FOUND_MESSAGE, answer_question


class FakeEmbeddingProvider(EmbeddingProvider):
    """Test double: always returns the same scripted vector for every text
    in the batch, regardless of content."""

    def __init__(self, vector: list[float]) -> None:
        self._vector = vector

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._vector for _ in texts]


class FakeLLMProvider(LLMProvider):
    def __init__(self, response: str | Exception) -> None:
        self._response = response
        self.calls: list[str] = []

    def generate(self, prompt: str) -> str:
        self.calls.append(prompt)
        if isinstance(self._response, Exception):
            raise self._response
        return self._response


@pytest.fixture
def collection():
    client = chromadb.EphemeralClient()
    collection = client.get_or_create_collection("test_policy_docs")
    collection.add(
        ids=["pto_policy.md::0"],
        embeddings=[[1.0, 0.0, 0.0]],
        documents=["Employees accrue 15 days of PTO annually."],
        metadatas=[{"source": "pto_policy.md"}],
    )
    return collection


def test_answer_question_happy_path(collection):
    embedding_provider = FakeEmbeddingProvider([1.0, 0.0, 0.0])
    llm_provider = FakeLLMProvider("Employees get 15 days [pto_policy.md::0].")

    result = answer_question(
        embedding_provider, llm_provider, collection, "How many vacation days?"
    )

    assert result.found is True
    assert result.answer == "Employees get 15 days [pto_policy.md::0]."
    assert len(result.chunks) == 1
    assert result.chunks[0].chunk_id == "pto_policy.md::0"


def test_answer_question_not_found_when_no_relevant_chunks(collection):
    embedding_provider = FakeEmbeddingProvider([-1.0, 0.0, 0.0])
    llm_provider = FakeLLMProvider("should never be called")

    result = answer_question(
        embedding_provider, llm_provider, collection, "What is the capital of France?"
    )

    assert result.found is False
    assert result.answer == NOT_FOUND_MESSAGE
    assert result.chunks == []
    assert llm_provider.calls == []


def test_answer_question_handles_llm_failure(collection):
    embedding_provider = FakeEmbeddingProvider([1.0, 0.0, 0.0])
    llm_provider = FakeLLMProvider(LLMGenerationError("503 Service Unavailable"))

    result = answer_question(
        embedding_provider, llm_provider, collection, "How many vacation days?"
    )

    assert result.found is True
    assert "unavailable" in result.answer
    assert len(result.chunks) == 1

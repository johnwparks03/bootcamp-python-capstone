from python_capstone.llm.embedding_base import EmbeddingProvider
from python_capstone.db.vectorstore import RetrievedChunk, similarity_search
from chromadb.api.models.Collection import Collection


MAX_RELEVANT_DISTANCE = 0.45
TOP_K = 5


def filter_by_relevance(chunks: list[RetrievedChunk], max_distance: float = MAX_RELEVANT_DISTANCE) -> list[RetrievedChunk]:
    return [chunk for chunk in chunks if chunk.distance <= max_distance]


def embed_query(embedding_provider: EmbeddingProvider, question: str) -> list[float]:
    return embedding_provider.embed([question])[0]


def retrieve(embedding_provider: EmbeddingProvider, collection: Collection, question: str) -> list[RetrievedChunk]:
    query_embedding = embed_query(embedding_provider=embedding_provider, question=question)
    similar_chunks = similarity_search(collection=collection, query_embedding=query_embedding, k=TOP_K)
    relevant_chunks = filter_by_relevance(similar_chunks, max_distance=MAX_RELEVANT_DISTANCE)
    return relevant_chunks

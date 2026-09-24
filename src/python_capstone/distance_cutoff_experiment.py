"""Throwaway experiment: compare distances for relevant vs. irrelevant queries
to find a reasonable relevance threshold for 4.4.

Run with: uv run python /path/to/distance_experiment.py
"""

from python_capstone.config import settings
from python_capstone.db.vectorstore import open_collection, similarity_search
from python_capstone.llm.gemini_embedding_provider import GeminiEmbeddingProvider
from python_capstone.qualitative_agent.retrieve import embed_query

RELEVANT_QUERIES = [
    "What is the process for reviewing a pull request?",
    "How should we respond to an angry customer complaint?",
    "What do new employees need to do on their first day?",
    "How many vacation days do employees get per year?",
    "Can employees work from home?",
    "What are the password requirements for company systems?",
]

IRRELEVANT_QUERIES = [
    "What's the weather like today?",
    "How do I bake a chocolate cake?",
    "Who won the World Cup in 2018?",
    "What is the capital of France?",
    "Explain quantum entanglement.",
    "Recommend a good sci-fi movie.",
]


def run(label: str, queries: list[str], provider, collection) -> None:
    print(f"\n=== {label} ===")
    for q in queries:
        query_embedding = embed_query(provider, q)
        results = similarity_search(collection, query_embedding, k=1)
        top = results[0]
        print(f"{round(top.distance, 4):>8}  {q!r:60}  -> {top.source}")


def main() -> None:
    provider = GeminiEmbeddingProvider(
        api_key=settings.gemini_api_key, model=settings.gemini_embedding_model
    )
    collection = open_collection()

    run("RELEVANT", RELEVANT_QUERIES, provider, collection)
    run("IRRELEVANT", IRRELEVANT_QUERIES, provider, collection)


if __name__ == "__main__":
    main()

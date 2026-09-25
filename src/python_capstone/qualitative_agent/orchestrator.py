from dataclasses import dataclass, field
from time import perf_counter

from chromadb.api.models.Collection import Collection

from python_capstone.logging_conf import get_logger
from python_capstone.db.vectorstore import RetrievedChunk
from python_capstone.llm.base import LLMGenerationError, LLMProvider
from python_capstone.llm.embedding_base import EmbeddingProvider
from python_capstone.qualitative_agent.generate import generate_answer
from python_capstone.qualitative_agent.retrieve import retrieve

NOT_FOUND_MESSAGE = "I don't have information about that in the knowledge base."

logger = get_logger(__name__)

@dataclass
class QualitativeAnswer:
    chunks: list[RetrievedChunk] = field(default_factory=list)
    answer: str = ""
    found: bool = True


def answer_question(
    embedding_provider: EmbeddingProvider,
    llm_provider: LLMProvider,
    collection: Collection,
    question: str,
) -> QualitativeAnswer:
    logger.info("Starting qualitative answer generation...")
    logger.info("Incoming query: %s", question)
    start_time = perf_counter()

    relevant_chunks = retrieve(embedding_provider, collection, question)

    if not relevant_chunks:
        logger.info("Retrieved no chunks")
        return QualitativeAnswer(answer=NOT_FOUND_MESSAGE, found=False)

    logger.info("Successfully retrieved %d chunks %s", len(relevant_chunks), [c.chunk_id for c in relevant_chunks])

    try:
        answer = generate_answer(llm_provider, question, relevant_chunks)
    except LLMGenerationError as e:
        logger.warning("Ran into exception calling AI Service: %s Execution time: %.3fs", e, perf_counter() - start_time)
        return QualitativeAnswer(
            chunks=relevant_chunks,
            answer=f"The AI service is currently unavailable: {e}",
        )

    logger.info("Qualitative answer generation successful! Execution time: %.3fs", perf_counter() - start_time)
    qualitative_answer = QualitativeAnswer(chunks=relevant_chunks, answer=answer)
    return qualitative_answer


def format_sources(answer: QualitativeAnswer) -> str:
    if not answer.chunks:
        return answer.answer

    sources = "\n".join(f"  - {chunk.chunk_id} (distance: {chunk.distance:.4f})" for chunk in answer.chunks)

    return f"{answer.answer}\n\nSources:\n{sources}"

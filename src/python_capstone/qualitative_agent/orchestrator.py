from dataclasses import dataclass, field

from chromadb.api.models.Collection import Collection

from python_capstone.db.vectorstore import RetrievedChunk
from python_capstone.llm.base import LLMGenerationError, LLMProvider
from python_capstone.llm.embedding_base import EmbeddingProvider
from python_capstone.qualitative_agent.generate import generate_answer
from python_capstone.qualitative_agent.retrieve import retrieve

NOT_FOUND_MESSAGE = "I don't have information about that in the knowledge base."


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
    relevant_chunks = retrieve(embedding_provider, collection, question)

    if not relevant_chunks:
        return QualitativeAnswer(answer=NOT_FOUND_MESSAGE, found=False)

    try:
        answer = generate_answer(llm_provider, question, relevant_chunks)
    except LLMGenerationError as e:
        return QualitativeAnswer(
            chunks=relevant_chunks,
            answer=f"The AI service is currently unavailable: {e}",
        )

    qualitative_answer = QualitativeAnswer(chunks=relevant_chunks, answer=answer)
    return qualitative_answer


def format_sources(answer: QualitativeAnswer) -> str:
    if not answer.chunks:
        return answer.answer

    sources = "\n".join(f"  - {chunk.chunk_id} (distance: {chunk.distance:.4f})" for chunk in answer.chunks)

    return f"{answer.answer}\n\nSources:\n{sources}"

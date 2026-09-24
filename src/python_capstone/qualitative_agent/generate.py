from python_capstone.db.vectorstore import RetrievedChunk
from python_capstone.llm.base import LLMProvider
from python_capstone.qualitative_agent.prompt import build_rag_prompt


def generate_answer(llm_provider: LLMProvider, question: str, chunks: list[RetrievedChunk]) -> str:
    rag_prompt = build_rag_prompt(question=question, chunks=chunks)
    return llm_provider.generate(rag_prompt)

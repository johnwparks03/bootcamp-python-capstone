from python_capstone.db.vectorstore import RetrievedChunk

SYSTEM_INSTRUCTIONS = """You are a policy assistant. Answer the question using ONLY the context
chunks provided below — never use outside knowledge, even if you know the answer.

Rules:
- Every claim in your answer must be followed by the source tag of the chunk it came from,
  in square brackets, e.g. [pto_policy.md::1].
- If the context does not fully answer the question, say so explicitly rather than guessing
  or filling gaps with outside knowledge.
- Do not fabricate source tags. Only cite tags that appear in the context below.
"""


def format_context(chunks: list[RetrievedChunk]) -> str:
    return "\n\n".join(f"[{chunk.chunk_id}] {chunk.text}" for chunk in chunks)


def build_rag_prompt(question: str, chunks: list[RetrievedChunk]) -> str:
    context = format_context(chunks)
    return (
        f"{SYSTEM_INSTRUCTIONS}\n"
        f"Context:\n{context}\n\n"
        f"Question: {question}\n"
        f"Answer:"
    )

from python_capstone.db.vectorstore import RetrievedChunk
from python_capstone.qualitative_agent.prompt import build_rag_prompt, format_context


def make_chunk(chunk_id: str, text: str) -> RetrievedChunk:
    return RetrievedChunk(chunk_id=chunk_id, text=text, source="source.md", distance=0.1)


def test_format_context_tags_single_chunk():
    chunk = make_chunk("pto_policy.md::1", "Employees accrue 15 days of PTO annually.")
    assert format_context([chunk]) == "[pto_policy.md::1] Employees accrue 15 days of PTO annually."


def test_format_context_joins_multiple_chunks():
    chunks = [make_chunk("a::0", "First chunk."), make_chunk("b::1", "Second chunk.")]
    context = format_context(chunks)
    assert "[a::0] First chunk." in context
    assert "[b::1] Second chunk." in context


def test_format_context_empty_list():
    assert format_context([]) == ""


def test_build_rag_prompt_includes_question_and_context():
    chunk = make_chunk("pto_policy.md::1", "Employees accrue 15 days of PTO annually.")
    prompt = build_rag_prompt(question="How many vacation days?", chunks=[chunk])

    assert "How many vacation days?" in prompt
    assert "[pto_policy.md::1] Employees accrue 15 days of PTO annually." in prompt

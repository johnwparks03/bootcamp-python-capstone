from python_capstone.db.vectorstore import RetrievedChunk
from python_capstone.qualitative_agent.retrieve import MAX_RELEVANT_DISTANCE, filter_by_relevance


def make_chunk(chunk_id: str, distance: float) -> RetrievedChunk:
    return RetrievedChunk(chunk_id=chunk_id, text="text", source="source.md", distance=distance)


def test_keeps_chunks_below_threshold():
    chunks = [make_chunk("a", 0.1), make_chunk("b", 0.2)]
    assert filter_by_relevance(chunks, max_distance=0.4) == chunks


def test_drops_chunks_above_threshold():
    chunks = [make_chunk("a", 0.5), make_chunk("b", 0.6)]
    assert filter_by_relevance(chunks, max_distance=0.4) == []


def test_keeps_chunk_exactly_at_threshold():
    chunks = [make_chunk("a", 0.4)]
    assert filter_by_relevance(chunks, max_distance=0.4) == chunks


def test_filters_mixed_chunks():
    relevant = make_chunk("a", 0.2)
    irrelevant = make_chunk("b", 0.6)
    assert filter_by_relevance([relevant, irrelevant], max_distance=0.4) == [relevant]


def test_uses_default_threshold_when_not_specified():
    just_inside = make_chunk("a", MAX_RELEVANT_DISTANCE - 0.01)
    just_outside = make_chunk("b", MAX_RELEVANT_DISTANCE + 0.01)
    assert filter_by_relevance([just_inside, just_outside]) == [just_inside]

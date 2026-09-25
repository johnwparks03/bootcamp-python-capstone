import pytest

from python_capstone.llm.base import LLMProvider
from python_capstone.manager_agent import orchestrator
from python_capstone.manager_agent.orchestrator import CLARIFICATION_MESSAGE, answer_question, format_answer
from python_capstone.qualitative_agent.orchestrator import QualitativeAnswer
from python_capstone.quantitative_agent.orchestrator import QueryAnswer


class FakeLLMProvider(LLMProvider):
    """Test double: returns a scripted response for the classification call."""

    def __init__(self, response: str) -> None:
        self._response = response
        self.calls: list[str] = []

    def generate(self, prompt: str) -> str:
        self.calls.append(prompt)
        return self._response


def classification_json(
    category: str,
    reasoning: str = "test reasoning",
    quantitative_subquery: str | None = None,
    qualitative_subquery: str | None = None,
) -> str:
    return (
        '{"category": "%s", "reasoning": "%s", '
        '"quantitative_subquery": %s, "qualitative_subquery": %s}'
    ) % (
        category,
        reasoning,
        f'"{quantitative_subquery}"' if quantitative_subquery is not None else "null",
        f'"{qualitative_subquery}"' if qualitative_subquery is not None else "null",
    )


@pytest.fixture
def spy_agents(monkeypatch):
    """Replaces both sub-agent orchestrators with spies that record their
    arguments and return a canned answer, so tests only exercise the
    manager's routing/merging logic, not the SQL or RAG pipelines themselves
    (those are covered by their own test suites).
    """
    quantitative_calls: list[tuple] = []
    qualitative_calls: list[tuple] = []

    canned_quantitative = QueryAnswer(
        columns=["revenue"], rows=[(100,)], formatted_table="revenue\n100", insight="Revenue is 100."
    )
    canned_qualitative = QualitativeAnswer(chunks=[], answer="Here's the policy.", found=True)

    def fake_answer_quantitative(llm_provider, dbconn, schema, question):
        quantitative_calls.append((llm_provider, dbconn, schema, question))
        return canned_quantitative

    def fake_answer_qualitative(embedding_provider, llm_provider, collection, question):
        qualitative_calls.append((embedding_provider, llm_provider, collection, question))
        return canned_qualitative

    monkeypatch.setattr(orchestrator, "answer_quantitative", fake_answer_quantitative)
    monkeypatch.setattr(orchestrator, "answer_qualitative", fake_answer_qualitative)

    return quantitative_calls, qualitative_calls, canned_quantitative, canned_qualitative


def test_routes_to_quantitative_only(spy_agents):
    quantitative_calls, qualitative_calls, canned_quantitative, _ = spy_agents
    provider = FakeLLMProvider(classification_json("quantitative"))

    result = answer_question(provider, None, None, "SCHEMA", None, "What's our revenue?")

    assert result.category == "quantitative"
    assert result.quantitative is canned_quantitative
    assert result.qualitative is None
    assert len(quantitative_calls) == 1
    assert quantitative_calls[0][3] == "What's our revenue?"
    assert qualitative_calls == []


def test_routes_to_qualitative_only(spy_agents):
    quantitative_calls, qualitative_calls, _, canned_qualitative = spy_agents
    provider = FakeLLMProvider(classification_json("qualitative"))

    result = answer_question(provider, None, None, "SCHEMA", None, "What's our security policy?")

    assert result.category == "qualitative"
    assert result.qualitative is canned_qualitative
    assert result.quantitative is None
    assert len(qualitative_calls) == 1
    assert qualitative_calls[0][3] == "What's our security policy?"
    assert quantitative_calls == []


def test_routes_to_both_using_subqueries_not_raw_question(spy_agents):
    quantitative_calls, qualitative_calls, canned_quantitative, canned_qualitative = spy_agents
    provider = FakeLLMProvider(
        classification_json(
            "both",
            quantitative_subquery="Analyze our sales performance.",
            qualitative_subquery="What are our customer success policies?",
        )
    )

    result = answer_question(
        provider,
        None,
        None,
        "SCHEMA",
        None,
        "Analyze our sales performance and recommend policy changes based on our customer success strategies.",
    )

    assert result.category == "both"
    assert result.quantitative is canned_quantitative
    assert result.qualitative is canned_qualitative
    assert quantitative_calls[0][3] == "Analyze our sales performance."
    assert qualitative_calls[0][3] == "What are our customer success policies?"


def test_ambiguous_question_calls_neither_agent(spy_agents):
    quantitative_calls, qualitative_calls, _, _ = spy_agents
    provider = FakeLLMProvider(classification_json("ambiguous"))

    result = answer_question(provider, None, None, "SCHEMA", None, "Can you help with that thing?")

    assert result.category == "ambiguous"
    assert result.message == CLARIFICATION_MESSAGE
    assert quantitative_calls == []
    assert qualitative_calls == []


def test_malformed_classification_returns_error_and_calls_neither_agent(spy_agents):
    quantitative_calls, qualitative_calls, _, _ = spy_agents
    provider = FakeLLMProvider("not valid json")

    result = answer_question(provider, None, None, "SCHEMA", None, "Anything")

    assert result.category == "error"
    assert result.message != ""
    assert quantitative_calls == []
    assert qualitative_calls == []


def test_format_answer_quantitative_only():
    answer = orchestrator.ManagerAnswer(
        category="quantitative",
        quantitative=QueryAnswer(formatted_table="table", insight="insight"),
    )
    formatted = format_answer(answer)
    assert "From sales data:" in formatted
    assert "From policy docs:" not in formatted


def test_format_answer_qualitative_only():
    answer = orchestrator.ManagerAnswer(
        category="qualitative",
        qualitative=QualitativeAnswer(chunks=[], answer="Here's the policy.", found=True),
    )
    formatted = format_answer(answer)
    assert "From policy docs:" in formatted
    assert "From sales data:" not in formatted


def test_format_answer_both_labels_each_section():
    answer = orchestrator.ManagerAnswer(
        category="both",
        quantitative=QueryAnswer(formatted_table="table", insight="insight"),
        qualitative=QualitativeAnswer(chunks=[], answer="Here's the policy.", found=True),
    )
    formatted = format_answer(answer)
    assert "From sales data:" in formatted
    assert "From policy docs:" in formatted


def test_format_answer_ambiguous_returns_message():
    answer = orchestrator.ManagerAnswer(category="ambiguous", message=CLARIFICATION_MESSAGE)
    assert format_answer(answer) == CLARIFICATION_MESSAGE

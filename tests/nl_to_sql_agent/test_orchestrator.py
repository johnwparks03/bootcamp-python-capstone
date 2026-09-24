import sqlite3

import pytest

from python_capstone.llm.base import LLMGenerationError, LLMProvider
from python_capstone.quantitative_agent.orchestrator import answer_question


class FakeLLMProvider(LLMProvider):
    """Test double: returns a scripted sequence of responses, one per call
    to generate(). If a response is an Exception instance, it is raised
    instead of returned - lets a single test script an LLM failure at a
    specific step (e.g. the SQL call succeeds but the insight call fails).
    """

    def __init__(self, responses: list[str | Exception]) -> None:
        self._responses = list(responses)
        self.calls: list[str] = []

    def generate(self, prompt: str) -> str:
        self.calls.append(prompt)
        response = self._responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


@pytest.fixture
def memory_conn():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE products (product_id INTEGER, name TEXT, unit_price REAL)")
    conn.execute("INSERT INTO products VALUES (1, 'Mug', 16.99)")
    conn.execute("INSERT INTO products VALUES (2, 'Wallet', 49.99)")
    conn.commit()
    yield conn
    conn.close()


SCHEMA = "Table: products\n  - product_id: INTEGER\n  - name: TEXT\n  - unit_price: REAL"


def test_answer_question_happy_path(memory_conn):
    provider = FakeLLMProvider(
        responses=[
            "SELECT name, unit_price FROM products ORDER BY product_id",
            "Products range from $16.99 to $49.99.",
        ]
    )

    result = answer_question(provider, memory_conn, SCHEMA, "List all products")

    assert result.error is None
    assert result.columns == ["name", "unit_price"]
    assert result.rows == [("Mug", 16.99), ("Wallet", 49.99)]
    assert "Mug" in result.formatted_table
    assert result.insight == "Products range from $16.99 to $49.99."


def test_answer_question_strips_markdown_fences_from_sql(memory_conn):
    provider = FakeLLMProvider(
        responses=[
            "```sql\nSELECT name FROM products\n```",
            "Two products found.",
        ]
    )

    result = answer_question(provider, memory_conn, SCHEMA, "List all product names")

    assert result.error is None
    assert result.columns == ["name"]


def test_answer_question_rejects_unsafe_sql(memory_conn):
    provider = FakeLLMProvider(responses=["DELETE FROM products"])

    result = answer_question(provider, memory_conn, SCHEMA, "Delete everything")

    assert result.error is not None
    assert "safe query" in result.error
    assert result.rows == []


def test_answer_question_handles_invalid_sql(memory_conn):
    provider = FakeLLMProvider(responses=["SELECT * FROM nonexistent_table"])

    result = answer_question(provider, memory_conn, SCHEMA, "Show me nonsense")

    assert result.error is not None
    assert "invalid" in result.error


def test_answer_question_handles_llm_failure_on_sql_generation(memory_conn):
    provider = FakeLLMProvider(responses=[LLMGenerationError("503 Service Unavailable")])

    result = answer_question(provider, memory_conn, SCHEMA, "List all products")

    assert result.error is not None
    assert "unavailable" in result.error


def test_answer_question_fails_gracefully_when_insight_generation_fails(memory_conn):
    provider = FakeLLMProvider(
        responses=[
            "SELECT name FROM products",
            LLMGenerationError("503 Service Unavailable"),
        ]
    )

    result = answer_question(provider, memory_conn, SCHEMA, "List all products")

    assert result.error is None
    assert result.rows != []
    assert "unavailable" in result.insight


def test_answer_question_skips_insight_call_on_empty_results(memory_conn):
    provider = FakeLLMProvider(responses=["SELECT * FROM products WHERE product_id = 999"])

    result = answer_question(provider, memory_conn, SCHEMA, "Find product 999")

    assert result.error is None
    assert result.rows == []
    assert result.insight == "No results found for that question."
    assert len(provider.calls) == 1

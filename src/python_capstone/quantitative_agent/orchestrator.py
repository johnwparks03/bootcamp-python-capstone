import sqlite3
from dataclasses import dataclass, field

from python_capstone.db.sqldb import execute_query, format_results
from python_capstone.llm.base import LLMGenerationError, LLMProvider
from python_capstone.quantitative_agent.generate import generate_sql
from python_capstone.quantitative_agent.guardrail import UnsafeSqlError, validate_select_only
from python_capstone.quantitative_agent.insight import generate_insight


@dataclass
class QueryAnswer:
    columns: list[str] = field(default_factory=list)
    rows: list[tuple] = field(default_factory=list)
    formatted_table: str = ""
    insight: str = ""
    error: str | None = None


def answer_question(
    llm_provider: LLMProvider,
    dbconn: sqlite3.Connection,
    schema: str,
    question: str,
) -> QueryAnswer:
    try:
        raw_sql = generate_sql(llm_provider=llm_provider, schema=schema, user_question=question)
        safe_sql = validate_select_only(raw_sql)
        columns, rows = execute_query(dbconn, safe_sql)
    except UnsafeSqlError as e:
        return QueryAnswer(error=f"Couldn't generate a safe query for that question: {e}")
    except sqlite3.OperationalError as e:
        return QueryAnswer(error=f"The generated SQL was invalid: {e}")
    except LLMGenerationError as e:
        return QueryAnswer(error=f"The AI service is currently unavailable: {e}")

    formatted_table = format_results(columns, rows)

    if not rows:
        insight = "No results found for that question."
    else:
        try:
            insight = generate_insight(llm_provider, question, formatted_table)
        except LLMGenerationError:
            insight = "(Insight unavailable: the AI service is currently unavailable.)"

    return QueryAnswer(
        columns=columns,
        rows=rows,
        formatted_table=formatted_table,
        insight=insight,
    )

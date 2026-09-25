import sqlite3
from dataclasses import dataclass, field
from time import perf_counter

from python_capstone.logging_conf import get_logger
from python_capstone.db.sqldb import execute_query, format_results
from python_capstone.llm.base import LLMGenerationError, LLMProvider
from python_capstone.quantitative_agent.generate import generate_sql
from python_capstone.quantitative_agent.guardrail import UnsafeSqlError, validate_select_only
from python_capstone.quantitative_agent.insight import generate_insight

logger = get_logger(__name__)

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
    logger.info("Starting quantitative answer generation...")
    logger.info("Incoming query: %s", question)
    start_time = perf_counter()
    try:
        start_sql_generate = perf_counter()
        raw_sql = generate_sql(llm_provider=llm_provider, schema=schema, user_question=question)
        logger.info("Generated SQL: %s. Took %.3fs", raw_sql, perf_counter() - start_sql_generate)
        safe_sql = validate_select_only(raw_sql)
        start_execute_query = perf_counter()
        columns, rows = execute_query(dbconn, safe_sql)
        logger.info("Execute query took %.3fs", perf_counter() - start_execute_query)
    except UnsafeSqlError as e:
        logger.warning("Unsafe SQL rejected: %s | Reason: %s | Execution time: %.3fs", raw_sql, e, perf_counter() - start_time)
        return QueryAnswer(error=f"Couldn't generate a safe query for that question: {e}")
    except sqlite3.OperationalError as e:
        logger.warning("Invalid SQL generated: %s | Reason: %s | Execution time: %.3fs", raw_sql, e, perf_counter() - start_time)
        return QueryAnswer(error=f"The generated SQL was invalid: {e}")
    except LLMGenerationError as e:
        logger.warning("Ran into exception calling AI Service: %s Execution time: %.3fs", e, perf_counter() - start_time)
        return QueryAnswer(error=f"The AI service is currently unavailable: {e}")

    formatted_table = format_results(columns, rows)

    if not rows:
        insight = "No results found for that question."
    else:
        try:
            insight = generate_insight(llm_provider, question, formatted_table)
        except LLMGenerationError as e:
            logger.warning("Ran into exception calling AI Service for insight generation: %s | Execution time: %.3fs", e, perf_counter() - start_time)
            insight = "(Insight unavailable: the AI service is currently unavailable.)"

    logger.info("Quantitative answer generation successful! Execution time: %.3fs", perf_counter() - start_time)
    return QueryAnswer(
        columns=columns,
        rows=rows,
        formatted_table=formatted_table,
        insight=insight,
    )

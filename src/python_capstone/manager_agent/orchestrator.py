import sqlite3
from dataclasses import dataclass, field
from time import perf_counter

from chromadb.api.models.Collection import Collection

from python_capstone.logging_conf import get_logger
from python_capstone.llm.base import LLMProvider
from python_capstone.llm.embedding_base import EmbeddingProvider
from python_capstone.manager_agent.generate import ClassificationParseError, classify_question
from python_capstone.qualitative_agent.orchestrator import QualitativeAnswer, format_sources
from python_capstone.qualitative_agent.orchestrator import answer_question as answer_qualitative
from python_capstone.quantitative_agent.orchestrator import QueryAnswer
from python_capstone.quantitative_agent.orchestrator import answer_question as answer_quantitative

CLARIFICATION_MESSAGE = (
    "I'm not sure whether that's a question about our sales data, our company policies, both, "
    "or something outside what I can help with. Could you clarify what you're asking about?"
)

logger = get_logger(__name__)

@dataclass
class ManagerAnswer:
    category: str
    quantitative: QueryAnswer | None = field(default=None)
    qualitative: QualitativeAnswer | None = field(default=None)
    message: str = ""


def answer_question(
    llm_provider: LLMProvider,
    embedding_provider: EmbeddingProvider,
    dbconn: sqlite3.Connection,
    schema: str,
    collection: Collection,
    question: str,
) -> ManagerAnswer:
    try:
        classification = classify_question(llm_provider, question)
        logger.info("Classified as %s | Reasoning: %s", classification.category, classification.reasoning)
    except ClassificationParseError as e:
        logger.warning("Unable to route question %s", e)
        return ManagerAnswer(
            category="error",
            message=f"Sorry, I couldn't figure out how to route that question: {e}",
        )

    if classification.category == "quantitative":
        logger.info("Selected Quantitative Agent")
        quantitative = answer_quantitative(llm_provider, dbconn, schema, question)
        return ManagerAnswer(category="quantitative", quantitative=quantitative)

    if classification.category == "qualitative":
        logger.info("Selected Qualitative Agent")
        qualitative = answer_qualitative(embedding_provider, llm_provider, collection, question)
        return ManagerAnswer(category="qualitative", qualitative=qualitative)

    if classification.category == "both":
        logger.info("Selected Both Agents")
        assert classification.qualitative_subquery is not None
        assert classification.quantitative_subquery is not None
        
        quantitative = answer_quantitative(
            llm_provider, dbconn, schema, classification.quantitative_subquery
        )
    
        qualitative = answer_qualitative(
            embedding_provider, llm_provider, collection, classification.qualitative_subquery
        )
        return ManagerAnswer(category="both", quantitative=quantitative, qualitative=qualitative)

    return ManagerAnswer(category="ambiguous", message=CLARIFICATION_MESSAGE)

def format_answer(answer: ManagerAnswer) -> str:
    if answer.category in ("error", "ambiguous"):
        return answer.message

    if answer.category == "quantitative":
        assert answer.quantitative is not None
        return f"From sales data:\n{_format_quantitative(answer.quantitative)}"

    if answer.category == "qualitative":
        assert answer.qualitative is not None
        return f"From policy docs:\n{format_sources(answer.qualitative)}"

    assert answer.quantitative is not None
    assert answer.qualitative is not None
    quantitative_section = f"From sales data:\n{_format_quantitative(answer.quantitative)}"
    qualitative_section = f"From policy docs:\n{format_sources(answer.qualitative)}"
    return f"{quantitative_section}\n\n{qualitative_section}"


def _format_quantitative(answer: QueryAnswer) -> str:
    if answer.error is not None:
        return answer.error
    return f"{answer.formatted_table}\n\n{answer.insight}"

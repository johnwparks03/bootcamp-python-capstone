from rich.console import Console
from rich.panel import Panel

from python_capstone.config import settings
from python_capstone.db.sqldb import format_schema, introspect_schema, open_connection
from python_capstone.db.vectorstore import open_collection
from python_capstone.llm.base import LLMGenerationError
from python_capstone.llm.gemini_embedding_provider import GeminiEmbeddingProvider
from python_capstone.llm.groq_provider import GroqProvider
from python_capstone.manager_agent.generate import ClassificationParseError
from python_capstone.manager_agent.orchestrator import answer_question, format_answer
from python_capstone.quantitative_agent.guardrail import UnsafeSqlError

EXIT_COMMANDS = {"exit", "quit"}

STYLE_BY_CATEGORY = {
    "error": "red",
    "ambiguous": "yellow",
}


def repl() -> None:
    console = Console()

    llm_provider = GroqProvider(api_key=settings.groq_api_key, model=settings.groq_chat_model)
    embedding_provider = GeminiEmbeddingProvider(settings.gemini_api_key, settings.gemini_embedding_model)
    dbconn = open_connection()
    schema = format_schema(introspect_schema(dbconn))
    collection = open_collection()

    console.print("[bold cyan]Demonbreun Goods Assistant[/bold cyan] - Ask me anything! (type 'exit' to quit)\n")

    while True:
        try:
            question = console.input("[bold]> [/bold]").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\nGoodbye!")
            break

        if not question:
            continue
        if question.lower() in EXIT_COMMANDS:
            console.print("Goodbye!")
            break

        try:
            answer = answer_question(llm_provider, embedding_provider, dbconn, schema, collection, question)
            text = format_answer(answer)
            style = STYLE_BY_CATEGORY.get(answer.category, "green")
            console.print(Panel(text, title=answer.category, border_style=style))
        except (UnsafeSqlError, LLMGenerationError, ClassificationParseError) as e:
            console.print(Panel(str(e), title="error", border_style="red"))


if __name__ == "__main__":
    repl()

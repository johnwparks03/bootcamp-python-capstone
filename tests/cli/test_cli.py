import pytest
from rich.console import Console

from python_capstone import cli
from python_capstone.llm.base import LLMGenerationError
from python_capstone.manager_agent.generate import ClassificationParseError
from python_capstone.manager_agent.orchestrator import ManagerAnswer
from python_capstone.quantitative_agent.guardrail import UnsafeSqlError


class ScriptedConsole(Console):
    """Test double: feeds a scripted sequence of inputs instead of reading
    stdin, and records everything printed so tests can assert on output.
    """

    def __init__(self, inputs: list[str]) -> None:
        super().__init__(record=True)
        self._inputs = list(inputs)

    def input(self, *args, **kwargs) -> str:
        if not self._inputs:
            raise EOFError
        return self._inputs.pop(0)

    def output_text(self) -> str:
        return self.export_text(clear=False)


def run(monkeypatch, inputs: list[str], canned_answer=None, raises=None):
    """Runs run_repl with a scripted console and a stubbed answer_question,
    returning the console for output assertions plus the recorded calls.
    """
    calls: list[str] = []

    def fake_answer_question(llm_provider, embedding_provider, dbconn, schema, collection, question):
        calls.append(question)
        if raises is not None:
            raise raises
        return canned_answer

    monkeypatch.setattr(cli, "answer_question", fake_answer_question)

    console = ScriptedConsole(inputs)
    cli.run_repl(None, None, None, "SCHEMA", None, console)
    return console, calls


def test_normal_question_prints_answer_panel(monkeypatch):
    answer = ManagerAnswer(category="qualitative", message="")
    monkeypatch.setattr(cli, "format_answer", lambda a: "Here's the policy.")

    console, calls = run(monkeypatch, ["What's our security policy?", "exit"], canned_answer=answer)

    assert calls == ["What's our security policy?"]
    assert "Here's the policy." in console.output_text()
    assert "Goodbye!" in console.output_text()


def test_exit_command_breaks_loop_without_calling_answer_question(monkeypatch):
    console, calls = run(monkeypatch, ["exit"])

    assert calls == []
    assert "Goodbye!" in console.output_text()


def test_quit_command_also_exits(monkeypatch):
    console, calls = run(monkeypatch, ["quit"])

    assert calls == []
    assert "Goodbye!" in console.output_text()


def test_empty_input_reprompts_without_calling_answer_question(monkeypatch):
    answer = ManagerAnswer(category="qualitative", message="")
    monkeypatch.setattr(cli, "format_answer", lambda a: "answer text")

    console, calls = run(monkeypatch, ["", "  ", "a real question", "exit"], canned_answer=answer)

    assert calls == ["a real question"]


def test_eof_breaks_loop_cleanly(monkeypatch):
    # ScriptedConsole raises EOFError once its scripted inputs are exhausted.
    console, calls = run(monkeypatch, [])

    assert calls == []
    assert "Goodbye!" in console.output_text()


@pytest.mark.parametrize(
    "exception",
    [
        UnsafeSqlError("rejected: not a SELECT"),
        LLMGenerationError("provider timed out"),
        ClassificationParseError("malformed classification json"),
    ],
)
def test_known_exceptions_print_error_panel_and_continue(monkeypatch, exception):
    console, calls = run(monkeypatch, ["bad question", "exit"], raises=exception)

    assert calls == ["bad question"]
    assert str(exception) in console.output_text()
    assert "Goodbye!" in console.output_text()

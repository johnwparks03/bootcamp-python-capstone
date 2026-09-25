import json
import re
from dataclasses import dataclass

from python_capstone.llm.base import LLMProvider
from python_capstone.manager_agent.prompt import build_classification_prompt

FENCE_PATTERN = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE | re.MULTILINE)

VALID_CATEGORIES = {"quantitative", "qualitative", "both", "ambiguous"}


class ClassificationParseError(Exception):
    """Raised when the LLM's classification output isn't valid, well-formed JSON."""


@dataclass
class Classification:
    category: str
    reasoning: str
    quantitative_subquery: str | None = None
    qualitative_subquery: str | None = None


def strip_json_fences(text: str) -> str:
    return FENCE_PATTERN.sub("", text).strip()


def classify_question(llm_provider: LLMProvider, user_question: str) -> Classification:
    classification_prompt = build_classification_prompt(user_question)
    response = llm_provider.generate(classification_prompt)
    raw_json = strip_json_fences(response)

    try:
        parsed = json.loads(raw_json)
    except json.JSONDecodeError as e:
        raise ClassificationParseError(f"LLM output wasn't valid JSON: {e}") from e

    category = parsed.get("category")
    if category not in VALID_CATEGORIES:
        raise ClassificationParseError(f"LLM returned an unrecognized category: {category!r}")

    reasoning = parsed.get("reasoning")
    if not isinstance(reasoning, str):
        raise ClassificationParseError("LLM output is missing a string 'reasoning' field.")

    quantitative_subquery = parsed.get("quantitative_subquery")
    qualitative_subquery = parsed.get("qualitative_subquery")

    if category == "both" and (not quantitative_subquery or not qualitative_subquery):
        raise ClassificationParseError(
            "Category 'both' requires both 'quantitative_subquery' and 'qualitative_subquery' to be set."
        )

    return Classification(
        category=category,
        reasoning=reasoning,
        quantitative_subquery=quantitative_subquery,
        qualitative_subquery=qualitative_subquery,
    )

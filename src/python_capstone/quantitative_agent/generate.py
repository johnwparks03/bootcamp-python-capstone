import re

from python_capstone.llm.base import LLMProvider
from python_capstone.quantitative_agent.prompt import build_sql_prompt

FENCE_PATTERN = re.compile(r"^```(?:sql)?\s*|\s*```$", re.IGNORECASE | re.MULTILINE)


def strip_sql_fences(text: str) -> str:
    return FENCE_PATTERN.sub("", text).strip()


def generate_sql(llm_provider: LLMProvider, schema: str, user_question: str) -> str:
    sql_prompt = build_sql_prompt(schema=schema, user_question=user_question)
    response = llm_provider.generate(sql_prompt)
    return strip_sql_fences(response)

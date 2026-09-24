from python_capstone.llm.base import LLMProvider

INSIGHT_INSTRUCTIONS = """You are analyzing the results of a SQL query that answered a user's question.
Only describe what is actually shown in the data below. Do not invent numbers, trends, or facts
that are not present in the results. If the results are empty, say so plainly instead of guessing.

Question: {question}

Results:
{formatted_results}

Write a 1-2 sentence insight summarizing what this data shows.
"""


def generate_insight(llm_provider: LLMProvider, question: str, formatted_results: str) -> str:
    prompt = INSIGHT_INSTRUCTIONS.format(question=question, formatted_results=formatted_results)
    return llm_provider.generate(prompt).strip()

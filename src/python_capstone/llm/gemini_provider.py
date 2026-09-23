"""Gemini implementation of the LLMProvider interface."""

from __future__ import annotations

from langchain_google_genai import ChatGoogleGenerativeAI

from python_capstone.llm.base import LLMProvider


class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str, model: str) -> None:
        self._client = ChatGoogleGenerativeAI(model=model, google_api_key=api_key)

    def generate(self, prompt: str) -> str:
        response = self._client.invoke(prompt)
        content = response.content

        if isinstance(content, str):
            return content

        # Newer Gemini responses come back as a list of content blocks
        # (e.g. {"type": "text", "text": "..."}) instead of a flat string.
        text_blocks = [
            block["text"]
            for block in content
            if isinstance(block, dict) and block.get("type") == "text"
        ]
        return "".join(text_blocks)

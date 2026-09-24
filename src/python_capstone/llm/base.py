"""Abstract interface for LLM providers.

Every agent (Manager, RAG, NL-to-SQL) depends on this interface, never on a
concrete provider like Gemini. Swapping the underlying model later means
writing one new subclass here, not touching agent code.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class LLMGenerationError(Exception):
    """Raised when a provider fails to generate a response (timeout, rate
    limit, service unavailable, etc). Providers should catch their own
    underlying SDK/API exceptions and re-raise this instead, so callers never
    need to know which concrete provider is in use.
    """


class LLMProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Send a fully-assembled prompt to the LLM and return the raw text
        response. Callers are responsible for combining any system
        instructions with the user query before calling this method.
        """
        raise NotImplementedError

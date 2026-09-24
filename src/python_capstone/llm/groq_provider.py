from python_capstone.llm.base import LLMGenerationError, LLMProvider
from pydantic import SecretStr
from groq import Groq


class GroqProvider(LLMProvider):
    def __init__(self, api_key: SecretStr, model: str) -> None:
        self._client = Groq(api_key=api_key.get_secret_value())
        self._model = model

    def generate(self, prompt: str) -> str:
        try:
            response = self._client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model=self._model
            )
        except Exception as e:
            raise LLMGenerationError(f"Groq API call failed: {e}") from e

        content = response.choices[0].message.content

        if content is None:
            raise LLMGenerationError(f"Groq API returned no response")

        return content

        
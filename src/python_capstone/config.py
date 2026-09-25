"""Central application settings, loaded from environment variables / .env."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
from pydantic import SecretStr

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    gemini_api_key: SecretStr
    groq_api_key: SecretStr
    gemini_chat_model: str
    groq_chat_model: str
    gemini_embedding_model: str
    chroma_persist_dir: Path
    sqlite_db_path: Path
    log_level: str

    @classmethod
    def from_env(cls) -> "Settings":
        raw_gemini_api_key = os.environ.get("GEMINI_API_KEY", "")
        if not raw_gemini_api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not set. Copy .env.example to .env and fill it in."
            )

        raw_groq_api_key = os.environ.get("GROQ_API_KEY", "")

        return cls(
            gemini_api_key=SecretStr(raw_gemini_api_key),
            groq_api_key=SecretStr(raw_groq_api_key),
            gemini_chat_model=os.environ.get("GEMINI_CHAT_MODEL", "gemini-3.6-flash"),
            groq_chat_model=os.environ.get("GROQ_CHAT_MODEL", "llama-3.3-70b-versatile"),
            gemini_embedding_model=os.environ.get(
                "GEMINI_EMBEDDING_MODEL", "models/gemini-embedding-001"
            ),
            chroma_persist_dir=PROJECT_ROOT
            / os.environ.get("CHROMA_PERSIST_DIR", "chroma_db"),
            sqlite_db_path=PROJECT_ROOT / os.environ.get("SQLITE_DB_PATH", "data/seed.db"),
            log_level=os.environ.get("LOG_LEVEL", "INFO"),
        )


settings = Settings.from_env()

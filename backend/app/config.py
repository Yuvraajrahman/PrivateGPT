from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM provider: openai_compatible (LM Studio, vLLM, etc.) | ollama
    llm_provider: Literal["openai_compatible", "ollama"] = "openai_compatible"
    openai_base_url: str = "http://127.0.0.1:1234/v1"
    openai_api_key: str = "lm-studio"
    chat_model: str = "local-model"

    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "llama3.1"

    chroma_path: Path = Path("./data/chroma")
    embedding_model: str = "all-MiniLM-L6-v2"
    cross_encoder_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    chunk_size: int = 900
    chunk_overlap: int = 120
    k_dense: int = 20
    k_sparse: int = 20
    k_fused: int = 12
    k_final: int = 5
    rrf_k: int = 60

    notion_token: str | None = None
    notion_page_id: str | None = None

    # Backend API auth (required)
    rag_api_key: str | None = None

    cors_origins: str = (
        "http://localhost:3000,http://127.0.0.1:3000,"
        "http://localhost:3001,http://127.0.0.1:3001,"
        "http://localhost:3002,http://127.0.0.1:3002,"
        "http://localhost:3003,http://127.0.0.1:3003,"
        "http://localhost:3004,http://127.0.0.1:3004,"
        "http://localhost:3005,http://127.0.0.1:3005"
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


def get_settings() -> Settings:
    return Settings()

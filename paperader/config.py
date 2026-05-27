from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="PAPERADER_",
        env_file=".env",
        env_file_encoding="utf-8",
    )

    # Database
    database_url: str = f"sqlite:///{PROJECT_ROOT}/data/paperader.db"

    # Storage
    pdf_storage_path: str = str(PROJECT_ROOT / "data" / "pdfs")

    # LLM
    llm_model: str = "openrouter/google/gemini-2.5-flash"
    llm_api_key: str = ""
    llm_base_url: str = "https://openrouter.ai/api/v1"

    # Semantic Scholar
    s2_api_key: str = ""

    # Server
    server_host: str = "0.0.0.0"
    server_port: int = 8000
    debug: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()

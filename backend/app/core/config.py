from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./voiceforge.db"
    upload_dir: Path = Path("uploads")
    export_dir: Path = Path("exports")
    review_quality_threshold: int = 60
    kafka_bootstrap_servers: str = "localhost:9092"
    enable_whisper: bool = False
    openai_api_key: str | None = None
    transcription_model: str = "whisper-1"
    enable_fasttext_language: bool = True
    fasttext_language_model_path: Path = Path("models/lid.176.ftz")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    settings.export_dir.mkdir(parents=True, exist_ok=True)
    settings.fasttext_language_model_path.parent.mkdir(parents=True, exist_ok=True)
    return settings

"""
Application configuration management.
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import model_validator


class Settings(BaseSettings):
    """Application settings."""

    # API settings
    api_title: str = "LLM Test Generator"
    api_version: str = "0.1.0"
    api_description: str = "Generate and grade educational tests using LLMs"
    default_provider: str = "openai"

    # OpenAI settings
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"  # Lightweight model for testing
    openai_base_url: str | None = None

    # Yandex Cloud settings
    yandex_cloud_api_key: str = ""
    yandex_cloud_api_key_identifier: str = ""
    yandex_folder_id: str = ""
    yandex_model: str = "yandexgpt-lite"  # yandexgpt-lite or yandexgpt

    # Generation defaults
    default_total_questions: int = 20
    default_single_choice_ratio: float = 0.7
    default_multiple_choice_ratio: float = 0.3

    # Output settings
    data_dir: str = "data"  # root for runtime artifacts
    output_dir: str = "out"  # exams/grades; normalized under data_dir unless absolute
    uploads_dir: str = "uploads"  # uploaded markdown; normalized under data_dir unless absolute

    @model_validator(mode="after")
    def _normalize_paths(self) -> 'Settings':
        """Place output/uploads under data_dir when defaults are used."""
        data_root = Path(self.data_dir)

        # Normalize output_dir if default-like
        output_path = Path(self.output_dir)
        if output_path == Path("out"):
            output_path = data_root / "out"

        # Normalize uploads_dir if default-like
        uploads_path = Path(self.uploads_dir)
        if uploads_path == Path("uploads"):
            uploads_path = data_root / "uploads"

        self.output_dir = str(output_path)
        self.uploads_dir = str(uploads_path)
        self.data_dir = str(data_root)
        return self

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields in .env


# Global settings instance
settings = Settings()

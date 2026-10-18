"""Application Configuration & Environment Variables.

What this file does:
    Loads and validates configuration settings from environment variables or a .env file
    using Pydantic BaseSettings. It provides centralized access to the database connection
    string, Gemini API credentials, model name, and timeout parameters.

Connections with other files:
    - app/storage.py: Uses 'settings.sqlalchemy_url' to create the SQLAlchemy engine.
    - app/services/llm.py: Uses 'settings.gemini_api_key', 'settings.gemini_model',
      and 'settings.llm_timeout_seconds' to initialize and query Google Gemini.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration class for application settings."""
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://chatbot:chatbot@localhost:5432/chatbot"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash-lite"
    llm_timeout_seconds: float = 1.3

    @property
    def sqlalchemy_url(self) -> str:
        """Adapts connection URL to use the psycopg driver required by SQLAlchemy.

        What it does:
            PaaS providers like Render, Neon, or Supabase provide URLs starting with
            'postgres://' or 'postgresql://'. This method normalizes them to
            'postgresql+psycopg://' so SQLAlchemy can connect seamlessly.

        Returns:
            str: A formatted database connection string compatible with psycopg 3.
        """
        url = self.database_url
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+psycopg://", 1)
        elif url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+psycopg://", 1)
        return url


settings = Settings()
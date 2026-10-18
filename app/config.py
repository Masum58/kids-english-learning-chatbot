from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://chatbot:chatbot@localhost:5432/chatbot"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash-lite"
    llm_timeout_seconds: float = 1.3

    @property
    def sqlalchemy_url(self) -> str:
        # Neon/Render "postgresql://" dey, amader driver er jonno "+psycopg" lage
        url = self.database_url
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+psycopg://", 1)
        elif url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+psycopg://", 1)
        return url


settings = Settings()
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    app_env: str = "dev"
    log_level: str = "INFO"

    llm_provider: str = "openai"
    openai_api_key: str | None = None

    database_url: str = "sqlite:///./demo.db"

settings = Settings()

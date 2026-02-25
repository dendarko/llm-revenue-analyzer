from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

from llm_revenue_analyzer.core.version import __version__


class Settings(BaseSettings):
    app_name: str = "llm-revenue-analyzer"
    environment: str = "dev"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"

    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/llm_revenue_analyzer"
    pricing_file: str = "data/pricing.yaml"

    anomaly_multiplier: float = 2.0
    anomaly_lookback_days: int = 7

    default_budget_soft_limit_pct: float = 0.8
    hard_limit_reject_default: bool = True

    metrics_namespace: str = "llm_revenue"

    api_base_url: str = "http://localhost:8000"
    seed_days: int = 14
    seed_llm_events: int = 420
    seed_revenue_events: int = 140
    seed_random_seed: int = 42

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="LRA_",
        extra="ignore",
    )

    @property
    def pricing_path(self) -> Path:
        return Path(self.pricing_file)

    @property
    def version(self) -> str:
        return __version__

    @property
    def is_postgres(self) -> bool:
        return self.database_url.startswith("postgresql")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

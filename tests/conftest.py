from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from llm_revenue_analyzer.api.app import create_app
from llm_revenue_analyzer.api.deps import get_session
from llm_revenue_analyzer.core.settings import Settings, get_settings
from llm_revenue_analyzer.store.db import create_all, get_session_factory, reset_engine


@pytest.fixture()
def test_settings(tmp_path: Path) -> Settings:
    db_path = tmp_path / "test.db"
    reset_engine()
    get_settings.cache_clear()
    return Settings(
        database_url=f"sqlite+pysqlite:///{db_path}",
        pricing_file="data/pricing.yaml",
        debug=False,
        anomaly_multiplier=1000.0,
        anomaly_lookback_days=7,
    )


@pytest.fixture()
def client(test_settings: Settings) -> Generator[TestClient, None, None]:
    create_all(test_settings)
    session_factory = get_session_factory(test_settings)

    app = create_app(test_settings)

    def _get_settings_override() -> Settings:
        return test_settings

    def _get_session_override():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_settings] = _get_settings_override
    app.dependency_overrides[get_session] = _get_session_override

    with TestClient(app) as test_client:
        yield test_client

    reset_engine()
    get_settings.cache_clear()

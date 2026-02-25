from __future__ import annotations

from fastapi import FastAPI

from llm_revenue_analyzer.api.middleware import request_id_middleware
from llm_revenue_analyzer.api.routes_budgets import router as budgets_router
from llm_revenue_analyzer.api.routes_events import router as events_router
from llm_revenue_analyzer.api.routes_metrics import router as analytics_router
from llm_revenue_analyzer.api.routes_system import router as system_router
from llm_revenue_analyzer.core.logging import configure_logging
from llm_revenue_analyzer.core.settings import Settings, get_settings
from llm_revenue_analyzer.observability.metrics import instrument_request


def create_app(settings: Settings | None = None) -> FastAPI:
    active_settings = settings or get_settings()
    configure_logging(active_settings.log_level)

    app = FastAPI(title=active_settings.app_name, version=active_settings.version)
    app.middleware("http")(request_id_middleware)
    app.middleware("http")(instrument_request)

    @app.get("/")
    def root() -> dict[str, str]:
        return {"service": active_settings.app_name, "version": active_settings.version}

    app.include_router(system_router)
    app.include_router(events_router)
    app.include_router(budgets_router)
    app.include_router(analytics_router)
    return app


app = create_app()

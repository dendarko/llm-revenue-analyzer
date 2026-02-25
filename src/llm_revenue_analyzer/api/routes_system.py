from __future__ import annotations

from fastapi import APIRouter, Depends, Response
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from llm_revenue_analyzer.api.deps import get_session
from llm_revenue_analyzer.api.schemas import HealthResponse, VersionResponse
from llm_revenue_analyzer.core.settings import Settings, get_settings
from llm_revenue_analyzer.observability.metrics import render_metrics_text

router = APIRouter(tags=["system"])


@router.get("/health", response_model=HealthResponse)
def health(session: Session = Depends(get_session)) -> HealthResponse:
    try:
        session.execute(text("SELECT 1"))
        return HealthResponse(status="ok", database="ok")
    except SQLAlchemyError:
        return HealthResponse(status="degraded", database="error")


@router.get("/version", response_model=VersionResponse)
def version(settings: Settings = Depends(get_settings)) -> VersionResponse:
    return VersionResponse(service=settings.app_name, version=settings.version)


@router.get("/metrics", include_in_schema=False)
def prometheus_metrics() -> Response:
    body, content_type = render_metrics_text()
    return Response(content=body, media_type=content_type)

from __future__ import annotations

from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from llm_revenue_analyzer.analytics import AnalyticsService
from llm_revenue_analyzer.api.deps import get_session
from llm_revenue_analyzer.api.schemas import BreakdownResponse, SummaryMetricsResponse

router = APIRouter(prefix="/metrics", tags=["analytics"])


@router.get("/summary", response_model=SummaryMetricsResponse)
def metrics_summary(
    tenant_id: str,
    from_ts: datetime = Query(alias="from"),
    to_ts: datetime = Query(alias="to"),
    session: Session = Depends(get_session),
) -> SummaryMetricsResponse:
    data = AnalyticsService(session).summary(tenant_id=tenant_id, from_ts=from_ts, to_ts=to_ts)
    return SummaryMetricsResponse.model_validate(data)


@router.get("/by-model", response_model=BreakdownResponse)
def metrics_by_model(
    tenant_id: str,
    from_ts: datetime = Query(alias="from"),
    to_ts: datetime = Query(alias="to"),
    granularity: Literal["total", "day"] = "total",
    session: Session = Depends(get_session),
) -> BreakdownResponse:
    rows = AnalyticsService(session).by_model(tenant_id=tenant_id, from_ts=from_ts, to_ts=to_ts, granularity=granularity)
    return BreakdownResponse.model_validate(
        {"tenant_id": tenant_id, "from": from_ts, "to": to_ts, "granularity": granularity, "rows": rows}
    )


@router.get("/by-feature", response_model=BreakdownResponse)
def metrics_by_feature(
    tenant_id: str,
    from_ts: datetime = Query(alias="from"),
    to_ts: datetime = Query(alias="to"),
    granularity: Literal["total", "day"] = "total",
    session: Session = Depends(get_session),
) -> BreakdownResponse:
    rows = AnalyticsService(session).by_feature(
        tenant_id=tenant_id,
        from_ts=from_ts,
        to_ts=to_ts,
        granularity=granularity,
    )
    return BreakdownResponse.model_validate(
        {"tenant_id": tenant_id, "from": from_ts, "to": to_ts, "granularity": granularity, "rows": rows}
    )

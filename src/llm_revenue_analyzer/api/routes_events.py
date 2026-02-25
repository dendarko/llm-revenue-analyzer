from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from llm_revenue_analyzer.analytics import AnomalyDetector
from llm_revenue_analyzer.api.deps import get_cost_calculator, get_session
from llm_revenue_analyzer.api.schemas import (
    LLMEventIn,
    LLMIngestResponse,
    RevenueEventIn,
    RevenueIngestResponse,
)
from llm_revenue_analyzer.budgets import BudgetService
from llm_revenue_analyzer.core.logging import get_logger
from llm_revenue_analyzer.core.settings import Settings, get_settings
from llm_revenue_analyzer.observability.metrics import record_llm_ingest, record_revenue_ingest
from llm_revenue_analyzer.pricing import CostCalculator, PricingError, PricingNotFound
from llm_revenue_analyzer.store.models import LLMEvent, RevenueEvent
from llm_revenue_analyzer.store.repos import TenantRepo

logger = get_logger(__name__)
router = APIRouter(prefix="/events", tags=["events"])


@router.post("/llm", response_model=LLMIngestResponse)
def ingest_llm_event(
    payload: LLMEventIn,
    request: Request,
    session: Session = Depends(get_session),
    cost_calculator: CostCalculator = Depends(get_cost_calculator),
    settings: Settings = Depends(get_settings),
) -> LLMIngestResponse:
    _ = request
    tenant_repo = TenantRepo(session)
    budget_service = BudgetService(session)

    try:
        computed = payload.cost_usd is None
        try:
            cost_usd = (
                cost_calculator.compute_cost_usd(
                    provider=payload.provider,
                    model=payload.model,
                    prompt_tokens=payload.prompt_tokens,
                    completion_tokens=payload.completion_tokens,
                )
                if computed
                else Decimal(str(payload.cost_usd))
            )
        except PricingNotFound as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
        except PricingError as exc:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc

        tenant_repo.ensure(payload.tenant_id)
        evaluation = budget_service.evaluate_llm_cost(payload.tenant_id, cost_usd, now=payload.timestamp)
        if not evaluation.allowed:
            session.commit()
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "message": evaluation.warning or "Hard budget limit exceeded",
                    "guardrail_status": evaluation.status,
                    "projected_spend_usd": evaluation.projected_spend_usd,
                    "monthly_budget_usd": evaluation.monthly_budget_usd,
                },
            )

        event = LLMEvent(
            timestamp=payload.timestamp,
            tenant_id=payload.tenant_id,
            user_id=payload.user_id,
            request_id=payload.request_id,
            model=payload.model,
            provider=payload.provider,
            prompt_tokens=payload.prompt_tokens,
            completion_tokens=payload.completion_tokens,
            total_tokens=payload.total_tokens or (payload.prompt_tokens + payload.completion_tokens),
            latency_ms=payload.latency_ms,
            status=payload.status,
            cost_usd=cost_usd,
            feature=payload.feature,
            metadata_json=payload.metadata_json,
        )
        session.add(event)
        session.flush()

        anomaly = AnomalyDetector(
            session=session,
            multiplier=settings.anomaly_multiplier,
            lookback_days=settings.anomaly_lookback_days,
        ).check_daily_cost_spike(payload.tenant_id, now=payload.timestamp)

        session.commit()
        record_llm_ingest(float(cost_usd))
        logger.info(
            "llm_event_ingested",
            extra={
                "extra": {
                    "tenant_id": payload.tenant_id,
                    "request_id": payload.request_id,
                    "event_id": event.id,
                    "cost_usd": float(cost_usd),
                    "guardrail_status": evaluation.status,
                }
            },
        )
        return LLMIngestResponse(
            event_id=event.id,
            request_id=payload.request_id,
            cost_usd=float(cost_usd),
            cost_source="computed" if computed else "supplied",
            guardrail_status=evaluation.status,
            warning=evaluation.warning,
            anomaly_warning=anomaly.message,
        )
    except HTTPException:
        session.rollback()
        raise
    except Exception:
        session.rollback()
        logger.exception(
            "llm_event_ingest_failed",
            extra={"extra": {"tenant_id": payload.tenant_id, "request_id": payload.request_id}},
        )
        raise


@router.post("/revenue", response_model=RevenueIngestResponse)
def ingest_revenue_event(
    payload: RevenueEventIn,
    session: Session = Depends(get_session),
) -> RevenueIngestResponse:
    tenant_repo = TenantRepo(session)
    try:
        tenant_repo.ensure(payload.tenant_id)
        event = RevenueEvent(
            timestamp=payload.timestamp,
            tenant_id=payload.tenant_id,
            user_id=payload.user_id,
            amount_usd=Decimal(str(payload.amount_usd)),
            currency=payload.currency,
            source=payload.source,
            metadata_json=payload.metadata_json,
        )
        session.add(event)
        session.flush()
        session.commit()
        record_revenue_ingest(float(event.amount_usd))
        return RevenueIngestResponse(event_id=event.id)
    except Exception:
        session.rollback()
        logger.exception("revenue_event_ingest_failed", extra={"extra": {"tenant_id": payload.tenant_id}})
        raise

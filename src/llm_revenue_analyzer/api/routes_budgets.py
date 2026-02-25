from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from llm_revenue_analyzer.api.deps import get_session
from llm_revenue_analyzer.api.schemas import (
    BudgetSetRequest,
    BudgetSetResponse,
    BudgetStatusResponse,
)
from llm_revenue_analyzer.budgets import BudgetService
from llm_revenue_analyzer.store.repos import TenantRepo

router = APIRouter(prefix="/budgets", tags=["budgets"])


@router.post("/set", response_model=BudgetSetResponse)
def set_budget(payload: BudgetSetRequest, session: Session = Depends(get_session)) -> BudgetSetResponse:
    tenant_repo = TenantRepo(session)
    tenant_repo.ensure(payload.tenant_id)
    service = BudgetService(session)
    budget = service.set_budget(
        tenant_id=payload.tenant_id,
        monthly_budget_usd=Decimal(str(payload.monthly_budget_usd)),
        hard_limit=payload.hard_limit,
        soft_limit_pct=payload.soft_limit_pct,
    )
    session.commit()
    return BudgetSetResponse(
        tenant_id=budget.tenant_id,
        monthly_budget_usd=float(budget.monthly_budget_usd),
        hard_limit=bool(budget.hard_limit),
        soft_limit_pct=float(budget.soft_limit_pct),
        created_at=budget.created_at,
    )


@router.get("/status", response_model=BudgetStatusResponse)
def budget_status(tenant_id: str, session: Session = Depends(get_session)) -> BudgetStatusResponse:
    service = BudgetService(session)
    data = service.get_status(tenant_id)
    return BudgetStatusResponse.model_validate(data)

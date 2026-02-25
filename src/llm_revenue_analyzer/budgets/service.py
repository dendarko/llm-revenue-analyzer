from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from llm_revenue_analyzer.store.models import Alert, Budget
from llm_revenue_analyzer.store.repos import AlertRepo, BudgetRepo, LLMEventRepo, RevenueEventRepo


@dataclass(frozen=True)
class BudgetEvaluation:
    allowed: bool
    status: str
    warning: str | None
    projected_spend_usd: float
    current_spend_usd: float
    monthly_budget_usd: float | None
    soft_limit_pct: float | None


class BudgetLimitExceeded(Exception):
    def __init__(self, message: str, evaluation: BudgetEvaluation) -> None:
        super().__init__(message)
        self.evaluation = evaluation


class BudgetService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.budgets = BudgetRepo(session)
        self.llm_events = LLMEventRepo(session)
        self.revenue_events = RevenueEventRepo(session)
        self.alerts = AlertRepo(session)

    def set_budget(
        self,
        tenant_id: str,
        monthly_budget_usd: Decimal,
        hard_limit: bool,
        soft_limit_pct: float,
    ) -> Budget:
        return self.budgets.upsert(
            tenant_id=tenant_id,
            monthly_budget_usd=monthly_budget_usd,
            hard_limit=hard_limit,
            soft_limit_pct=soft_limit_pct,
        )

    def evaluate_llm_cost(self, tenant_id: str, new_cost_usd: Decimal, now: datetime | None = None) -> BudgetEvaluation:
        reference = (now or datetime.now(UTC)).astimezone(UTC)
        budget = self.budgets.get(tenant_id)
        current_spend = self.llm_events.month_cost_sum(tenant_id, reference)
        projected = current_spend + new_cost_usd

        if budget is None:
            return BudgetEvaluation(
                allowed=True,
                status="no_budget",
                warning=None,
                projected_spend_usd=float(projected),
                current_spend_usd=float(current_spend),
                monthly_budget_usd=None,
                soft_limit_pct=None,
            )

        soft_threshold = budget.monthly_budget_usd * Decimal(str(budget.soft_limit_pct))
        if projected > budget.monthly_budget_usd and budget.hard_limit:
            message = (
                f"Hard budget limit exceeded for tenant {tenant_id}: projected={float(projected):.4f} "
                f"budget={float(budget.monthly_budget_usd):.4f}"
            )
            self.alerts.create(
                tenant_id=tenant_id,
                alert_type="budget_hard_limit",
                severity="critical",
                message=message,
                metadata_json={
                    "current_spend_usd": float(current_spend),
                    "projected_spend_usd": float(projected),
                    "monthly_budget_usd": float(budget.monthly_budget_usd),
                },
            )
            return BudgetEvaluation(
                allowed=False,
                status="hard_limit_exceeded",
                warning=message,
                projected_spend_usd=float(projected),
                current_spend_usd=float(current_spend),
                monthly_budget_usd=float(budget.monthly_budget_usd),
                soft_limit_pct=float(budget.soft_limit_pct),
            )

        if projected >= soft_threshold:
            message = (
                f"Soft budget threshold reached for tenant {tenant_id}: projected={float(projected):.4f} "
                f"soft_limit={float(soft_threshold):.4f}"
            )
            self.alerts.create(
                tenant_id=tenant_id,
                alert_type="budget_soft_limit",
                severity="warning",
                message=message,
                metadata_json={
                    "current_spend_usd": float(current_spend),
                    "projected_spend_usd": float(projected),
                    "monthly_budget_usd": float(budget.monthly_budget_usd),
                    "soft_limit_pct": float(budget.soft_limit_pct),
                },
            )
            return BudgetEvaluation(
                allowed=True,
                status="soft_limit_exceeded",
                warning=message,
                projected_spend_usd=float(projected),
                current_spend_usd=float(current_spend),
                monthly_budget_usd=float(budget.monthly_budget_usd),
                soft_limit_pct=float(budget.soft_limit_pct),
            )

        return BudgetEvaluation(
            allowed=True,
            status="ok",
            warning=None,
            projected_spend_usd=float(projected),
            current_spend_usd=float(current_spend),
            monthly_budget_usd=float(budget.monthly_budget_usd),
            soft_limit_pct=float(budget.soft_limit_pct),
        )

    def get_status(self, tenant_id: str, now: datetime | None = None) -> dict[str, object]:
        reference = (now or datetime.now(UTC)).astimezone(UTC)
        budget = self.budgets.get(tenant_id)
        spend = self.llm_events.month_cost_sum(tenant_id, reference)
        revenue = self.revenue_events.month_revenue_sum(tenant_id, reference)
        if budget is None:
            return {
                "tenant_id": tenant_id,
                "status": "no_budget",
                "month": reference.strftime("%Y-%m"),
                "monthly_budget_usd": None,
                "monthly_spend_usd": float(spend),
                "monthly_revenue_usd": float(revenue),
                "remaining_budget_usd": None,
                "soft_limit_pct": None,
                "hard_limit": None,
                "alerts": [self._serialize_alert(a) for a in self.alerts.list_recent(tenant_id, limit=10)],
            }

        budget_value = Decimal(budget.monthly_budget_usd)
        remaining = budget_value - spend
        soft_threshold = budget_value * Decimal(str(budget.soft_limit_pct))
        if spend > budget_value:
            status = "hard_limit_exceeded" if budget.hard_limit else "over_budget"
        elif spend >= soft_threshold:
            status = "soft_limit_exceeded"
        else:
            status = "ok"

        return {
            "tenant_id": tenant_id,
            "status": status,
            "month": reference.strftime("%Y-%m"),
            "monthly_budget_usd": float(budget_value),
            "monthly_spend_usd": float(spend),
            "monthly_revenue_usd": float(revenue),
            "remaining_budget_usd": float(remaining),
            "soft_limit_pct": float(budget.soft_limit_pct),
            "hard_limit": bool(budget.hard_limit),
            "alerts": [self._serialize_alert(a) for a in self.alerts.list_recent(tenant_id, limit=10)],
        }

    @staticmethod
    def _serialize_alert(alert: Alert) -> dict[str, object]:
        return {
            "id": alert.id,
            "type": alert.type,
            "severity": alert.severity,
            "message": alert.message,
            "created_at": alert.created_at,
            "metadata_json": alert.metadata_json,
        }

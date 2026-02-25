from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import Select, and_, func, select
from sqlalchemy.orm import Session

from llm_revenue_analyzer.store.models import Alert, Budget, LLMEvent, RevenueEvent, Tenant


def month_bounds(reference: datetime) -> tuple[datetime, datetime]:
    ref = reference.astimezone(UTC)
    start = datetime(ref.year, ref.month, 1, tzinfo=UTC)
    if ref.month == 12:
        end = datetime(ref.year + 1, 1, 1, tzinfo=UTC)
    else:
        end = datetime(ref.year, ref.month + 1, 1, tzinfo=UTC)
    return start, end


def day_bounds(day: date) -> tuple[datetime, datetime]:
    start = datetime.combine(day, time.min, tzinfo=UTC)
    end = start + timedelta(days=1)
    return start, end


class TenantRepo:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, tenant_id: str) -> Tenant | None:
        return self.session.get(Tenant, tenant_id)

    def ensure(self, tenant_id: str, name: str | None = None) -> Tenant:
        tenant = self.get(tenant_id)
        if tenant is None:
            tenant = Tenant(id=tenant_id, name=name or tenant_id)
            self.session.add(tenant)
            self.session.flush()
        elif name and tenant.name != name:
            tenant.name = name
        return tenant

    def list_all(self) -> list[Tenant]:
        return list(self.session.scalars(select(Tenant).order_by(Tenant.id)))


class LLMEventRepo:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, event: LLMEvent) -> LLMEvent:
        self.session.add(event)
        self.session.flush()
        return event

    def month_cost_sum(self, tenant_id: str, reference: datetime) -> Decimal:
        start, end = month_bounds(reference)
        stmt = select(func.coalesce(func.sum(LLMEvent.cost_usd), 0)).where(
            and_(LLMEvent.tenant_id == tenant_id, LLMEvent.timestamp >= start, LLMEvent.timestamp < end)
        )
        value = self.session.scalar(stmt)
        return Decimal(value or 0)

    def list_for_window(
        self,
        tenant_id: str,
        from_ts: datetime,
        to_ts: datetime,
    ) -> list[LLMEvent]:
        stmt = (
            select(LLMEvent)
            .where(
                and_(LLMEvent.tenant_id == tenant_id, LLMEvent.timestamp >= from_ts, LLMEvent.timestamp < to_ts)
            )
            .order_by(LLMEvent.timestamp.asc())
        )
        return list(self.session.scalars(stmt))

    def list_daily_costs(
        self,
        tenant_id: str,
        from_ts: datetime,
        to_ts: datetime,
    ) -> list[tuple[date, Decimal]]:
        rows = self.list_for_window(tenant_id=tenant_id, from_ts=from_ts, to_ts=to_ts)
        buckets: dict[date, Decimal] = {}
        for row in rows:
            key = row.timestamp.astimezone(UTC).date()
            buckets[key] = buckets.get(key, Decimal("0")) + row.cost_usd
        return sorted(buckets.items(), key=lambda item: item[0])


class RevenueEventRepo:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, event: RevenueEvent) -> RevenueEvent:
        self.session.add(event)
        self.session.flush()
        return event

    def list_for_window(self, tenant_id: str, from_ts: datetime, to_ts: datetime) -> list[RevenueEvent]:
        stmt = (
            select(RevenueEvent)
            .where(
                and_(
                    RevenueEvent.tenant_id == tenant_id,
                    RevenueEvent.timestamp >= from_ts,
                    RevenueEvent.timestamp < to_ts,
                )
            )
            .order_by(RevenueEvent.timestamp.asc())
        )
        return list(self.session.scalars(stmt))

    def month_revenue_sum(self, tenant_id: str, reference: datetime) -> Decimal:
        start, end = month_bounds(reference)
        stmt = select(func.coalesce(func.sum(RevenueEvent.amount_usd), 0)).where(
            and_(RevenueEvent.tenant_id == tenant_id, RevenueEvent.timestamp >= start, RevenueEvent.timestamp < end)
        )
        value = self.session.scalar(stmt)
        return Decimal(value or 0)


class BudgetRepo:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, tenant_id: str) -> Budget | None:
        return self.session.get(Budget, tenant_id)

    def upsert(
        self,
        tenant_id: str,
        monthly_budget_usd: Decimal,
        hard_limit: bool,
        soft_limit_pct: float,
    ) -> Budget:
        budget = self.get(tenant_id)
        if budget is None:
            budget = Budget(
                tenant_id=tenant_id,
                monthly_budget_usd=monthly_budget_usd,
                hard_limit=hard_limit,
                soft_limit_pct=soft_limit_pct,
            )
            self.session.add(budget)
        else:
            budget.monthly_budget_usd = monthly_budget_usd
            budget.hard_limit = hard_limit
            budget.soft_limit_pct = soft_limit_pct
        self.session.flush()
        return budget


class AlertRepo:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        tenant_id: str,
        alert_type: str,
        severity: str,
        message: str,
        metadata_json: dict[str, Any] | None = None,
    ) -> Alert:
        alert = Alert(
            tenant_id=tenant_id,
            type=alert_type,
            severity=severity,
            message=message,
            metadata_json=metadata_json,
        )
        self.session.add(alert)
        self.session.flush()
        return alert

    def list_recent(self, tenant_id: str, limit: int = 20) -> list[Alert]:
        stmt: Select[tuple[Alert]] = (
            select(Alert)
            .where(Alert.tenant_id == tenant_id)
            .order_by(Alert.created_at.desc())
            .limit(limit)
        )
        return list(self.session.scalars(stmt))

    def list_all(self, tenant_id: str | None = None) -> list[Alert]:
        stmt = select(Alert)
        if tenant_id is not None:
            stmt = stmt.where(Alert.tenant_id == tenant_id)
        stmt = stmt.order_by(Alert.created_at.desc())
        return list(self.session.scalars(stmt))

from __future__ import annotations

import random
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import delete

from llm_revenue_analyzer.analytics import AnomalyDetector
from llm_revenue_analyzer.budgets import BudgetService
from llm_revenue_analyzer.core.settings import get_settings
from llm_revenue_analyzer.pricing import CostCalculator, PricingCatalog
from llm_revenue_analyzer.store.db import get_session_factory
from llm_revenue_analyzer.store.models import Alert, Budget, LLMEvent, RevenueEvent, Tenant
from llm_revenue_analyzer.store.repos import AlertRepo, TenantRepo

TENANTS = [
    {"id": "tenant-alpha", "name": "Tenant Alpha", "budget": 0.35, "hard_limit": False, "soft": 0.8},
    {"id": "tenant-beta", "name": "Tenant Beta", "budget": 0.20, "hard_limit": False, "soft": 0.75},
]
FEATURES = ["chat", "search", "copilot", "classification"]
MODELS = [
    ("openai", "gpt-4o-mini"),
    ("openai", "gpt-4.1-mini"),
    ("anthropic", "claude-3-5-haiku"),
    ("google", "gemini-2.0-flash"),
]
REVENUE_SOURCES = ["subscription", "usage", "enterprise-addon"]


def _reset_tables(session) -> None:
    for model in (Alert, LLMEvent, RevenueEvent, Budget, Tenant):
        session.execute(delete(model))
    session.commit()


def _seed_budgets(session) -> None:
    tenant_repo = TenantRepo(session)
    budget_service = BudgetService(session)
    for tenant in TENANTS:
        tenant_repo.ensure(tenant["id"], tenant["name"])
        budget_service.set_budget(
            tenant_id=tenant["id"],
            monthly_budget_usd=Decimal(str(tenant["budget"])),
            hard_limit=bool(tenant["hard_limit"]),
            soft_limit_pct=float(tenant["soft"]),
        )
    session.commit()


def _generate_llm_events(session, cost_calc: CostCalculator, seed: int, count: int, days: int) -> int:
    rng = random.Random(seed)
    now = datetime.now(UTC).replace(minute=0, second=0, microsecond=0)
    inserted = 0
    for idx in range(count):
        tenant = TENANTS[idx % len(TENANTS)]
        day_offset = rng.randint(0, days - 1)
        base_ts = now - timedelta(days=day_offset)
        ts = base_ts.replace(hour=rng.randint(0, 23)) + timedelta(minutes=rng.randint(0, 59))
        provider, model = rng.choice(MODELS)
        feature = rng.choice(FEATURES)
        prompt_tokens = rng.randint(200, 6000)
        completion_tokens = rng.randint(100, 2500)
        if tenant["id"] == "tenant-beta" and day_offset == 0 and idx % 12 == 1:
            provider, model = ("openai", "gpt-4.1")
            prompt_tokens *= 200
            completion_tokens *= 250
        cost_usd = cost_calc.compute_cost_usd(provider, model, prompt_tokens, completion_tokens)
        event = LLMEvent(
            timestamp=ts,
            tenant_id=tenant["id"],
            user_id=f"user-{rng.randint(1, 25)}",
            request_id=f"seed-{idx:05d}",
            model=model,
            provider=provider,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            latency_ms=rng.randint(120, 4000),
            status="success" if rng.random() > 0.06 else "error",
            cost_usd=cost_usd,
            feature=feature,
            metadata_json={"seed": True, "day_offset": day_offset},
        )
        session.add(event)
        inserted += 1
    session.commit()
    return inserted


def _generate_revenue_events(session, seed: int, count: int, days: int) -> int:
    rng = random.Random(seed + 99)
    now = datetime.now(UTC).replace(minute=0, second=0, microsecond=0)
    inserted = 0
    for idx in range(count):
        tenant = TENANTS[idx % len(TENANTS)]
        day_offset = rng.randint(0, days - 1)
        base_ts = now - timedelta(days=day_offset)
        ts = base_ts.replace(hour=rng.randint(0, 23)) + timedelta(minutes=rng.randint(0, 59))
        feature = rng.choice(FEATURES)
        amount = round(rng.uniform(1.0, 50.0), 2)
        if tenant["id"] == "tenant-beta" and day_offset == 0 and idx % 9 == 0:
            amount = round(amount * 0.5, 2)
        event = RevenueEvent(
            timestamp=ts,
            tenant_id=tenant["id"],
            user_id=f"user-{rng.randint(1, 25)}",
            amount_usd=Decimal(str(amount)),
            currency="USD",
            source=rng.choice(REVENUE_SOURCES),
            metadata_json={"seed": True, "feature": feature},
        )
        session.add(event)
        inserted += 1
    session.commit()
    return inserted


def _create_budget_alerts(session) -> None:
    budget_service = BudgetService(session)
    alerts = AlertRepo(session)
    for tenant in TENANTS:
        status = budget_service.get_status(tenant["id"])
        if status["status"] in {"soft_limit_exceeded", "hard_limit_exceeded", "over_budget"}:
            alerts.create(
                tenant_id=tenant["id"],
                alert_type="budget_status_snapshot",
                severity="warning" if status["status"] != "hard_limit_exceeded" else "critical",
                message=f"Seed snapshot budget status: {status['status']}",
                metadata_json={
                    "monthly_spend_usd": status["monthly_spend_usd"],
                    "monthly_budget_usd": status["monthly_budget_usd"],
                },
            )
    session.commit()


def _run_anomalies(session) -> None:
    settings = get_settings()
    detector = AnomalyDetector(session, settings.anomaly_multiplier, settings.anomaly_lookback_days)
    for tenant in TENANTS:
        detector.check_daily_cost_spike(tenant["id"])
    session.commit()


def main() -> None:
    settings = get_settings()
    catalog = PricingCatalog.from_yaml(settings.pricing_path)
    cost_calc = CostCalculator(catalog)
    session_factory = get_session_factory(settings)
    with session_factory() as session:
        _reset_tables(session)
        _seed_budgets(session)
        llm_inserted = _generate_llm_events(
            session,
            cost_calc=cost_calc,
            seed=settings.seed_random_seed,
            count=settings.seed_llm_events,
            days=settings.seed_days,
        )
        revenue_inserted = _generate_revenue_events(
            session,
            seed=settings.seed_random_seed,
            count=settings.seed_revenue_events,
            days=settings.seed_days,
        )
        _run_anomalies(session)
        _create_budget_alerts(session)
        print(f"Seeded tenants={len(TENANTS)} llm_events={llm_inserted} revenue_events={revenue_inserted}")


if __name__ == "__main__":
    main()

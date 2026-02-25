from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from math import ceil
from statistics import mean
from typing import Any, Literal

from sqlalchemy.orm import Session

from llm_revenue_analyzer.store.repos import LLMEventRepo, RevenueEventRepo

Granularity = Literal["total", "day"]


@dataclass(frozen=True)
class Window:
    from_ts: datetime
    to_ts: datetime

    @classmethod
    def normalize(cls, from_ts: datetime, to_ts: datetime) -> Window:
        start = _to_utc(from_ts)
        end = _to_utc(to_ts)
        if end <= start:
            raise ValueError("'to' must be after 'from'")
        return cls(from_ts=start, to_ts=end)


def _to_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _decimal(value: Any) -> Decimal:
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _quantize_money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.000001"))


def _p95(values: list[int]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, ceil(0.95 * len(ordered)) - 1)
    return float(ordered[index])


class AnalyticsService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.llm_repo = LLMEventRepo(session)
        self.revenue_repo = RevenueEventRepo(session)

    def summary(self, tenant_id: str, from_ts: datetime, to_ts: datetime) -> dict[str, object]:
        window = Window.normalize(from_ts, to_ts)
        llm_events = self.llm_repo.list_for_window(tenant_id, window.from_ts, window.to_ts)
        revenue_events = self.revenue_repo.list_for_window(tenant_id, window.from_ts, window.to_ts)

        requests = len(llm_events)
        errors = sum(1 for e in llm_events if e.status.lower() != "success")
        total_cost = sum((e.cost_usd for e in llm_events), Decimal("0"))
        total_revenue = sum((e.amount_usd for e in revenue_events), Decimal("0"))
        latency_values = [e.latency_ms for e in llm_events]

        return {
            "tenant_id": tenant_id,
            "from": window.from_ts,
            "to": window.to_ts,
            "requests": requests,
            "tokens": sum(e.total_tokens for e in llm_events),
            "prompt_tokens": sum(e.prompt_tokens for e in llm_events),
            "completion_tokens": sum(e.completion_tokens for e in llm_events),
            "cost_usd": float(_quantize_money(total_cost)),
            "revenue_usd": float(_quantize_money(total_revenue)),
            "margin_usd": float(_quantize_money(total_revenue - total_cost)),
            "error_rate": (errors / requests) if requests else 0.0,
            "avg_latency_ms": float(mean(latency_values)) if latency_values else None,
            "p95_latency_ms": _p95(latency_values),
            "daily": [
                {
                    "day": day.isoformat(),
                    "cost_usd": float(_quantize_money(cost)),
                }
                for day, cost in self.llm_repo.list_daily_costs(tenant_id, window.from_ts, window.to_ts)
            ],
        }

    def by_model(
        self,
        tenant_id: str,
        from_ts: datetime,
        to_ts: datetime,
        granularity: Granularity = "total",
    ) -> list[dict[str, Any]]:
        window = Window.normalize(from_ts, to_ts)
        llm_events = self.llm_repo.list_for_window(tenant_id, window.from_ts, window.to_ts)
        buckets: dict[tuple[str, ...], dict[str, Any]] = {}
        for e in llm_events:
            day_key = e.timestamp.astimezone(UTC).date().isoformat() if granularity == "day" else None
            key = (e.provider, e.model, day_key or "")
            if key not in buckets:
                buckets[key] = {
                    "provider": e.provider,
                    "model": e.model,
                    "day": day_key,
                    "requests": 0,
                    "errors": 0,
                    "tokens": 0,
                    "cost_usd": Decimal("0"),
                    "latencies": [],
                }
            b = buckets[key]
            b["requests"] = int(b["requests"]) + 1
            b["errors"] = int(b["errors"]) + (0 if e.status.lower() == "success" else 1)
            b["tokens"] = int(b["tokens"]) + e.total_tokens
            b["cost_usd"] = _decimal(b["cost_usd"]) + e.cost_usd
            cast_latencies = b["latencies"]
            if isinstance(cast_latencies, list):
                cast_latencies.append(e.latency_ms)

        result: list[dict[str, Any]] = []
        for bucket in buckets.values():
            latencies = bucket.pop("latencies")
            errors = int(bucket.pop("errors"))
            requests = int(bucket["requests"])
            result.append(
                {
                    **bucket,
                    "cost_usd": float(_quantize_money(_decimal(bucket["cost_usd"]))),
                    "error_rate": (errors / requests) if requests else 0.0,
                    "avg_latency_ms": float(mean(latencies)) if latencies else None,
                    "p95_latency_ms": _p95(latencies),
                }
            )
        result.sort(key=lambda row: ((row.get("day") or ""), -float(row["cost_usd"]), str(row["model"])))
        return result

    def by_feature(
        self,
        tenant_id: str,
        from_ts: datetime,
        to_ts: datetime,
        granularity: Granularity = "total",
    ) -> list[dict[str, object]]:
        window = Window.normalize(from_ts, to_ts)
        llm_events = self.llm_repo.list_for_window(tenant_id, window.from_ts, window.to_ts)
        revenue_events = self.revenue_repo.list_for_window(tenant_id, window.from_ts, window.to_ts)

        buckets: dict[tuple[str, ...], dict[str, Any]] = {}

        def ensure_bucket(feature: str, day: str | None) -> dict[str, Any]:
            key = (feature, day or "")
            if key not in buckets:
                buckets[key] = {
                    "feature": feature,
                    "day": day,
                    "requests": 0,
                    "errors": 0,
                    "tokens": 0,
                    "cost_usd": Decimal("0"),
                    "revenue_usd": Decimal("0"),
                    "latencies": [],
                }
            return buckets[key]

        for e in llm_events:
            day_key = e.timestamp.astimezone(UTC).date().isoformat() if granularity == "day" else None
            b = ensure_bucket(e.feature, day_key)
            b["requests"] = int(b["requests"]) + 1
            b["errors"] = int(b["errors"]) + (0 if e.status.lower() == "success" else 1)
            b["tokens"] = int(b["tokens"]) + e.total_tokens
            b["cost_usd"] = _decimal(b["cost_usd"]) + e.cost_usd
            latencies = b["latencies"]
            if isinstance(latencies, list):
                latencies.append(e.latency_ms)

        for revenue_event in revenue_events:
            feature = str((revenue_event.metadata_json or {}).get("feature", "unattributed"))
            day_key = (
                revenue_event.timestamp.astimezone(UTC).date().isoformat()
                if granularity == "day"
                else None
            )
            b = ensure_bucket(feature, day_key)
            b["revenue_usd"] = _decimal(b["revenue_usd"]) + revenue_event.amount_usd

        result: list[dict[str, Any]] = []
        for bucket in buckets.values():
            latencies = bucket.pop("latencies")
            errors = int(bucket.pop("errors"))
            requests = int(bucket["requests"])
            cost = _decimal(bucket["cost_usd"])
            revenue = _decimal(bucket["revenue_usd"])
            result.append(
                {
                    **bucket,
                    "cost_usd": float(_quantize_money(cost)),
                    "revenue_usd": float(_quantize_money(revenue)),
                    "margin_usd": float(_quantize_money(revenue - cost)),
                    "error_rate": (errors / requests) if requests else 0.0,
                    "avg_latency_ms": float(mean(latencies)) if latencies else None,
                    "p95_latency_ms": _p95(latencies),
                }
            )
        result.sort(key=lambda row: ((row.get("day") or ""), -float(row["cost_usd"]), str(row["feature"])))
        return result

    def cost_history(self, tenant_id: str, days: int, until: datetime | None = None) -> list[tuple[date, Decimal]]:
        anchor = _to_utc(until or datetime.now(UTC))
        start = (anchor - timedelta(days=days)).replace(hour=0, minute=0, second=0, microsecond=0)
        end = (anchor + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        return self.llm_repo.list_daily_costs(tenant_id, start, end)

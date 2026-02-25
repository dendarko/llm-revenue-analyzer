from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from llm_revenue_analyzer.analytics.service import AnalyticsService
from llm_revenue_analyzer.store.repos import AlertRepo


@dataclass(frozen=True)
class AnomalyCheckResult:
    triggered: bool
    today_cost_usd: float
    baseline_avg_usd: float
    threshold_usd: float
    message: str | None = None


class AnomalyDetector:
    def __init__(self, session: Session, multiplier: float, lookback_days: int) -> None:
        self.session = session
        self.multiplier = multiplier
        self.lookback_days = lookback_days
        self.analytics = AnalyticsService(session)
        self.alerts = AlertRepo(session)

    def check_daily_cost_spike(self, tenant_id: str, now: datetime | None = None) -> AnomalyCheckResult:
        now_utc = (now or datetime.now(UTC)).astimezone(UTC)
        today = now_utc.date()
        history = self.analytics.cost_history(tenant_id, days=self.lookback_days + 1, until=now_utc)
        buckets = {day: cost for day, cost in history}
        today_cost = buckets.get(today, Decimal("0"))
        baseline_days = [today - timedelta(days=offset) for offset in range(1, self.lookback_days + 1)]
        baseline_values = [buckets[d] for d in baseline_days if d in buckets]
        if not baseline_values:
            return AnomalyCheckResult(False, float(today_cost), 0.0, 0.0)

        baseline_avg = sum(baseline_values, Decimal("0")) / Decimal(len(baseline_values))
        threshold = baseline_avg * Decimal(str(self.multiplier))
        if baseline_avg > 0 and today_cost > threshold:
            metadata = {
                "date": today.isoformat(),
                "today_cost_usd": float(today_cost),
                "baseline_avg_usd": float(baseline_avg),
                "multiplier": self.multiplier,
            }
            recent = self.alerts.list_recent(tenant_id, limit=50)
            already_exists = any(
                a.type == "cost_anomaly"
                and isinstance(a.metadata_json, dict)
                and a.metadata_json.get("date") == today.isoformat()
                for a in recent
            )
            message = (
                f"Daily LLM cost anomaly detected: today={float(today_cost):.4f} USD exceeds "
                f"{self.multiplier:.2f}x 7-day avg={float(baseline_avg):.4f} USD"
            )
            if not already_exists:
                self.alerts.create(
                    tenant_id=tenant_id,
                    alert_type="cost_anomaly",
                    severity="warning",
                    message=message,
                    metadata_json=metadata,
                )
            return AnomalyCheckResult(True, float(today_cost), float(baseline_avg), float(threshold), message)

        return AnomalyCheckResult(False, float(today_cost), float(baseline_avg), float(threshold))

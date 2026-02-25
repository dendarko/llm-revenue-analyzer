from __future__ import annotations

from datetime import UTC, datetime, timedelta

import httpx

from llm_revenue_analyzer.core.settings import get_settings

TENANTS = ["tenant-alpha", "tenant-beta"]


def _fmt_money(value) -> str:
    if value is None:
        return "n/a"
    return f"${float(value):,.4f}"


def main() -> None:
    settings = get_settings()
    base_url = settings.api_base_url.rstrip("/")
    now = datetime.now(UTC)
    from_ts = (now - timedelta(days=settings.seed_days)).isoformat()
    to_ts = now.isoformat()

    with httpx.Client(base_url=base_url, timeout=30.0) as client:
        health = client.get("/health")
        health.raise_for_status()
        print("Health:", health.json())

        for tenant_id in TENANTS:
            print(f"\n=== {tenant_id} ===")
            summary = client.get(
                "/metrics/summary",
                params={"tenant_id": tenant_id, "from": from_ts, "to": to_ts},
            )
            summary.raise_for_status()
            summary_json = summary.json()
            print(
                "Summary:",
                {
                    "requests": summary_json["requests"],
                    "cost_usd": _fmt_money(summary_json["cost_usd"]),
                    "revenue_usd": _fmt_money(summary_json["revenue_usd"]),
                    "margin_usd": _fmt_money(summary_json["margin_usd"]),
                    "error_rate": round(summary_json["error_rate"], 4),
                    "p95_latency_ms": summary_json["p95_latency_ms"],
                },
            )

            by_model = client.get(
                "/metrics/by-model",
                params={"tenant_id": tenant_id, "from": from_ts, "to": to_ts},
            )
            by_model.raise_for_status()
            top_models = by_model.json()["rows"][:3]
            print("Top models:")
            for row in top_models:
                print(
                    f"  - {row['provider']}/{row['model']} cost={_fmt_money(row['cost_usd'])} "
                    f"requests={row['requests']} tokens={row['tokens']}"
                )

            budget = client.get("/budgets/status", params={"tenant_id": tenant_id})
            budget.raise_for_status()
            budget_json = budget.json()
            print(
                "Budget:",
                {
                    "status": budget_json["status"],
                    "monthly_budget_usd": _fmt_money(budget_json["monthly_budget_usd"]),
                    "monthly_spend_usd": _fmt_money(budget_json["monthly_spend_usd"]),
                    "remaining_budget_usd": _fmt_money(budget_json["remaining_budget_usd"]),
                },
            )
            print("Alerts:")
            for alert in budget_json.get("alerts", [])[:5]:
                print(f"  - [{alert['severity']}] {alert['type']}: {alert['message']}")


if __name__ == "__main__":
    main()

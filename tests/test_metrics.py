from __future__ import annotations

from datetime import UTC, datetime, timedelta


def test_metrics_summary_shape(client) -> None:
    now = datetime.now(UTC)

    llm_payload = {
        "timestamp": now.isoformat(),
        "tenant_id": "tenant-metrics",
        "user_id": "user-1",
        "request_id": "req-m1",
        "provider": "openai",
        "model": "gpt-4o-mini",
        "prompt_tokens": 1000,
        "completion_tokens": 500,
        "latency_ms": 300,
        "status": "success",
        "feature": "chat",
    }
    revenue_payload = {
        "timestamp": now.isoformat(),
        "tenant_id": "tenant-metrics",
        "user_id": "user-1",
        "amount_usd": 5.0,
        "currency": "USD",
        "source": "usage",
        "metadata_json": {"feature": "chat"},
    }

    assert client.post("/events/llm", json=llm_payload).status_code == 200
    assert client.post("/events/revenue", json=revenue_payload).status_code == 200

    from_ts = (now - timedelta(days=1)).isoformat()
    to_ts = (now + timedelta(days=1)).isoformat()
    response = client.get(
        "/metrics/summary",
        params={"tenant_id": "tenant-metrics", "from": from_ts, "to": to_ts},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["tenant_id"] == "tenant-metrics"
    assert set(["requests", "cost_usd", "revenue_usd", "margin_usd", "error_rate"]).issubset(body.keys())

    by_model = client.get(
        "/metrics/by-model",
        params={"tenant_id": "tenant-metrics", "from": from_ts, "to": to_ts},
    )
    assert by_model.status_code == 200
    assert isinstance(by_model.json()["rows"], list)

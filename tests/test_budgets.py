from __future__ import annotations

from datetime import UTC, datetime


def test_budget_hard_limit_blocks(client) -> None:
    budget = {
        "tenant_id": "tenant-hard",
        "monthly_budget_usd": 0.001,
        "hard_limit": True,
        "soft_limit_pct": 0.5,
    }
    set_resp = client.post("/budgets/set", json=budget)
    assert set_resp.status_code == 200, set_resp.text

    payload = {
        "timestamp": datetime.now(UTC).isoformat(),
        "tenant_id": "tenant-hard",
        "user_id": "user-1",
        "request_id": "req-hard-1",
        "provider": "openai",
        "model": "gpt-4.1",
        "prompt_tokens": 2000,
        "completion_tokens": 1000,
        "latency_ms": 700,
        "status": "success",
        "feature": "copilot",
    }
    response = client.post("/events/llm", json=payload)
    assert response.status_code == 403
    detail = response.json()["detail"]
    assert detail["guardrail_status"] == "hard_limit_exceeded"

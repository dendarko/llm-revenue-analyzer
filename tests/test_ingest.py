from __future__ import annotations

from datetime import UTC, datetime


def test_ingest_llm_computes_cost(client) -> None:
    payload = {
        "timestamp": datetime.now(UTC).isoformat(),
        "tenant_id": "tenant-a",
        "user_id": "user-1",
        "request_id": "req-1",
        "provider": "openai",
        "model": "gpt-4o-mini",
        "prompt_tokens": 1000,
        "completion_tokens": 1000,
        "latency_ms": 500,
        "status": "success",
        "feature": "chat",
        "metadata_json": {"test": True},
    }
    response = client.post("/events/llm", json=payload)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["cost_source"] == "computed"
    assert body["cost_usd"] == 0.00075
    assert body["accepted"] is True

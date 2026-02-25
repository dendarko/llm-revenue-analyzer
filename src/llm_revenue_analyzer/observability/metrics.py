from __future__ import annotations

from collections.abc import Awaitable, Callable
from time import perf_counter
from typing import Any

from fastapi import Request, Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Histogram,
    generate_latest,
    make_asgi_app,
)

REQUEST_COUNT = Counter(
    "lra_http_requests_total",
    "HTTP requests",
    ["method", "path", "status_code"],
)
REQUEST_LATENCY = Histogram(
    "lra_http_request_latency_seconds",
    "HTTP request latency",
    ["method", "path"],
)
EVENTS_INGESTED = Counter(
    "lra_events_ingested_total",
    "Business events ingested",
    ["event_type"],
)
LLM_COST_TOTAL = Counter(
    "lra_llm_cost_usd_total",
    "Total ingested LLM cost in USD",
)
REVENUE_TOTAL = Counter(
    "lra_revenue_usd_total",
    "Total ingested revenue in USD",
)


def metrics_asgi_app() -> Any:
    return make_asgi_app()


async def instrument_request(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    start = perf_counter()
    path = request.url.path
    method = request.method
    response = await call_next(request)
    elapsed = perf_counter() - start
    REQUEST_COUNT.labels(method=method, path=path, status_code=str(response.status_code)).inc()
    REQUEST_LATENCY.labels(method=method, path=path).observe(elapsed)
    return response


def record_llm_ingest(cost_usd: float) -> None:
    EVENTS_INGESTED.labels(event_type="llm").inc()
    LLM_COST_TOTAL.inc(cost_usd)


def record_revenue_ingest(amount_usd: float) -> None:
    EVENTS_INGESTED.labels(event_type="revenue").inc()
    REVENUE_TOTAL.inc(amount_usd)


def render_metrics_text() -> tuple[bytes, str]:
    return generate_latest(), CONTENT_TYPE_LATEST

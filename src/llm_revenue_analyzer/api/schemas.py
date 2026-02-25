from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class APIModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)


class LLMEventIn(APIModel):
    timestamp: datetime
    tenant_id: str = Field(min_length=1, max_length=64)
    user_id: str = Field(min_length=1, max_length=128)
    request_id: str = Field(min_length=1, max_length=128)
    model: str = Field(min_length=1, max_length=128)
    provider: str = Field(min_length=1, max_length=128)
    prompt_tokens: int = Field(ge=0)
    completion_tokens: int = Field(ge=0)
    total_tokens: int | None = Field(default=None, ge=0)
    latency_ms: int = Field(ge=0)
    status: str = Field(min_length=1, max_length=32)
    cost_usd: float | None = Field(default=None, ge=0)
    feature: str = Field(min_length=1, max_length=128)
    metadata_json: dict[str, Any] | None = None

    @model_validator(mode="after")
    def validate_totals(self) -> LLMEventIn:
        expected = self.prompt_tokens + self.completion_tokens
        if self.total_tokens is None:
            self.total_tokens = expected
        elif self.total_tokens != expected:
            raise ValueError("total_tokens must equal prompt_tokens + completion_tokens")
        return self


class RevenueEventIn(APIModel):
    timestamp: datetime
    tenant_id: str = Field(min_length=1, max_length=64)
    user_id: str = Field(min_length=1, max_length=128)
    amount_usd: float = Field(gt=0)
    currency: str = Field(default="USD", min_length=3, max_length=16)
    source: str = Field(min_length=1, max_length=128)
    metadata_json: dict[str, Any] | None = None

    @field_validator("currency")
    @classmethod
    def upper_currency(cls, value: str) -> str:
        return value.upper()


class LLMIngestResponse(APIModel):
    accepted: bool = True
    event_id: int
    request_id: str
    cost_usd: float
    cost_source: Literal["supplied", "computed"]
    guardrail_status: str
    warning: str | None = None
    anomaly_warning: str | None = None


class RevenueIngestResponse(APIModel):
    accepted: bool = True
    event_id: int


class BudgetSetRequest(APIModel):
    tenant_id: str = Field(min_length=1, max_length=64)
    monthly_budget_usd: float = Field(gt=0)
    hard_limit: bool = True
    soft_limit_pct: float = Field(default=0.8, gt=0, le=1.0)


class AlertOut(APIModel):
    id: int
    type: str
    severity: str
    message: str
    created_at: datetime
    metadata_json: dict[str, Any] | None = None


class BudgetStatusResponse(APIModel):
    tenant_id: str
    status: str
    month: str
    monthly_budget_usd: float | None
    monthly_spend_usd: float
    monthly_revenue_usd: float
    remaining_budget_usd: float | None
    soft_limit_pct: float | None
    hard_limit: bool | None
    alerts: list[AlertOut]


class BudgetSetResponse(APIModel):
    tenant_id: str
    monthly_budget_usd: float
    hard_limit: bool
    soft_limit_pct: float
    created_at: datetime


class SummaryMetricsResponse(APIModel):
    tenant_id: str
    from_: datetime = Field(alias="from")
    to: datetime
    requests: int
    tokens: int
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float
    revenue_usd: float
    margin_usd: float
    error_rate: float
    avg_latency_ms: float | None
    p95_latency_ms: float | None
    daily: list[dict[str, Any]]


class BreakdownRow(APIModel):
    provider: str | None = None
    model: str | None = None
    feature: str | None = None
    day: str | None = None
    requests: int
    tokens: int
    cost_usd: float
    revenue_usd: float | None = None
    margin_usd: float | None = None
    error_rate: float
    avg_latency_ms: float | None
    p95_latency_ms: float | None


class BreakdownResponse(APIModel):
    tenant_id: str
    from_: datetime = Field(alias="from")
    to: datetime
    granularity: str
    rows: list[BreakdownRow]


class HealthResponse(APIModel):
    status: str
    database: str


class VersionResponse(APIModel):
    service: str
    version: str

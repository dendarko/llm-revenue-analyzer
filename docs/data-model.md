# Data Model

## Tables

- `tenants`
  - `id` (PK)
  - `name`
  - `created_at`
- `llm_events`
  - `timestamp`, `tenant_id`, `user_id`, `request_id`
  - `model`, `provider`, `feature`, `status`
  - `prompt_tokens`, `completion_tokens`, `total_tokens`
  - `latency_ms`, `cost_usd`, `metadata_json`
- `revenue_events`
  - `timestamp`, `tenant_id`, `user_id`
  - `amount_usd`, `currency`, `source`, `metadata_json`
- `budgets`
  - `tenant_id` (PK/FK)
  - `monthly_budget_usd`, `hard_limit`, `soft_limit_pct`, `created_at`
- `alerts`
  - `tenant_id`, `type`, `severity`, `message`, `created_at`, `metadata_json`

## Notes

- `metadata_json` is JSON for flexible tenant/application attributes.
- LLM event `cost_usd` is always stored explicitly (either supplied or computed during ingest).
- Indexes prioritize time-window analytics and tenant-scoped lookups.

## Migration Strategy

- Alembic migration `0001_initial` creates all required tables + indexes.
- Future schema changes should be additive where possible to preserve API/report compatibility.

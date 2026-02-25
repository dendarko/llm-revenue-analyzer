# Budgets and Alerts

## Budget Guardrails

`POST /budgets/set` configures a tenant monthly LLM spend budget.

Fields:

- `monthly_budget_usd`
- `hard_limit` (boolean reject behavior)
- `soft_limit_pct` (fraction, e.g. `0.8`)

## Guardrail Behavior

- Soft limit exceeded:
  - event is accepted
  - API response includes warning + `guardrail_status=soft_limit_exceeded`
  - alert stored (`budget_soft_limit`)
- Hard limit exceeded and `hard_limit=true`:
  - API returns `403`
  - alert stored (`budget_hard_limit`)
  - event is rejected

## Alerts

Alert types used by the system:

- `budget_soft_limit`
- `budget_hard_limit`
- `cost_anomaly`
- `budget_status_snapshot` (seed/demo convenience)

## Anomaly Detection

During LLM ingest and during demo seeding checks:

- compute today's LLM cost
- compute average of prior `N` days (default 7)
- create `cost_anomaly` alert if `today_cost > multiplier * avg_prior_days`

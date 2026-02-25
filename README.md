# llm-revenue-analyzer

Production-grade local demo and API for LLM cost + revenue analytics (FastAPI + Postgres + Alembic + Prometheus).

## Features

- LLM usage and revenue event ingestion
- Cost computation from configurable pricing catalog (`data/pricing.yaml`)
- Budget guardrails (soft warning + hard reject)
- Analytics by tenant/model/feature/time window
- Simple anomaly detection for daily cost spikes
- Prometheus metrics + structured logs with request IDs
- Docker Compose local stack (`api` + `postgres`)

## Quickstart

1. Create env file and install deps.

```bash
cp .env.example .env
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

2. Start Postgres + API.

```bash
make up
```

3. Seed demo data (~560 events total across 14 days, 2 tenants).

```bash
make seed
```

4. Run demo summary printer.

```bash
make demo
```

5. Run checks.

```bash
make lint
make typecheck
make test
```

## API Endpoints

- `POST /events/llm`
- `POST /events/revenue`
- `GET /metrics/summary?tenant_id=&from=&to=`
- `GET /metrics/by-model?tenant_id=&from=&to=&granularity=total|day`
- `GET /metrics/by-feature?tenant_id=&from=&to=&granularity=total|day`
- `GET /budgets/status?tenant_id=`
- `POST /budgets/set`
- `GET /health`
- `GET /version`
- `GET /metrics` (Prometheus)

## Example Requests

See `examples/`.

## Docs

- `docs/architecture.md`
- `docs/data-model.md`
- `docs/pricing.md`
- `docs/budgets-alerts.md`
- `docs/runbooks.md`

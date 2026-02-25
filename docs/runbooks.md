# Runbooks

## Local Start

```bash
make up
make seed
make demo
```

## Health Checks

- `GET /health`
- `GET /version`
- `GET /metrics` (Prometheus scrape)

## Common Ops Tasks

### Update pricing

1. Edit `data/pricing.yaml`
2. Run `make test`
3. Rebuild/restart API if running in Docker: `make up`

### Reset demo data

`make seed` clears and reseeds all app tables.

### Inspect budgets

```bash
curl "http://localhost:8000/budgets/status?tenant_id=tenant-alpha"
```

### Troubleshooting

- `403` on `POST /events/llm`: tenant likely exceeded hard budget limit.
- `400` on `POST /events/llm`: missing pricing config for `(provider, model)`.
- `/health` degraded: verify Postgres is running and `LRA_DATABASE_URL` is correct.
- Empty analytics: verify `from`/`to` are UTC ISO timestamps and include seeded date range.

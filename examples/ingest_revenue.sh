curl -X POST http://localhost:8000/events/revenue \
  -H "Content-Type: application/json" \
  -d '{
    "timestamp":"2026-02-25T12:05:00Z",
    "tenant_id":"tenant-alpha",
    "user_id":"user-1",
    "amount_usd":12.50,
    "currency":"USD",
    "source":"usage",
    "metadata_json":{"feature":"chat"}
  }'

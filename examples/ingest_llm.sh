curl -X POST http://localhost:8000/events/llm \
  -H "Content-Type: application/json" \
  -d '{
    "timestamp":"2026-02-25T12:00:00Z",
    "tenant_id":"tenant-alpha",
    "user_id":"user-1",
    "request_id":"req-123",
    "provider":"openai",
    "model":"gpt-4o-mini",
    "prompt_tokens":1200,
    "completion_tokens":400,
    "latency_ms":850,
    "status":"success",
    "feature":"chat",
    "metadata_json":{"channel":"web"}
  }'

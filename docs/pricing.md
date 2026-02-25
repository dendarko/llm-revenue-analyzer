# Pricing

## Source of Truth

Pricing is configured in `data/pricing.yaml` and loaded at runtime.

## Schema (per provider/model)

- `input_per_1k_tokens`
- `output_per_1k_tokens`
- `currency` (default `USD`)

## Cost Computation

If `POST /events/llm` omits `cost_usd`, the service computes:

- `prompt_tokens / 1000 * input_per_1k_tokens`
- `completion_tokens / 1000 * output_per_1k_tokens`
- rounded to `0.000001` USD precision

If `cost_usd` is supplied, the API accepts it as an override and stores it unchanged.

## Operational Guidance

- Update `data/pricing.yaml` when provider pricing changes.
- Add CI tests for any pricing schema/logic changes.
- Keep model IDs normalized to the exact values your clients emit.

# Architecture

## Overview

The system ingests LLM usage + revenue events, computes missing LLM costs from a repo-local pricing catalog, applies budget guardrails, stores events in Postgres, and exposes analytics/health metrics via FastAPI.

## Data Flow

```mermaid
flowchart LR
  C[Client / SDK] --> E1[POST /events/llm]
  C --> E2[POST /events/revenue]
  E1 --> P[Pricing Engine]
  E1 --> G[Budget Guardrails]
  G --> A[Alert Service]
  E1 --> DB[(Postgres)]
  E2 --> DB
  DB --> Q[Analytics Service]
  Q --> M1[GET /metrics/summary]
  Q --> M2[GET /metrics/by-model]
  Q --> M3[GET /metrics/by-feature]
  DB --> B1[GET /budgets/status]
  API[FastAPI] --> PR[Prometheus /metrics]
```

## Components

```mermaid
flowchart TD
  API[FastAPI App]
  MW[Middleware\nrequest_id + HTTP metrics]
  OBS[Observability\nPrometheus counters/histograms]
  CORE[Core\nsettings + logging + version]
  STORE[Store\nSQLAlchemy models/repos + Alembic]
  PRICING[Pricing\npricing.yaml loader + cost calculator]
  BUDGETS[Budgets\nstatus + guardrails + alerts]
  ANALYTICS[Analytics\naggregations + anomaly detection]

  API --> MW
  API --> CORE
  API --> STORE
  API --> PRICING
  API --> BUDGETS
  API --> ANALYTICS
  MW --> OBS
  BUDGETS --> STORE
  ANALYTICS --> STORE
  ANALYTICS --> BUDGETS
```

## Deployment (Local)

```mermaid
flowchart LR
  Dev[Developer Machine] --> DC[docker compose]
  DC --> API[api container\nFastAPI + Alembic]
  DC --> PG[postgres container]
  HostPy[host python env] --> Seed[make seed]
  HostPy --> Demo[make demo]
  Seed --> PG
  Demo --> API
```

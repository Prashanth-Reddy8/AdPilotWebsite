# AdPilot v1 Architecture

## Scope and safety boundary

Version 1 monitors Meta ad creatives, classifies performance, and notifies users. It is intentionally read-only with respect to campaign delivery: the Meta adapter requests reporting/account-read capabilities and the public API exposes no campaign-status mutation. `TURN_OFF_RECOMMENDATION` is a recommendation, never an automated action.

## System shape

AdPilot is a modular monolith. FastAPI owns HTTP APIs, orchestration, and the hourly scheduler. PostgreSQL is the system of record. Meta and Slack are external adapters behind application services. Flutter consumes stable JSON APIs and contains no analysis logic.

Request flow:

1. JWT authentication resolves the current user.
2. API routers validate input and call an application service.
3. Services enforce account ownership and coordinate repositories/adapters.
4. SQLAlchemy persists normalized entities, metrics, recommendations, and delivery attempts.
5. A scheduler invokes the same sync service used by `POST /sync`; scheduled and manual runs therefore have identical behavior.

## Data model

- `users`: login identity and account lifecycle.
- `meta_accounts`: user-owned Meta ad accounts; access tokens are encrypted at rest.
- `products`: user-defined product groups.
- `campaigns`: normalized Meta campaigns, optionally assigned to a product.
- `ad_sets`: normalized Meta ad sets.
- `creatives`: creative identity plus current recommendation state.
- `ads`: Meta ads joining campaigns, ad sets, and creatives.
- `daily_metrics`: one ad/day fact row. Ratios are retained for source fidelity while spend/revenue/click counters support correct aggregate recomputation.
- `settings`: per-user analyzer thresholds and notification configuration.
- `alerts`: immutable state-transition events with a metric snapshot.
- `notification_logs`: each delivery attempt and outcome.
- `sync_runs`: operational audit record for manual and scheduled imports.

Tenant isolation is enforced by ownership checks in services and user/account foreign keys. A future organization/brand layer can be inserted above users without changing external provider identifiers.

## Analyzer semantics

The current day is compared with the average of the preceding seven available days. CTR, CPA, frequency, and ROAS are recomputed from additive facts; daily ratio averages are not summed. A rule only evaluates when its required baseline/data exists.

Default rules:

- CTR decrease greater than 20%: adverse signal.
- CPA increase greater than 30%: adverse signal.
- ROAS below configured target: adverse signal.
- Frequency above 3.5 while CTR is below its baseline: adverse signal.
- Spend above INR 2,000 with zero purchases: critical signal.

Classification is deterministic:

- `HEALTHY`: no adverse signals.
- `WATCH`: one adverse signal.
- `TURN_OFF_RECOMMENDATION`: a critical signal or at least two adverse signals.

Only transitions from Healthy to Watch, or Watch/Healthy to Turn Off Recommendation, create alerts. Repeated hourly evaluation of an unchanged state is idempotent.

## API contract

- `POST /api/v1/auth/login`: email/password to bearer JWT.
- `POST /api/v1/meta/connect`: exchanges a Meta OAuth code, validates account access, encrypts the long-lived token, and stores the selected account.
- `POST /api/v1/sync`: synchronously imports the last eight days and evaluates affected creatives. A later queue can make this asynchronous without changing the service.
- `GET /api/v1/dashboard`: current totals, classification counts, recent alerts, and paginated creative rows.
- `GET /api/v1/campaigns`: account campaigns with product assignment.
- `PUT /api/v1/campaigns/{id}/product`: assign or clear a product group.
- `GET /api/v1/creatives`: searchable/filterable creative performance.
- `GET /api/v1/alerts`: paginated state-transition history.
- `GET /api/v1/settings`, `PUT /api/v1/settings`: retrieve/update thresholds and Slack configuration.

All list endpoints are bounded and paginated. Errors use a stable `detail` string in v1; a typed error envelope is a planned compatibility improvement.

## Repository structure

```text
backend/
  app/
    api/             HTTP routes and dependencies
    core/            configuration, security, logging, exceptions
    db/              SQLAlchemy base/session
    models/          persistence model
    schemas/         API input/output contracts
    integrations/    Meta and Slack adapters
    services/        sync, analysis, dashboard, notifications
    main.py           application lifecycle
  alembic/            database migrations
  tests/              unit and API-focused tests
  Dockerfile
frontend/             Flutter client (next milestone)
docs/                 architecture and operating decisions
```

## Scaling path without premature distribution

The modular monolith is sufficient for thousands of businesses when API replicas are stateless and scheduled work has a single elected runner. Before horizontal scheduler scaling, move sync jobs to a durable queue (for example, Celery/Redis or a managed queue) and add a per-account distributed lock. Partition or roll up `daily_metrics` only after measured table growth warrants it. Add organization, brand, and role tables when multi-brand/RBAC enters scope rather than embedding those concepts in v1.

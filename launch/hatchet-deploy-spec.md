# Hatchet Deploy Spec

## Role

Durable workflow execution layer for Hermes, scheduled deliverables, retries, observability, and webhook-triggered automation.

## Railway constraints

- Hatchet requires Postgres.
- Do not overlap bot tokens or poller lifecycles across Hermes instances.
- Run Hatchet as a separate bounded service, not merged into Hermes core.

## Minimal deploy spec

1. Provision Railway Postgres and capture connection string.
2. Create a new Railway service for the Hatchet worker.
3. Bind the Postgres URL into the Hatchet service via Railway env.
4. Expose worker health via a bound path and probe with the Railway health wrapper.
5. Create one controlled workflow that writes a durable delivery receipt.
6. Attach ACP local metering before increasing workflow volume.

## Evidence to collect

- Health probe returning 200.
- Workflow delivery receipt persisted.
- Retry count and latency metrics available.
- ACP local metering report present.

## Rollback

- Disable or scale the Hatchet worker to zero.
- Revert workflow routing to Hermes cron.
- Preserve Hermes core unchanged.

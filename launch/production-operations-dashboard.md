# Production Operations Dashboard

This document describes the operational dashboard output expected for production readiness.

## Cards

- Gateway status: `launch/evidence/vault/.../runtime_probe/gateway.json`
- Telegram status: `launch/evidence/vault/.../runtime_probe/telegram.json`
- Worker health: Hatchet metrics endpoint + task counts
- Queue depth: Hatchet queue depth metric
- Promptfoo score: latest `launch/evidence/vault/.../promptfoo/` score
- Evidence completeness: count of expected files in `launch/evidence/vault/`
- Documents generated: count of PDF artifacts under `launch/rendered/`
- Failure count: count of failed probes in latest runtime evidence
- Railway health: Railway deploy status + health endpoint
- Database health: `launch/evidence/vault/.../postgres.json`
- End-to-end latency: `telegram->gateway->worker->reply` histogram

## Consumption

- Render from evidence JSON files using a static site generator or Hermes skill.
- Refresh cadence: every 60 seconds in production.

# PRIORITIZED CHANGE REGISTER

## P0 — Required before production declaration
- Immutable request_id/trace_id generation and propagation
- Canonical lifecycle event emission
- Empty-final-response instrumentation
- No-empty-response guard (behavioral)
- Side-effect-safe retry protection
- Incident evidence capture harness

## P1 — Required for dependable operation
- Structured logging migration with request_id/stage/status/error_class
- Explicit Telegram send success/failure event
- Provider response metadata capture
- Budget exhaustion telemetry and handling
- Health endpoint enrichment

## P2 — Operational improvement
- Tool-result compression for large contexts
- Memory-store compaction automation
- Cron output retention policy and archive/prune
- Alert thresholds for empty responses, provider timeouts, budget exhaustion

## P3 — Future enhancement
- Provider-agnostic response metadata store
- Dashboard incident timeline view
- Automated incident record generation
- Session split/compression lifecycle audit events

EOF
# REPORT 7 — Permanent Hardening Recommendations

## P0 — Critical
- Implement immutable Request Correlation IDs across Telegram → Gateway → Agent → Tools → Model → Delivery.
- Implement No-Empty-Response Guard with retry, fallback, and structured incident message.

## P1 — High
- Enforce structured logging format with request_id, stage, duration, status, error_class.
- Formalize response lifecycle events: response_started, response_completed, response_empty, response_retry.
- Add delivery confirmation event for Telegram outbound messages.

## P2 — Medium
- Tool-result compression threshold for requests exceeding 100k input context.
- Memory-store compaction automation to reduce no-match warnings.
- Cron output retention policy and archive/prune schedule.
- Enrich health endpoint with lightweight resource metrics.

## P3 — Future Enhancement
- Provider-agnostic response metadata capture.
- Session split/compression lifecycle audit events.
- Dashboard incident timeline view.
- Automated incident record generation.


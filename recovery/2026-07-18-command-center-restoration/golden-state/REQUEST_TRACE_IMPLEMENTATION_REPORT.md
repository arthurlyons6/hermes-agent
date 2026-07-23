# REQUEST_TRACE_IMPLEMENTATION_REPORT
Change ID: IMP-20260718-INSTRUMENTATION-001

## Change summary
- Added `agent/telemetry.py` with request_id/trace_id generation, context propagation, and `emit_event(...)` helper.
- Wired `RequestContext` into gateway inbound handling at `gateway/run.py:_handle_message_with_agent`.
- Added lifecycle events: `REQUEST_RECEIVED`, `RESPONSE_SERIALIZED`, `MODEL_RESPONSE_EMPTY`.
- Added explicit Telegram send telemetry with `TELEGRAM_SEND_STARTED`, `TELEGRAM_SEND_ACCEPTED`, `TELEGRAM_SEND_FAILED`, success/failure metadata without secrets.

## Files affected
- `hermes-agent/agent/telemetry.py`
- `hermes-agent/gateway/run.py`
- `hermes-agent/gateway/platforms/base.py`

## Validation
- Static compile checks passed for modified files.
- End-to-end event footprint preserved in append-only form.

## Risk
- Low: changes are additive instrumentation only.
- No behavior change.
- No retry/fallback logic introduced.
- No secrets logged.


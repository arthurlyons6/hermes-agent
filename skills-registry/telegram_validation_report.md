# Telegram Validation Report

Generated: 2026-07-21T18:43:17.844380+00:00

## Config Expectation
- `TELEGRAM_BOT_TOKEN` is read from env and loaded into platform config.
- Allowed users/chats supported via gateway config keys.
- `HERMES_FORCE_TELEGRAM_POLLING` is supported by diagnostics and adapter.

## Tests
- Outbound: `tools/debug_railway_telegram.py` and `tools/diag_railway_telegram.py` probe `getMe`/`getUpdates`/`sendMessage`.
- Inbound: adapter read path exists; gateway transient-error handling confirmed in `gateway/run.py`.

## Risk
- Do not log tokens; diagnostics print only identifiers/message metadata.

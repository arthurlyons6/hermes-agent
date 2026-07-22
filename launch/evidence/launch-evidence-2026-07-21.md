# Launch Evidence Record

Generated: 2026-07-21
Scope: local evidence collection for Railway gateway, Telegram delivery, volume, Postgres, ACP, Hatchet

## Evidence

### E1 Railway gateway health
- Status: not obtained
- Reason: requires live Railway service URL or dashboard Execute action; no Railway shell access in this turn
- Next: run `python tools/start_railway_health_check.py` or probe Railway public domain from Railway dashboard

### E2 Telegram end-to-end delivery
- Status: failed
- Reason: `TELEGRAM_BOT_TOKEN` is not present in the current local RJW environment
- Commands executed:
  - `python tools/diag_railway_telegram.py` -> `KeyError: 'TELEGRAM_BOT_TOKEN'`
  - `python tools/debug_railway_telegram.py` -> `KeyError: 'TELEGRAM_BOT_TOKEN'`
- Key finding: local delivery validation cannot pass without Railway-provided bot token; this is expected and should not be retried blindly
- Next: execute these commands in the Railway shell or inject token via Railway env and rerun

### E3 Persistent volume operation
- Status: not obtained
- Next: validate Railway volume mount path and write/read via Railway shell or dashboard File/Execute path

### E4 PostgreSQL operation
- Status: not obtained
- Next: validate Railway Postgres connection string and query from both Hermes gateway and Hatchet worker

### E5 ACP local metering
- Status: not obtained
- Next: install plugin in temp HERMES_HOME and run `acp-hermes report`

### E6 Hatchet worker
- Status: not obtained
- Next: deploy Railway Hatchet service and verify workflow delivery receipt

# End-to-End Telegram Runtime Manifest

## Goal

Prove inbound and outbound Telegram delivery on Railway with explicit evidence.

## Prerequisites

- Railway gateway healthy on `/health`.
- Telegram config present at runtime and loadable.
- Unique bot token for Railway instance.

## Steps

1. Start Hermes gateway via the Railway process supervisor.
2. Probe `/health` until it returns 200.
3. Run Telegram outbound probe with bot token and allowed user.
4. Send one Telegram message from the allowed user.
5. Confirm Hermes receives and replies without auth or group gate failure.
6. Capture evidence fields:

```text
health_url=<url>
health_status=<status>
telegram_config_path=<path>
telegram_allowed_users=<csv>
webhook_info=<json>
recent_updates_count=<count>
probe_sent=<true/false>
reply_received=<true/false>
```

## Rollback

- Stop poller on Railway instance.
- Revert runtime config file to last known good snapshot.
- Restart gateway and confirm `/health` before resuming.

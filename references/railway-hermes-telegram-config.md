# Railway Telegram config fix

## Verified root cause
`hermes-z0Rv` logs show:
`WARNING gateway.run: No adapter could be created for any of the 1 configured platform(s).`

A Railway-runtime check confirms:
- `TELEGRAM_BOT_TOKEN` is present
- `HERMES_HOME=/app/.hermes`
- `/app/.hermes/config.yaml` may not exist

So the failure was missing runtime config, not missing dependency/auth.

## Current env-driven safety net
`gateway/config.py::_apply_env_overrides()` now auto-enables Telegram when
`HERMES_ENV=railway` (or `RAILWAY_ENVIRONMENT=railway`) and `TELEGRAM_BOT_TOKEN`
are present, so a missing `config.yaml` no longer blocks adapter creation.
`config.yaml` is still recommended for explicit platform settings/config.

Recommended `/app/.hermes/config.yaml`:

```yaml
platforms:
  telegram:
    enabled: true
```

## Railway-side Transport choice
Telegram supports webhooks and long polling. On Railway, public webhook ingress
is often unreliable, and Hermes has an explicit escape hatch for this case.

To make Railway Telegram reliable with exactly one active consumer:

1. Railway must use **TELEGRAM poll mode only**. Set:
   - `HERMES_FORCE_TELEGRAM_POLLING=true`
   - Do NOT set `TELEGRAM_WEBHOOK_URL` in Railway.
2. Local Hermes uses its own bot token and profile (`BlackGold8891_Bot`).
   Railway Hermes uses `Lyons8891_bot`.
3. Only ONE Hermes instance per bot token, globally. See Operator switching steps.

With `HERMES_FORCE_TELEGRAM_POLLING=1`, the Telegram adapter:
- ignores any `TELEGRAM_WEBHOOK_URL`
- attempts `deleteWebhook` best-effort to clear stale webhooks
- enters bounded `start_polling()` with reconnect recovery
- never starts the local webhook HTTP server

## Why two separate bot tokens avoid duplicates
Telegram delivers `getUpdates` to at most one active polling session per bot
token. If both local Hermes (`BlackGold8891_Bot`) and Railway Hermes
(`Lyons8891_bot`) use different tokens, Telegram treats them as separate bots;
neither blocks the other. Duplicate replies for the same target bot only
happen when two Hermes instances share the same token.

## Validation steps
1. Confirm the Railway container sees Telegram token + Railway env.
2. Confirm `/app/.hermes/config.yaml` has Telegram enabled.
3. Confirm Railway deploy logs show:
   - Telegram adapter connecting
   - `Forcing Telegram polling mode` when `HERMES_FORCE_TELEGRAM_POLLING=true`
   - `Webhook server listening` is absent
   - polling healthy
4. Send one Telegram message to `@Lyons8891_bot`; confirm it reaches Hermes.
5. Confirm `/health` is served by `tools/start_railway_health_check.py`.

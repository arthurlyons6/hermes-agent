# Railway Telegram config fix

## Verified root cause
`hermes-z0Rv` logs show:
`WARNING gateway.run: No adapter could be created for any of the 1 configured platform(s).`

At the same time, a Railway-runtime check confirms:
- `TELEGRAM_BOT_TOKEN` is present
- `HERMES_HOME=/app/.hermes`
- `/app/.hermes/config.yaml` does not exist

So the failure is missing runtime config, not missing dependency/auth.

## Proposed minimal config
Create `/app/.hermes/config.yaml` with:

```yaml
platforms:
  telegram:
    enabled: true
```

Then restart/redeploy the service. Hermes will load Telegram and attempt polling.

If write access via Railway SFTP/files upload is unavailable, an alternative
fallback is RuntimeStatus/boot-time config injection inside the deployed image,
but the YAML path is the intended supported path.

## Validation steps
1. Confirm `cat /app/.hermes/config.yaml` succeeds.
2. Watch deployment logs for:
   - removal of the no-adapter warning
   - Telegram polling/connection success
3. Send one Telegram message; confirm it reaches Hermes.

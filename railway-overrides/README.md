# Railway dashboard override for hermes-z0Rv

Manifest staleness is the root cause. Local repo changes do not force Railway
to pick up a `startCommand`, so `/health` returns 502 from the router.

Apply these as dashboard overrides in Railway → Settings → service override.

## Override values

- startCommand: `python -m hermes_cli.main gateway run --replace`
- healthcheckPath: `/health`

## Why this is the right fix

Manifests from targeted deploys show `startCommand: null` on recent Failures.
A null startCommand means Railway can’t boot the app, so inbound fails fast
and returns 502 before either adapter path runs. Escalating adapter-to-adapter
changes cannot heal a missing process.

## Manual steps

1. Open Railway → Service hermes-z0Rv → Settings → Deploy / Start Command
2. Paste: `python -m hermes_cli.main gateway run --replace`
3. Healthcheck path: `/health`
4. Redeploy
5. Tail logs for: `Gateway running with 1 platform(s)` or `✓ telegram connected`

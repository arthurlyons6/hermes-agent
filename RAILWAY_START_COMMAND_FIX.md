# Railway Start Command Fix

## Status: REPOSITORY FIXED, DASHBOARD OVERRIDE PENDING

## What was changed

### Dockerfile
- CMD changed from `python -m hermes_cli.main gateway run --replace` to `python -m gateway.run`
- Committed as e8b2b95 on master and pushed to railway/inbound-fix-polling-escape

### nixpacks.toml
- startCommand changed from `hermes` to `python -m gateway.run`
- Same commit

## Root cause confirmed

Railway Dashboard has a Start Command override set to `python -m hermes_cli.main gateway run --replace`.
This override takes precedence over Dockerfile CMD and nixpacks.toml startCommand.
Every deployment shows the old command in its service manifest metadata.

## Evidence

- All 20+ deployments show `startCommand: python -m hermes_cli.main gateway run --replace`
- Newest deployment (4a4c8623) has commit d3288e78 (old), not e8b2b95 (our fix)
- The `hermes_cli` module does not exist in this project (confirmed via pkgutil and import attempts)
- `python -m gateway.run` starts successfully locally, binds health server, returns HTTP 200

## What needs to happen next

The Railway Dashboard Start Command override must be changed:

1. Open https://railway.com/dashboard
2. Navigate to project `believable-wisdom` → service `hermes-z0Rv` → Settings → Deploy
3. Find Start Command field
4. Replace `python -m hermes_cli.main gateway run --replace` with `python -m gateway.run`
5. Save and trigger new deploy

## Repository status

Both files are correct and pushed:
- Dockerfile CMD: `["python", "-m", "gateway.run"]`
- nixpacks.toml startCommand: `python -m gateway.run`
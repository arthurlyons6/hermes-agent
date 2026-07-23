# Lyons Command Center — Railway Deployment Guide

## Service name
believable-wisdom

## Repository
https://github.com/arthurlyons6/hermes-agent

## Start command
```
python -m hermes_cli.main gateway run
```

## Variables
```env
HERMES_HOME=/app/.hermes
NODE_ENV=production
PORT=3006
HOST=0.0.0.0
HERMES_SESSION_SECRET=<generated>
HERMES_API_KEY=<generated>
TELEGRAM_BOT_TOKEN=<from @BotFather>
TELEGRAM_ALLOWED_USERS=8897743493
OPENROUTER_API_KEY=<from openrouter.ai>
# Optional later: GOOGLE_OAUTH_CLIENT_ID, GOOGLE_OAUTH_CLIENT_SECRET, ONEPASSWORD_TOKEN
```

## Volume
Mount at `/app/.hermes`

## Health check
Path `/health`, timeout 30s
Railway waits for health check before marking deploy complete.

## Telegram Gateway
- Use Railway public URL + webhook route if available
- Otherwise long-poll fallback remains

## Executive Briefing cron
Entrypoint: `python tools/briefing/run_daily_executive_brief.py --deliver`
Storage: `store_brief` writes to `/app/.hermes/executions.db`
Delivery: `deliver_brief` renders and sends Telegram text

## Deployment validation checklist
- [ ] Build completed
- [ ] Container started
- [ ] Health check passed
- [ ] Env vars loaded
- [ ] Volume mounted at `/app/.hermes`
- [ ] Telegram gateway initialized
- [ ] Command API responding
- [ ] Executive briefing module loads
- [ ] `store_brief()` writes successfully
- [ ] Logging operational
- [ ] No secrets in logs
- [ ] Restart resilience confirmed
- [ ] Rollback procedure tested

## Rollback procedure
- Railway project -> Deployments -> Redeploy previous known-good deploy
- Environment variables and Volume persist across redeploys
- Database `executions.db` is append-only; briefs are retained

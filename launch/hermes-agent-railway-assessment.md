# hermes-agent-railway Fork Assessment

Repository: https://github.com/arthurlyons6/hermes-agent-railway
Assessment date: 2026-07-21

## Purpose
- One-click Railway deploy manifest for Hermes Agent
- Dashboard cookie auth proxy (`auth_proxy.py`) for Railway UI access
- Thin wrapper around upstream Hermes Agent repo

## Benefits
- Zero-config deploy pattern documented
- Persistent storage mount path documented: `/root/.hermes`
- Platform env vars documented: `TELEGRAM_BOT_TOKEN`, `GATEWAY_ALLOW_ALL_USERS`, `HERMES_FORCE_TELEGRAM_POLLING`
- Healthcheck path documented in manifest: `/api/health`

## Risks
- Does NOT install or run real Hermes messaging/gateway adapters inside the container
- `entrypoint.sh` only starts dashboard + auth proxy; real Hermes gateway is expected to run separately
- Healthcheck bypasses real gateway: `/api/health` is served by auth proxy and returns `{"status":"ok"}` even if upstream Hermes is down
- Volume guidance uses `/root/.hermes`, which conflicts with current Hermes stage2 remap logic preferring `/opt/data`
- Auto-update via `git pull` in entrypoint is risky in production; can pull breaking changes without testing

## Dependencies
- Railway volumes
- LLM provider API key
- Telegram bot token
- `aiohttp` runtime in container

## Recommended owner
- Hermes CLI / platform adapter team
- Railway production operations team

## Integration approach
- Do NOT merge deploy wrappers into core Hermes repo
- Preserve as standalone deploy manifest
- Use its `railway.toml` and `Dockerfile` as the canonical Railway deploy template
- For listener/gateway sequencing issues in production, patch main Hermes repo rather than the fork

## Testing plan
1. Deploy fork in staging Railway project
2. Verify `/api/health` does not mask upstream failure
3. Verify dashboard login works
4. Verify Telegram adapter actually connects and responds
5. Verify volume persistence after redeploy

## Rollback plan
- Revert Railway service to previous deployment ID
- Use volume snapshot if `/root/.hermes` contains critical state

## Final recommendation: **Reference only**

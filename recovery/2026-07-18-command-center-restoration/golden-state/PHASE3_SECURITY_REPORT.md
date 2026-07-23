# Phase 3 — Security Report
Generated: 2026-07-18
Evidence-freeze: full/mask applied; no raw secrets reproduced.

## Credential inventory (masked)
- API_SERVER_KEY: present in `.env` line 4; masked ****
- TELEGRAM_BOT_TOKEN: present in `.env` line 5 and line 9; one lowercase and one uppercase duplicate; masked ****
- PHOTON_PROJECT_SECRET: present in quarantined script; masked **** - **MUST ROTATE**
- NOUS_API_KEY: present in `.env`/config; masked ****
- BWS_ACCESS_TOKEN: referenced by `config.yaml` env-var link; masked ****
- GMAIL: referenced via `auth.json` loader; masked ****
- PHOTON_SIDECAR_TOKEN: present in `.env`; masked ****

## Authentication trust map
- Gateway API auth: Bearer token validated against loaded `.env` value (`API_SERVER_KEY`)
- Telegram auth: bot token from `.env` lines 5/9
- External trigger path: same `.env`-loaded validator; confirmed correct token path rejects mismatches

## Secret exposure scan results
CRITICAL — Hard-coded live secret:
- File: `scripts/.quarantine/_tmp_photon_env_updater.py:10`
- Secret: `PHOTON_PROJECT_SECRET=...1q5w`
- Control: quarantined; original removed from active path

CRITICAL — `.env` duplicates duplicate `TELEGRAM_BOT_TOKEN`:
- `.env:5` and `.env:9`
- Risk: loader/order-dependent; could load stale/wrong token

HIGH — `.env` permission too open:
- `.env` mode `644`; violates least-privilege for secrets file

HIGH — Backups contain plaintext secrets:
- `backups/.env.bak-20260715_043337` contains `TELEGRAM_BOT_TOKEN` and other secret keys
- Count: 4 secret references in backup file

HIGH — Port exposure review:
- `0.0.0.0:7680` svchost.exe — Windows system service; requires explicit review before restriction
- `0.0.0.0:8080` httpd.exe — external listener; confirm necessity or restrict to localhost
- `127.0.0.1:8789` node.exe photon sidecar — should remain localhost unless remote access is required

MEDIUM — Active log redaction:
- Current logs show redacted markers (`****`) rather than raw secrets
- Prior structured tool output exposed full values earlier today; do not repeat

## Environment-file review
- `.env` is the single authoritative source for Hermes runtime secrets
- PATH: `C:\Users\13464\AppData\Local\hermes\.env`
- No source-control exposure found via git history search for secret commits
- `.gitignore` missing: need authoritative ignore rules for `.env`, `auth.json`, backup zips under `backups/`, logs

## Permission review
- `.env`, `auth.json`, `config.yaml`: all `644` (owner readable/writable; group/other readable)
- Service processes run under `User` context; reduce to owner-only read for secrets files when possible

## Least-privilege review
- Gateway/API binds `127.0.0.1:3006` — compliant
- Telegram/polling requires outbound only; no inbound needed
- Photon sidecar bound `0.0.0.0:8789`; restrict unless external access is required

## Logging redaction review
- `logs/agent.log`, `gateway.log`, `errors.log` contain no full secrets in current scan
- Masked references found: `8914053082:***` and `9710d1b9...` short forms
- Maintain redaction; avoid logging Authorization headers

## Configuration conflict report
- `.env` duplicate key `TELEGRAM_BOT_TOKEN` line 5 (`telegram_bot_token`) vs line 9 (`TELEGRAM_BOT_TOKEN`)
- Single authoritative source issue for telegram identity

## Credential-rotation recommendations
1. Rotate `PHOTON_PROJECT_SECRET` immediately; treat as compromised due to hard-coded storage and quarantine origin
2. Rotate `TELEGRAM_BOT_TOKEN` if `.env` duplication may have supplied wrong token to any live session
3. Confirm `API_SERVER_KEY` rotation unnecessary; only one authoritative source remains
4. Evaluate whether `BWS_ACCESS_TOKEN` env link is used or deprecated

## Security findings ranked
- CRITICAL: PHOTON secret hard-coded in quarantined file
- CRITICAL: `.env` duplicate telegram key
- HIGH: `.env` and secret files permission too open
- HIGH: backups contain live secrets
- MEDIUM: `.gitignore` absent for secrets paths
- MEDIUM: external listener ports need restriction decision
- LOW: active log redaction otherwise clean

## Remediation recommendations (effort / impact)
- Deduplicate `.env` telegram token: 5 min / low
- Restrict `.env` mode: 5 min / low
- Curate `.gitignore`: 15 min / low
- Archive or encrypt backup secret references: 30 min / low
- Restrict photon sidecar to localhost or document external requirement: 10 min / medium
- Confirm/service-bind review for `0.0.0.0:7680` and `0.0.0.0:8080`: 20 min / medium
- Rotate `PHOTON_PROJECT_SECRET` post change-control: 30 min / high

## Completion status
CONDITIONAL — Critical secret exposure and duplicate auth source remain unresolved at end of scan.


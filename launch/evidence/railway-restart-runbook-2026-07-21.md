# Railway restart runbook — 2026-07-21

## Verified root cause
- Service logs show Telegram polling actually starts.
- Fatal signal is repeated `SIGTERM` shutdown/restart cycles, which close the event loop and abort fetch: `Event loop is closed` -> `CancelledError`.
- Public URL remains `502 Bad Gateway`.

## Required production state change
Ensure `/app/.hermes/config.yaml` exists with live Railway env values, then let the init system perform a clean stop/start rather than killing the process mid-fetch.

## Manual fix block
Run this in Railway dashboard Execute or a fresh `railway ssh` session:

```bash
python - <<'PY'
from pathlib import Path
import os
out = Path('/app/.hermes/config.yaml')
out.parent.mkdir(parents=True, exist_ok=True)
with out.open('w', encoding='utf-8') as f:
    f.write('_config_version: 1\n')
    f.write('telegram:\n')
    f.write('  enabled: true\n')
    f.write('  token: "%s"\n' % os.environ.get('TELEGRAM_BOT_TOKEN','').strip())
    f.write('  allowed_users: "%s"\n' % os.environ.get('TELEGRAM_ALLOWED_USERS','').strip())
    f.write('  home_channel: "%s"\n' % os.environ.get('TELEGRAM_HOME_CHANNEL','').strip())
    f.write('  webhook_url: "%s"\n' % os.environ.get('TELEGRAM_WEBHOOK_URL','').strip())
    f.write('gateway:\n')
    f.write('  allow_all_users: true\n')
print(out.read_text())
PY

# Do NOT use kill -9; use the supervisor's restart path instead.
# If dashboard Execute, use the Railway dashboard Redeploy button after confirming
# the file contents above.
```

## Verification
After restart/redeploy:
```bash
railway logs --lines 80
python - <<'PY'
import urllib.request
url='https://hermes-z0rv-production.up.railway.app/health'
with urllib.request.urlopen(urllib.request.Request(url, method='GET'), timeout=15) as r:
    print({'status': r.status, 'body': r.read(200).decode(errors='replace')})
PY
```

## Evidence record
- Session shell: `proc_06dc3c5f8d5d` matched `root@` prompt; PTY closed before restart command execution.
- Repo commits: `639428f18`, `e81075486`
- Branch: `railway/inbound-fix-polling-escape`

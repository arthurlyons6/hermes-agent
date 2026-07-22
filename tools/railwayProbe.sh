#!/usr/bin/env bash
set -euo pipefail
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
echo WROTE_CONFIG

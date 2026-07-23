# Phase 4 — Testing Report
Generated: 2026-07-18

## Evidence restriction note
Phase 4 uses masked references only. No raw secrets, full tokens, or unrelated production values are reproduced.

## Tests executed
- Gateway health check
- API authentication failure path
- Configuration and scheduling validation
- Memory and port baseline
- Verifiable rollback artifact validation
- Scheduled-job output verification

## Gateway health
PASS
- Endpoint: http://127.0.0.1:3006/health
- Response: {"status":"ok","platform":"hermes-agent","version":"0.18.2"}
- No credential exposure observed

## Authentication failure path
PASS
- Wrong Bearer credential attempt returned controlled error response
- Empty auth attempt returned controlled error response
- No raw secrets exposed in error output

## Configuration and scheduling validation
PASS
- Active jobs:
  - `0e77fd645735` AI Skills Upgrade, next 2026-07-19T11:00:00-05:00
  - `64fce1abb3de` PE PR Pulse — BlackGold, next 2026-07-19T07:00:00-05:00
  - `b043387384da` Global AI/Open-Source Research, next 2026-07-19T09:00:00-05:00
  - `dac5a2f40582` Lyons Security Audit, next 2026-07-20T06:00:00-05:00
- All jobs active and scheduled; no failed active-job states observed
- `dac5a2f40582` uses script mode with presumed stdout delivery; not blocked

## Resource baseline
PASS
- Free physical memory: 1184416 KB
- Total memory: 8092728 KB
- Port 3006 owner: PID 11704
- No port conflicts on critical Herm services after Phase 2 cleanup

## Scheduled-job output verification
PASS
- Job 64fce1abb3de output present: 2026-07-18_18-27-45.md
- Response content verified in trace; task boundary maintained

## Recovery and rollback artifact validation
PASS
- toolsets.py restoration backup present at `toolsets.py.restoration-backup`
- gateway_state.json snap preserved at recovery workspace
- Rollback contents verified, no secrets exposed

## Post-restart state validation
PASS
- Post-restart WMI enumeration shows two stable Hermes pythonw processes: 11704 and 18900
- Tasklist showed two intermittent python.exe and one pythonw from same create timestamp bond; immediately after restart those processes stabilized to 11704 only
- Post-restart tasklist now shows two pythonw processes bound to identical module/args on different interpreter paths
- 11704 remains the authoritative port owner
- Impression: these may be hidden-startup or sidecar-style duplicate gateway handlers running with different interpreter context
- Recommendation: classify as Phase 2 open risk SEV-3 for future elevated review

## Final status
PASS


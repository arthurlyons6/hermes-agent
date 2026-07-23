# Phase 2 — Stabilization: Complete Report
Generated: 2026-07-18
Mission: Duplicate processes, port conflicts, auth mismatches, failed jobs, retries, broken imports, stale locks, log growth, startup inconsistency

## Before-and-after process inventory
### Before
- PID 11704: `.venv\Scripts\pythonw.exe -m hermes_cli.main gateway run` on port 3006
- PID 18900: `system Python\pythonw.exe -m hermes_cli.main gateway run`
- PID 14324: `system Python\python.exe cli.py`
- PID 15540: `.venv\Scripts\python.exe cli.py`

### After
- PID 11704: `.venv\Scripts\pythonw.exe -m hermes_cli.main gateway run` retained as authoritative
- PID 18900: retained pending exact classification; remains duplicate/redundant/hidden-startup origin unknown
- PID 14324/15540: retained pending classification; not active on port 3006
Change: Stale locks removed; no process termination authorized

## Before-and-after port registry
### Before
- 127.0.0.1:3006 LISTENING PID 11704
- TIME_WAIT connections on 3006 absent before cleanup

### After
- 127.0.0.1:3006 LISTENING PID 11704
- TIME_WAIT connections cleared after lock cleanup
- No new port conflicts observed
- Port 8080 bound to PID 5804; not Hermes; outside this phase

## Processes retained
- PID 11704: canonical gateway, port owner, scheduled-task-backed
- PID 18900: duplicate pythonw; kept until classification confirmed

## Processes terminated
- None

## Reason and evidence for each termination
- N/A; no terminations performed due to privilege limitations on host

## Authoritative startup paths
- Scheduled Task `\HermesGateway` → `cmd.exe /S /C gateway-service\Hermes_Gateway_canonical.cmd`
- Launcher files present: `Hermes_Gateway.vbs`, `Hermes_Gateway_cmd`, `Hermes_Gateway.ps1`, `Hermes_Gateway_canonical.cmd`
- Canonical task confirms single official gateway entrypoint

## Startup controls implemented
- Stale locks removed: `.jobs.lock`, `.tick.lock`
- No new process-control enforcement installed; depends on elevated remediation path

## Validation results
- Port 3006 ownership: PASS
- API health: PASS → `{"status":"ok","platform":"hermes-agent","version":"0.18.2"}`
- Auth path: PASS → wrong Bearer rejected correctly
- Telegram gateway health: PASS
- Scheduled job 64fce1abb3de: PASS → successful output written at 16:19:13
- Duplicate process count: FAIL/CONDITIONAL → still holds extra Hermes python processes
- Auto-restart containment: CONDITIONAL
- Clean restart behavior: CONDITIONAL
- Memory and CPU baseline: NOT RUN → target for Phase 5–7

## Remaining risks
- Two extra Hermes python processes (18900, 14324/15540 cluster) remain unclassified
- Cannot eliminate duplicates from current privilege boundary; target SEV-3
- Cron job 844bb2e78a96 failed once with SSL handshake timeout; treated separately as provider/TLS reliability issue, not process cleanup

## Rollback information
- No configuration change applied requiring rollback
- If future privileged remediation introduces issues, rollback to snapshot: pre-change state documented above
- Toolsets backup remains in place: `toolsets.py.bak-20260718-command-center-restoration`

## Final status
CONDITIONAL

Approved by: Marcus (partial; eligible for Phase 3 once duplication is resolved or escalation is accepted)

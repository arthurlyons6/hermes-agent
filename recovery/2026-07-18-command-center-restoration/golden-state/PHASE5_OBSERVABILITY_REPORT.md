# Phase 5 — Observability Report
Generated: 2026-07-18

## Service inventory
- Hermes Gateway on 127.0.0.1:3006, PID 11704
- Telegram adapter/platform
- Photon/sidecar on 127.0.0.1:8789
- Local API server / scheduled CRON with 4 active jobs
- Windows scheduled task `HermesGateway`
- Local models/providers: Nous and Ollama fallback

## Health-signal matrix
PASS
- Gateway health endpoint: http://127.0.0.1:3006/health returns HTTP/JSON including status, platform, version
- Cron list shows enablement, next run times, execution states
- Port ownership observable via netstat
- Process presence observable via WMI/tasklist
- Job outputs present per cron/output/<id>/*.md

## Structured logging review
PASS
- Timestamps, severity, module identifiers, job IDs, and outcomes present
- Auth failures observable without exposing full secrets
- Provider/base_url validation errors logged as structured refusals
- Session transcript warnings preserved with disk/memory counters
- Memory-store capacity warnings logged by tool layer

## Monitoring coverage map
- HEALTHY: Gateway, Telegram polling, scheduled jobs
- DEGRADED: transient Telegram heartbeat degradation observed at 2026-07-18 13:23 and 16:46
- UNHEALTHY: none currently
 Known degraded signal: photon-sidecar persistent/transient spectrum stream failures

## Metrics inventory
- Gateway uptime/heartbeat
- Cron execution/id/next-run/last-run metadata
- Job output files with timestamps
- Log volume: logs/ ~45MB total with .1/.2/.3 rotations
- Memory counters on transcript store in gateway.log warnings
 Absent: dedicated CPU/RAM/disk numeric metrics dashboard stream

## Alert inventory
- Auth failures / invalid API key
- Cron failures and timeouts
- Session transcript lag warnings
- Provider/base_url exfiltration refusal blocks
- SessionDB initialization timeout fallbacks
- Garbled tool errors / denied tools

## Incident trigger matrix
- SEV-1: unauthorized resource exposure or credential compromise
- SEV-2: repeated gateway failure, critical integration failure
- SEV-3: limited feature failure with mitigation
- SEV-4: minor defect with low operational impact
Current triggers matched to evidence:
- `.env` credential duplication + hard-coded secret in quarantine -> SEV-2 security path
- Cron `844bb2e78a96` SSL timeout -> SEV-3
- Memory FTS corruption warnings -> SEV-3
- Duplicate Hermes PIDs (not yet functionally abnormal) -> SEV-3 open risk

## Log retention review
PASS with gaps
- Primary logs: agent.log, gateway.log, errors.log active with rotated .1/.2/.3
- Cron outputs: 14 present from 2026-07-16 through 2026-07-18; short retention window
- Backup bundles present with integrity issue in one legacy zip
 Log retention policy documented by presence of rotation; max age/size cap not explicitly configured

## Observability gaps
- No single structured incident-record store
- No dedicated metrics endpoint beyond health
- No CPU/memory/disk numeric monitoring stream
- No alert pipeline beyond log-based discovery
- Cron output retention appears minimal
- Two stable duplicate Hermes pythonw processes are visible but lack ownership metadata and are not yet classified

## Recommendations ranked
- High impact / low effort: classify duplicate pythonw processes and document permitted owner
- High impact / low effort: add bounded cron-output retention policy and prune schedule
- Medium impact / low effort: establish incident record directory under recovery workspace
- Medium impact / medium effort: add lightweight resource snapshot script to logs/curator
- Lower impact / medium effort: enrich health endpoint with disk/memory/process metrics

## Final status
PASS with open observability gaps documented.


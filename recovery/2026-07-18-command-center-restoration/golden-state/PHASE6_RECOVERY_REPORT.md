# Phase 6 — Recovery Report
Generated: 2026-07-18

## Recovery inventory
- Hermes Gateway: canonical Windows Scheduled Task `HermesGateway` with launcher `gateway-service\Hermes_Gateway_canonical.cmd`
- Gateway state: `gateway_state.json`
- Active port: 127.0.0.1:3006 owned by PID 11704
- Backup path: `C:\Users\13464\AppData\Local\hermes\backups\`
- Recovery workspace: `C:\Users\13464\LyonsCommandCenter\recovery\2026-07-18-command-center-restoration\`

## Backup inventory
- `backups/auth.json.bak-20260715_043337`
- `backups/config.yaml.bak-20260715_043337`
- `backups/hermes-agent-20260709-backup.tar.gz` — integrity verified
- `backups/hermes-agent-20260709-backup.zip` — integrity failure; exclude from restore plan
- `backups/pre-update-2026-07-11-054129.zip`
- `backups/pre-update-2026-07-14-125315.zip`
- `backups/pre-update-2026-07-14-161259.zip`
- Golden-state rollback: `toolsets.py.restoration-backup` / `toolsets.py.bak-20260718-command-center-restoration`

## Restore procedure
1. Stop active gateway via Task Scheduler if necessary.
2. Restore `config.yaml`, `.env`, and `auth.json` from selected backup into `C:\Users\13464\AppData\Local\hermes\`.
3. Verify `toolsets.py` is present; restore rollback backup if mismatch detected.
4. Restart gateway via `schtasks /Run /TN HermesGateway`.
5. Validate health endpoint at `http://127.0.0.1:3006/health`.
6. Validate passwordless authentication test and one scheduled job.
7. Record outcome and retain rollback path.

## Rollback procedure
- Rollback target: pre-change files copied or timestamped backups.
- Domain-specific rollback available for `toolsets.py` repair via `toolsets.py.restoration-backup`.
- General rollback: restore from `backups/pre-update-*.zip` or dated tar.gz.

## Canonical restart procedure
- Preferred: `schtasks /Run /TN HermesGateway`
- Alternative VBS/CMD launcher: `gateway-service\Hermes_Gateway_canonical.cmd`
- Validation: `curl http://127.0.0.1:3006/health`, confirm `127.0.0.1:3006 LISTENING`, confirm PID.

## Telegram recovery procedure
- Validate Telegram adapter connected in `gateway.log` poller/flush events.
- Reconnect path: confirm live adapter or restart gateway and monitor `gateway.log` for reconnect success.
- If Telegram delivery drops again, inspect `response_delivery_dropped` records and provider/dns pathway before auth rotation.

## Provider recovery procedure
- Confirm `base_url` in config when errors mention provider block or TLS failure.
- For timeouts: verify provider host reachable, retry later, consider fallback.
- If provider returns invalid model/param error: select alternate model or request provider remediation.

## Authentication recovery procedure
- Verify `.env` contains `API_SERVER_KEY`.
- Restart gateway only, not whole stack.
- Re-test auth via invalid-token rejection and valid-token admission.
- If key mismatch persists, regenerate key, update `.env`, and restart task.

## Scheduled-job recovery procedure
- Re-pair imported symbols if import errors appear.
- Re-run failed job via manual trigger once repair confirmed.
- Inspect `cron/output/<job-id>/*.md` for response evidence.

## Model empty-response recovery procedure
1. Preserve request ID and tool outputs.
2. Classify failure boundary (tool / provider / model / gateway).
3. Do not rerun side-effecting tools automatically.
4. Retry once with instruction to produce final answer.
5. If retry fails, use approved fallback once with minimal necessary context.
6. If still failed, return controlled incident message referencing incident ID.
7. Record provider, model, tool counts, duration, error category, retry count.

## Recovery test results
- Gateway health check: PASS
- Scheduled job 64fce1abb3de: PASS
- Authentication rejection/acceptance: PASS
- Restart via canonical task: PASS
- toolsets rollback artifact present: PASS

## Recovery gaps
- Full Windows reboot recovery not reproduced in this evidence window; canonical restart validated only.
- Backup zip integrity failure for legacy archive remains unresolved.
- Model empty-response event not reproducible in local evidence; prevention guard pending production gate review.

## Final Phase 6 status
PASS with noted recovery gaps.


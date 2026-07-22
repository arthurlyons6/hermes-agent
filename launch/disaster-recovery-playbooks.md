# Disaster Recovery Playbooks

## 1. Database backup and restore
- Schedule daily pg_dump to Railway volume or external object store.
- Validate restore on a staging Railway service weekly.
- Evidence: `launch/scripts/db_backup_restore.py` output.

## 2. Rollback deployment
- Tag every production deployment with Railway deployment ID.
- Keep prior container image for 72 hours.
- Evidence: `launch/scripts/rollback_validation.py` output.

## 3. Persistent volume recovery
- Replicate critical `/opt/data` to a second Railway volume or S3 nightly.
- Test `rsync` or `tar` restore into a new volume weekly.
- Evidence: `launch/scripts/volume_health_probe.py` output.

## 4. Telegram outage
- Route inbound alerts to a secondary platform if `getMe` fails for >5 minutes.
- Reference: `launch/e2e-telegram-runtime-manifest.md` fallback behavior.
- Evidence: `launch/scripts/runtime_probe.py` telegram block.

## 5. Railway outage
- Pre-stage Docker image on Docker Hub.
- Maintain `docker-compose.yml` and Railway manifest for manual redeployment.
- Evidence: operator notes and Railway incident reference in `launch/evidence/`.

## 6. Provider outage
- Failover base URL pinned in config.yaml.
- Validate failover weekly by rotating env `HERMES_*_BASE_URL`.
- Evidence: gateway log containing fallback provider + timestamp.

## 7. LLM outage
- All scheduled jobs pin provider/model in cron job metadata.
- On provider error, queue deliverables in Hatchet for retry.
- Evidence: Hatchet worker logs + ACP metering report.

## 8. Network outage
- Hermes handles transient HTTP 5xx/timeouts with retries.
- Document workflows retry off Hatchet queue.
- Evidence: runtime logs + runtime metrics showing retry count.

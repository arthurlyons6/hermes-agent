# Operational Evidence Vault Policy

This directory contains the operational evidence archive for launch milestones.

## Retention rules

- Every evidence file must contain: Git commit SHA, Railway deployment ID, health check result, Promptfoo score, test result, generated PDF path, runtime log path, runtime metrics, rollback package, timestamp, operator, model used.
- Evidence directories are organized under `launch/evidence/vault/<YYYY-MM>/<YYYY-MM-DD>/<event-label>/`.

## Automation expectations

- `launch/scripts/runtime_probe.py` writes per-check evidence files.
- `launch/scripts/rollback_validation.py` writes rollback manifest.
- `launch/scripts/db_backup_restore.py` writes backup manifest.
- CI/mission should tar `launch/evidence/vault` after each milestone and retain in Railway volume or artifact store.

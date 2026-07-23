# ROLLBACK PLAN

For each change phase:
- Backup affected code/config before modification.
- Maintain feature flag or config switch for behavioral guard to disable instantly.
- Preserve prior logging format adapter to avoid breaking log consumers.
- Retain previous request/trace handling path until new path is validated.
- Recovery from bad instrumentation: revert logger format/config only.
- Recovery from bad behavioral guard: disable guard via config and retain original retry path.
- Incident review: if new telemetry creates false positives, refine thresholds rather than removing observability.

EOF
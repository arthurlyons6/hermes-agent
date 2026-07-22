# Production Readiness Review

## Acceptance Gates

| ID | Gate | Evidence Required | Status |
|----|-------|-------------------|--------|
| PR-1 | Railway gateway healthy | `/health` 200 with timestamp | pending |
| PR-2 | Telegram end-to-end delivery | `getMe` + probe message receipt | pending |
| PR-3 | Persistent volume writes and reads persist | `/opt/data` write/read probe | pending |
| PR-4 | PostgreSQL connection succeeds | `SELECT 1` from gateway and worker | pending |
| PR-5 | ACP local metering validates | JSON report from ACP validator | pending |
| PR-6 | Hatchet worker delivers workflow | workflow receipt + ack | pending |
| PR-7 | Docling ingests source materials | ledger entries with checksum match | pending |
| PR-8 | Promptfoo test suite executes | test report JSON | pending |
| PR-9 | Quarto renders branded PDF | PDF exists + visual inspection record | pending |
| PR-10 | Failure/retry/rollback test passes | runtime logs + rollback package | pending |
| PR-11 | Evidence vault archived | vault directory present with all artifacts | pending |
| PR-12 | DR playbook validated | evidence for DB backup, volume recovery, provider failover | pending |

## Operator sign-off

- Operator: ________________
- Timestamp: ________________
- SHA: ________________

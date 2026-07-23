# Railway Release Checklist

Goal: move from local-first to hosted deployment.

## Blocker chain
1. **Security signoff** — Naomi
2. **Data review** — Malcolm
3. **Validation** — Victor

## Artifacts
- Repo: `https://github.com/arthurlyons6/hermes-agent`
- Latest push: `e8f2e52e5` — batch synthetic pack generation, quarantine/approval, tests, docs
- Previous push: `cfc0f832b` — Windows-targeted pytest fixes + telemetry hardening

## Criteria for greenlight
- Naomi confirms no secrets/env leakage in repo and no unverified skill upload paths
- Malcolm confirms synthetic-only data posture; no live confidential/financial/banking/PII ingestion authorized yet
- Victor confirms environment/tests pass for Railway target

## Actions
- [ ] Naomi security signoff
- [ ] Malcolm data review
- [ ] Victor validation
- [ ] Railway config review
- [ ] Final deploy


# Lyons Command Center — Repository Integration Report
Generated: 2026-07-21T18:44:00Z
Reviewer: Marcus
Architecture baseline:
- Core agent runtime: Hermes Agent (Python)
- Production host: Railway container, gateway-mode, Telegram transport
- Local development: Windows 10/11, 8GB Lite
- Data/state: SQLite state.db, filesystem under HERMES_HOME
- Rule: Hermes-first; avoid architectural drift; gate local resource load

---

## 1. hermes-agent
- Repository: https://github.com/arthurlyons6/hermes-agent
- Type: core runtime library / framework
- Language: Python
- Status: active
- Purpose: Canonical Hermes agent core—conversation loop, model tools, gateway runtime, plugin/skill loading, CLI/TUI/Electron surfaces.
- Benefits: Directly improves reliability, gateway behavior, Telegram handling, observability, and platform support.
- Risks: High blast radius if modified incorrectly; prompt caching and role alternation constraints make invasive changes costly.
- Dependencies: Python, venv, optional Node for TUI/website, provider API keys.
- Windows compatibility: compatible
- Railway compatibility: compatible
- Resource requirements: moderate
- Recommended owner: Miles/Naomi
- Integration approach: Adopt as the single source of truth for Hermes runtime. Patch via focused PRs, reuse existing extension points (skills/plugins/hooks/gateway adapters) instead of core duplication.
- Testing plan: Run `scripts/run_tests.sh` subset for changed surfaces; gateway smoke test; Railway health probe; Telegram smoke.
- Rollback plan: revert PR tag or branch reset; restore previous pinned release.
- Final recommendation: Adopt

---

## 2. skills
- Repository: https://github.com/arthurlyons6/skills
- Type: skills collection
- Language: Markdown/Python
- Status: active
- Purpose: Externalized capability vault for Hermes—operational, security, debugging, DevOps, research, and creative skills.
- Benefits: Extends Hermes without growing core surface; governed by registry, duplicate detection, and specialist routing.
- Risks: Skill quality variance; activation can degrade prompt cache or increase token usage if over-activated.
- Dependencies: Hermes skill loader/config
- Windows compatibility: compatible
- Railway compatibility: compatible
- Resource requirements: varies by skill; static validation required before activation
- Recommended owner: Naomi/Miles
- Integration approach: staged activation from skills-registry; only validated priority package skills become active; remainder stay on hold.
- Testing plan: temp HERMES_HOME syntax + dependency + secret scan; controlled functional smoke before activation.
- Rollback plan: remove active skill copies; revert registry entry to activated=false.
- Final recommendation: Adopt (limited, governed activation)

---

## 3. hermes-council
- Repository: https://github.com/arthurlyons6/hermes-council
- Type: plugin/skills collection
- Language: Python
- Status: foundation only
- Purpose: Multi-agent debate plugin foundation for Hermes; structured expert debate rounds with synthesized recommendations.
- Benefits: Adds governed deliberation capability; aligns with Lyons Command Center hierarchy without replacing Marcus/Arthur authority.
- Risks: README explicitly says behavior/routing/storage/inference/tools are not implemented yet; current value is mostly scaffolding.
- Dependencies: Hermes plugin entry points
- Windows compatibility: compatible
- Railway compatibility: compatible
- Resource requirements: low
- Recommended owner: Marcus
- Integration approach: Adopt as foundation only; do not represent as fully functional until behavior, commands, routing, storage, tools, and inference are implemented and validated.
- Testing plan: import plugin entry point in herm Venv; verify register() without side effects; run smoke test against local Hermes session.
- Rollback plan: `pip uninstall hermes-agent-council`; disable plugin entry point.
- Final recommendation: Adopt (foundation only)

---

## 4. hatchet
- Repository: https://github.com/arthurlyons6/hatchet
- Type: workflow orchestration service/framework
- Language: Go
- Status: active
- Purpose: Durable background tasks, AI-agent workflow orchestration, cron/scheduled runs, DAGs, retries, observability; Postgres-backed durability.
- Benefits: Could replace or complement Hermes cron/job needs with stronger durability, retry, monitoring, and webhook-driven execution.
- Risks: Significant new infrastructure; Fly.io/Railway deployment model diverges from current hermetic Docker/s6-overlay pattern; introduces Go runtime, Postgres requirement, and separate service lifecycle.
- Dependencies: Postgres, Go runtime, optional TypeScript/Python/Ruby SDKs
- Windows compatibility: incompatible/native for service runtime; develop on WSL
- Railway compatibility: conditional
- Resource requirements: high
- Recommended owner: Marcus/Olivia
- Integration approach: Stage only; run as a separate bounded service if needed. Reuse Hermes builtin `cronjob` and gateway hooks until Hatchet proves materially better for Railway delivery reliability.
- Testing plan: local Docker Compose; Railway shadow deploy; compare job completion/retry/observability against Hermes cron baseline.
- Rollback plan: remove Hatchet service; revert to Hermes cron.
- Final recommendation: Stage

---

## 5. hermes-acp-plugin
- Repository: https://github.com/arthurlyons6/hermes-acp-plugin
- Type: plugin
- Language: Python
- Status: active
- Purpose: Agentic Control Plane plugin for Hermes—local metering/cost X-ray plus optional cloud governance/audit for tool calls and API spend.
- Benefits: Direct observability and governance uplift for Hermes with minimal core changes; matches Lyons governance doctrine.
- Risks: Cloud plane is optional but introduces external account/dashboard linkage; local DB path must not collide with HERMES_HOME paths; fail-open behavior is critical.
- Dependencies: Hermes plugin system; optional ACP cloud credentials
- Windows compatibility: compatible
- Railway compatibility: compatible
- Resource requirements: low
- Recommended owner: Naomi/Victor
- Integration approach: Adopt as an optional plugin behind explicit opt-in; default to local metering only; cloud login only on manual action.
- Testing plan: install plugin in temp Hermes venv; verify hook registration; ensure fail-open on network timeout/SQLite lock; validate `acp-hermes report` output.
- Rollback plan: disable plugin; remove `~/.acp` credentials; revert plugin install.
- Final recommendation: Adopt (opt-in)

---

## 6. Odysseus
- Repository: https://github.com/arthurlyons6/odysseus
- Type: application/framework
- Language: Python/TypeScript
- Status: dormant/existing
- Purpose: Self-hosted AI workspace with chat, agentic execution, memory/skills, email, calendar, compare, deep research.
- Benefits: Rich UI and broad capabilities; overlaps some Hermes surfaces but offers end-user web workspace experience.
- Risks: License AGPLv3; large surface area; high resource usage; overlaps Hermes memory/skills/web UI; governance entanglement risk if treated as co-equal runtime.
- Dependencies: Python 3.11+, FastAPI/uvicorn, optional Ollama/llama.cpp/vLLM, Chroma/fastembed, Postgres optional, Docker Compose
- Windows compatibility: partial
- Railway compatibility: incompatible as shared runtime
- Resource requirements: very high
- Recommended owner: Miles (if resuming)
- Integration approach: Do not merge into Hermes core. Treat as an optional external workspace deployable only under explicit user request; keep Hermes as command-layer runtime, not dashboard replacement.
- Testing plan: only if reactivation requested: Windows native run, Railway mold excluded, portal/docs review.
- Rollback plan: stop/remove Odysseus service; preserve Hermes core unchanged.
- Final recommendation: Reject from active integration scope

---

## 7. paperclip
- Repository: https://github.com/arthurlyons6/paperclip
- Type: orchestration platform/dashboard
- Language: TypeScript
- Status: active upstream
- Purpose: Multi-agent company/workplace orchestration—goal alignment, org charts, heartbeats, budgets, ticket tracking.
- Benefits: Offers business-governance UI and execution coordination beyond tool calls; can provide dashboard/board layer for multi-agent workforces.
- Risks: Different runtime model from Hermes; parallel process risk; shared state and authority boundaries unclear; higher ops complexity.
- Dependencies: Node.js server, database, agent adapters
- Windows compatibility: compatible
- Railway compatibility: conditional
- Resource requirements: high
- Recommended owner: Marcus
- Integration approach: Stage only; pilot behind explicit governance boundary as optional workforce dashboard, not as Hermes runtime replacement.
- Testing plan: inspect adapter compatibility with Hermes agent events; pilot in staging container; validate audit trail completeness.
- Rollback plan: disable dashboard service; retain Hermes core and Telegram channel.
- Final recommendation: Stage

---

## 8. gci-n8n
- Repository: https://github.com/arthurlyons6/gci-n8n
- Type: workflow automation service
- Language: TypeScript
- Status: upstream n8n fork/manifest
- Purpose: Workflow-based automation with HTTP/webhook/Telegram-capable integrations.
- Benefits: Proven workflow engine; can offload scheduled integration and GCI business workflows from Hermes.
- Risks: Repo size/type indicates manifest/maintenance fork; operational split between platform and core runtime; extra service to monitor.
- Dependencies: Node.js, Postgres, Redis optional
- Windows compatibility: compatible
- Railway compatibility: compatible
- Resource requirements: moderate
- Recommended owner: Olivia/Marcus
- Integration approach: Stage as an integration bus for GCI/non-agent workflow paths; keep Hermes as reasoning/routing core.
- Testing plan: Railway deploy shadow service; validate webhook round-trip; compare with Hermes cron for lightweight jobs.
- Rollback plan: remove service; validate Hermes-native cron fallback.
- Final recommendation: Stage

---

## 9. gci-dify
- Repository: https://github.com/arthurlyons6/gci-dify
- Type: application/framework
- Language: TypeScript
- Status: upstream Dify fork
- Purpose: LLM app/RAG/workflow builder for customer-facing assistants and data pipelines.
- Benefits: Strong RAG/assistant builder for GCI-facing channels; complements Hermes reasoning with dedicated assistant surfaces.
- Risks: Duplicates Hermes AI surface if not scoped; adds heavy frontend/backend stack; requires extra observability and auth integration.
- Dependencies: Node.js, Postgres, Redis, S3/minio optional, LLM provider keys
- Windows compatibility: compatible
- Railway compatibility: compatible
- Resource requirements: high
- Recommended owner: Julian/Grace
- Integration approach: Stage as a bounded customer/branch assistant platform; do not route core Hermes/Telegram traffic through it.
- Testing plan: Railway shadow deploy; auth flow against Hermes identity if shared; content-moderation/e2e smoke.
- Rollback plan: drain traffic; archive tenant state; revert Railway service.
- Final recommendation: Stage

---

## 10. gci-appsmith
- Repository: https://github.com/arthurlyons6/gci-appsmith
- Type: dashboard/internal tools
- Language: TypeScript
- Status: upstream Appsmith fork
- Purpose: Low-code internal app builder for dashboards and operational tools.
- Benefits: Fastest path to operational dashboards for GCI/internal users without writing frontends.
- Risks: Maintained fork of large TS repo; security patches and packaging effort are nontrivial.
- Dependencies: Node.js, Postgres, Redis
- Windows compatibility: compatible
- Railway compatibility: compatible
- Resource requirements: moderate-high
- Recommended owner: Sophia/Olivia
- Integration approach: Stage; use only where frontend-dev bandwidth is the blocker and Hermes JSON/TUI dashboards are not enough.
- Testing plan: Railway deploy; auth/permission smoke; data-source connectivity.
- Rollback plan: disable service or route to Hermes JSON endpoints.
- Final recommendation: Stage

---

## 11. gci-nocodb
- Repository: https://github.com/arthurlyons6/gci-nocodb
- Type: data/application platform
- Language: TypeScript
- Status: upstream NocoDB fork
- Purpose: Open-source Airtable-like data layer for business records and workflows.
- Benefits: Provides structured data surface for business pipelines, forms, and CRUD without bespoke admin UI.
- Risks: Adds persistence/auth model; can duplicate existing Postgres or state.db usage if carelessly adopted as source of truth.
- Dependencies: Node.js, Postgres
- Windows compatibility: compatible
- Railway compatibility: compatible
- Resource requirements: moderate-high
- Recommended owner: Malcolm/Olivia
- Integration approach: Stage; use as a presentation layer over approved data stores, not as canonical Hermes state storage.
- Testing plan: deploy against Railway Postgres; verify backup/restore; test row-level access.
- Rollback plan: export CSVs/JSON; disable service; restore canonical store.
- Final recommendation: Stage

---

## 12. gci-windmill
- Repository: https://github.com/arthurlyons6/gci-windmill
- Type: workflow/automation service
- Language: Rust
- Status: upstream Windmill fork
- Purpose: Script/flow/job execution platform with multi-language workers and webhook trigger model.
- Benefits: Strong execution/durability model with Rust runtime; useful for secure/sensitive script execution if Go/Python exec in Hermes is insufficient.
- Risks: Rust runtime adds operational complexity; niche compared to Hatchet/n8n; higher Windows maintenance burden.
- Dependencies: Rust, Postgres, SSO/worker runtime
- Windows compatibility: compatible
- Railway compatibility: compatible
- Resource requirements: moderate-high
- Recommended owner: Marcus/Olivia
- Integration approach: Stage as an alternate executor/automation backend only; compare with n8n and Hatchet on maintenance cost.
- Testing plan: Railway shadow; job success rate/latency; compare restart recovery.
- Rollback plan: remove worker; failover to Hermes cron/n8n.
- Final recommendation: Stage

---

## 13. BlackGold Equity Partners public site
- Repository: https://github.com/arthurlyons6/blackgold-equity-partners
- Type: website/dashboard
- Language: HTML
- Status: active
- Purpose: Public brand site for BlackGold Equity Partners.
- Benefits: Governed public presence for principal brand; lightweight.
- Risks: None for core AI platform; site hygiene/secrets scanning still required.
- Dependencies: hosting platform
- Windows compatibility: compatible
- Railway compatibility: compatible
- Resource requirements: low
- Recommended owner: Sophia
- Integration approach: Adopt as a standalone external site; do not embed into Hermes runtime.
- Testing plan: lint/HTML validation; secrets scan; domain/SSL check.
- Rollback plan: revert deploy commit; preserve DNS/hosting config.
- Final recommendation: Adopt (external)

---

## 14. peg-fullstack-app
- Repository: https://github.com/arthurlyons6/peg-fullstack-app
- Type: application
- Status: archived, private
- Purpose: prior private fullstack app scaffold
- Benefits: unknown
- Risks: private archive; unclear contents; no architectural necessity; duplicate of newer app platforms.
- Dependencies: unknown
- Windows compatibility: unknown
- Railway compatibility: unknown
- Resource requirements: unknown
- Recommended owner: n/a
- Integration approach: Reject unless Arthur explicitly requests de-archiving and migration.
- Testing plan: none
- Rollback plan: none
- Final recommendation: Reject

---

## 15. hermes-agent-railway
- Repository: https://github.com/arthurlyons6/hermes-agent-railway
- Type: manifest/deployment
- Status: archived
- Purpose: one-click Railway deploy manifest for Hermes Agent (historical).
- Benefits: historical reference for Railway deploy shape; not needed if canonical repo already includes deploy config.
- Risks: archived; stale bootstrap assumptions; duplicated with current Dockerfile/run scripts.
- Dependencies: Railway
- Windows compatibility: n/a
- Railway compatibility: historical only
- Resource requirements: low
- Recommended owner: Marcus/Olivia
- Integration approach: Reject; use canonical repo deploy artifacts instead.
- Testing plan: none
- Rollback plan: none
- Final recommendation: Reject

---

## 16. nexabaas-platform
- Repository: https://github.com/arthurlyons6/nexabaas-platform
- Type: service/platform
- Language: JavaScript/TypeScript
- Status: active
- Purpose: Banking-as-a-service platform for accounts/cards/ACH/wire/AML/webhooks.
- Benefits: Matches stated banking/GCI business domain; potential integration point for Julian if operational account rails are needed.
- Risks: Private repo; large/complex surface; PCI/financial compliance sensitivity; high operational burden; does not improve Hermes core.
- Dependencies: database, payment rails, compliance tooling
- Windows compatibility: unknown
- Railway compatibility: conditional
- Resource requirements: high
- Recommended owner: Julian
- Integration approach: Reject from Hermes/Lyons core for now; treat as Julian-owned domain platform with isolated governance.
- Testing plan: only if Julian requests: compliance review, deploy audit.
- Rollback plan: cut API/webhook dependency; revert to manual/Simplified flow.
- Final recommendation: Reject from core integration scope

---

## Summary recommendations
- Adopt: hermes-agent, skills (governed), hermes-council (foundation), hermes-acp-plugin (opt-in), BlackGold site (external)
- Stage: hatchet, paperclip, gci-n8n, gci-dify, gci-appsmith, gci-nocodb, gci-windmill
- Reject: Odysseus from integration scope, peg-fullstack-app, hermes-agent-railway, nexabaas-platform from core scope

---
End of Integration Report

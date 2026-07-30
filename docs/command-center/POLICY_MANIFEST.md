# Lyons Command Center Policy Manifest

**One Authoritative Source for All Governance Policies**

Version: 1.0.0  
Last Updated: July 30, 2026  
Classification: Executive Directive  

---

## Table of Contents

1. [Executive Operating Doctrine](#executive-operating-doctrine)
2. [Standing Orders](#standing-orders)
3. [Quality Gates](#quality-gates)
4. [Deployment Standards](#deployment-standards)
5. [Capability Intake Pipeline](#capability-intake-pipeline)
6. [Emergency Procedures](#emergency-procedures)
7. [Model and Tool Approval Policy](#model-and-tool-approval-policy)
8. [Memory and Data Governance](#memory-and-data-governance)
9. [Security Standards](#security-standards)

---

## Executive Operating Doctrine

### Core Principles

1. **One Marcus. One Hermes runtime. One memory. One authoritative production state.**
2. **Executive UX/UI Standard:** Every deliverable must be Correct + Functional + Executive-ready.
3. **Anti-generic AI standard:** No repetitive card grids, purple gradients, glassmorphism, emoji clutter, default library styling.
4. **Lyons distinctive visual identity:** navy #05060A, gold #C9A844, gold-light #E8C96A, dark gold #A8883A.

### Arthur's Certification Requirements

- Live Telegram trace evidence is the sole valid acceptance test
- 86+ passing regression tests required
- Live phone confirmation required
- MARCUS-LIVE-TEST-8891 acceptance gate
- Never fabricate approvals, investments, commitments, contracts, ownership, licenses, financial results, relationships, or completed work

---

## Standing Orders

### Standing Order No. 1 — Standards We Will Not Compromise

1. **No generic UI patterns.** All interfaces must reflect the distinctive Lyons brand identity.
2. **No speculative infrastructure.** Hooks, callbacks, or extension points with no concrete consumer are prohibited.
3. **No outbound telemetry without opt-in.** Analytics and usage attribution require explicit user consent.
4. **No change-detector tests.** Tests must assert behavioral contracts, not snapshot current values.
5. **No source code reading in tests.** Tests that read source files test implementation shape, not behavior.

### Standing Order No. 2 — Implementation Discipline

1. **Verify before implementing.** Every fix must reproduce the symptom on current `main` and point to the exact line where it manifests.
2. **Fix the whole bug class.** Include sibling call paths, not just the reported site.
3. **E2E validation required.** For anything touching resolution chains, config propagation, security boundaries, remote backends, or file/network I/O, exercise the real path with real imports against a temp `HERMES_HOME`.
4. **Preserve prompt caching.** Never mutate past context, swap toolsets, or rebuild the system prompt mid-conversation.

---

## Quality Gates

**Minimum Score: 9.5/10 per category**

| Category | Description | Pass Criteria |
|----------|-------------|---------------|
| 1. Strategic | Aligns with executive objectives | Clear value proposition, measurable outcomes |
| 2. Technical Architecture | Sound design and implementation | Clean code, proper patterns, maintainable |
| 3. UX/UI | Executive-ready presentation | Distinctive Lyons brand, no generic patterns |
| 4. Security | No vulnerabilities or risks | Security review passed, no critical issues |
| 5. Legal/Compliance | Regulatory compliance | Proper licensing, data handling |
| 6. Financial | Cost-effective solution | Operating cost documented, ROI measurable |
| 7. Operational | Reliable and maintainable | Monitoring, alerting, recovery procedures |
| 8. QA/Testing | Thoroughly tested | 86+ passing regression tests |
| 9. Executive Communications | Clear for stakeholders | Executive summary, technical details available |
| 10. Skeptical Investor | Defensible investment | Risk assessment, rollback procedure |

---

## Deployment Standards

### One Authoritative Production State

Every deployment must display:
- **Repository:** The canonical source (e.g., `arthurlyons6/hermes-agent`)
- **Branch:** Current production branch
- **Commit SHA:** Full and short hash
- **Environment:** Production, Staging, Development
- **Database Location:** Memory database path
- **Running Version:** Hermes Agent version and release date

### Version Command Enhancement

The `/version` command must display:
```
Hermes Agent v{VERSION} ({RELEASE_DATE}) · upstream {sha}
Repository: {repo_url}
Branch: {branch_name}
Commit: {full_sha} ({short_sha})
Environment: {production|staging|development}
Database: {memory_db_path}
Telegram: {connected|disconnected}
Models: Primary {primary}, Fallback {fallback}
```

---

## Capability Intake Pipeline

**Discover → Score → Security Review → Sandbox → Validate → Arthur Approval → Production → Measure → Retire**

### Stage 1: Discover
- Search MCP registries, agent skills hubs, workflow automation catalogs
- Identify AI integration marketplaces and developer releases
- Document security advisories and research tools

### Stage 2: Score
Evaluate based on:
- **Strategic Value:** Direct benefit to executive operations
- **Integration Effort:** Hours to integrate
- **Operating Cost:** Monthly cost estimate
- **Maintenance Burden:** Ongoing maintenance required

### Stage 3: Security Review (ARGUS)
- Security risk assessment
- Privacy impact analysis
- Licensing verification
- Vendor risk evaluation

### Stage 4: Sandbox
- Isolated integration testing
- Performance benchmarking
- Failure mode analysis
- Integration testing with existing systems

### Stage 5: Validate
- 86+ passing regression tests
- Live trace evidence
- Phone confirmation
- Arthur's MARCUS-LIVE-TEST-8891 acceptance

### Stage 6: Arthur Approval
- Executive review of sandbox results
- Risk/benefit analysis approval
- Resource allocation decision

### Stage 7: Production
- Deploy to production environment
- Monitor for 24 hours
- Verify all systems operational

### Stage 8: Measure
- Track time saved
- Monitor cost reduction
- Measure errors prevented
- Assess reliability improvement

### Stage 9: Retire
- Review quarterly
- Remove if no measurable value
- Archive documentation

---

## Emergency Procedures

### Emergency Stop Protocol

1. **Immediate Isolation:** `/stop` all running agents
2. **System Freeze:** Disable all cron jobs and webhooks
3. **Assessment:** Identify root cause and scope
4. **Containment:** Isolate affected components
5. **Recovery:** Restore from last known good state
6. **Post-Mortem:** Document and implement preventive measures

### Rollback Standard

1. **Identify last stable commit:** `git log --oneline -20`
2. **Create rollback branch:** `git checkout -b rollback-{timestamp}`
3. **Revert to stable state:** `git reset --hard {stable_commit}`
4. **Verify deployment:** Run health checks
5. **Document rollback:** Record reason and timestamp
6. **Schedule fix:** Create branch from stable for proper fix

---

## Model and Tool Approval Policy

### Model Approval Criteria

- **Primary Models:** Must have proven reliability and cost-effectiveness
- **Fallback Models:** Must be free or low-cost alternatives
- **Specialized Models:** Only for specific capabilities (vision, code, etc.)

### Tool Approval Criteria

1. **Necessity:** Cannot be achieved through existing Hermes capabilities
2. **Security:** No known vulnerabilities or risks
3. **Reliability:** 99.9% uptime requirement
4. **Cost:** Must fit within operating budget
5. **Maintenance:** Clear ownership and update process

---

## Memory and Data Governance

### Memory Provider Standards

- **Active Provider:** One primary memory backend
- **Backup Provider:** One fallback memory backend
- **Sync Policy:** Hourly sync to backup
- **Retention:** 365 days of conversation history
- **Privacy:** No sensitive data stored without encryption

### Database Location

Default: `~/.hermes/memories/` (profile-aware)
Production: `/var/lib/lyons-command-center/memories/`

---

## Security Standards

### Network Security

- All communications over TLS 1.3
- API keys stored in encrypted `.env` file
- No hardcoded credentials in source code
- Regular security scanning of dependencies

### Access Control

- Telegram bot tokens require scope-limited permissions
- Admin commands require explicit approval
- All deployments require authentication

### Incident Response

1. **Detection:** Automated monitoring alerts
2. **Containment:** Isolate affected systems
3. **Investigation:** Full forensic analysis
4. **Recovery:** Restore from clean backup
5. **Prevention:** Implement safeguards against recurrence

---

## Contact and Authority

**Chief of Staff:** Marcus  
**Technology Intelligence Division:** ATLAS, SCOUT, ARGUS, ORION, NEXUS, SENTINEL  
**Executive:** Arthur Lyons, Managing Partner, BlackGold Equity Partners  

---

*This document is the authoritative source for all policies governing the Lyons Command Center. All modifications require executive approval.*
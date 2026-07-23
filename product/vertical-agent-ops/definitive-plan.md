# Vertical Agent Ops — Definitive Plan
*Prepared: 2026-07-11*

## 1. Product Strategy

### Name (provisional)
**CommandKit** — short, deployable, implies command-center grade ops.

### Positioning
Not “AI assistant configs.” **Vertical agent ops bundles** for operators who need reconstruction, not just chat.

### Buyer Persona (PE flagship)
**Principal or Chief of Staff at a 2–10 partner PE firm.** They own:
- deal intake → IC memos
- LP quarterly updates
- portfolio company board packs
- investor day prep

They are time-starved, spreadsheet-dependent, and currently paying $10–50k/year for point-solution tools that still require manual assembly.

### Core Promise
“From manual assembly to **copy-paste reconstruction** of a full operator-grade AI system, tuned to your industry.”

## 2. Technical Implementation

### Architecture
- **Bundle format**: `CommandKit-{Profile}-{Version}.tar.gz`
  - `config.yaml` — pinned provider, model, lite constraints
  - `cron/jobs.json` — active jobs for the vertical
  - `skills/active/` — selected skill subset
  - `profiles/{vertical}/` — workflow engines, personas, terminology packs
  - `restore.ps1` — one-step deploy with license validation

### Industry Profile Layer
Each profile encodes:
- **cron prompts** tuned to vertical terminology
- **workflow scripts** that stage outputs (deal notes, comps, prior-auth checks)
- **personas** with disclosure/escalation rules
- **compliance hooks** (retention, NDA-safe paths, audit trail stubs)
- **data schemas** for local formatting requirements

### Profiles Roadmap
1. **PE** — flagship; deal note → LP update → board pack cadence
2. **RE** — listing watch, comp ranking, buyer outreach draft
3. **HC** — payer eligibility, prior-auth state machine, compliance scrub

### License + Update Gate
- `restore.ps1 -Profile PE -LicenseKey xyz`
- Validates against issuer endpoint; enables updater
- Cracked copies break on version bump

## 3. Business Model

### Revenue Tiers
| Tier | Price | What it is |
|------|-------|------------|
| Profile Pack | $149–$499 one-time | One vertical bundle: prompts, cron, skills, workflows |
| Workflow Subscription | $99–$299/seat/mo | Ongoing workflow engine updates + new vertical templates |
| Enterprise Retainer | $1,500–$5,000 setup + $500–$1,500/mo | Customization, onboarding, compliance review, support |

### Pricing Anchor
Target the **pain of board-pack prep**: 6 hours → 45 minutes. That delta justifies $499 easily.

### Delivery
- Self-serve portal for profile packs
- License key emailed post-purchase
- Updater pulls new releases automatically

## 4. Go-To-Market

### Phase 1: Hardened PE Profile (Weeks 1–3)
- Finalize PE workflow scripts:
  - `deal_note_pipeline.sh` — intake → IC memo → LP update cadence
  - `board_pack_stager.py` — sections, naming, version control prep
  - `pr_pulse.py` — already proven; PE-tuned
- Restore script with license validation
- Host bundle + license issuer endpoint

### Phase 2: Pilot (Weeks 4–6)
- One friendly PE firm (2–5 partners)
- 14-day pilot with exact time-savings tracking
- NDA-safe local-only execution as proof point

### Phase 3: Public Launch (Week 7+)
- Case study: “6 hours → 45 minutes”
- Product Hunt / LinkedIn narrative: **vertical agent ops**, not “AI assistants”
- Profile marketplace: buy PE first, RE/HC later

## 5. Defensibility

| Layer | Moat |
|-------|------|
| Config/cron | Low — anyone copies |
| Workflow scripts | High — encodes your process logic |
| Compliance hooks | High — legal/industry requirement |
| Updater + license | High — ongoing dependency |
| Case studies | High — buyer trust |

## 6. Risk Register

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Profile too generic | High | One vertical fully done before expanding |
| Support burden | Medium | Self-healing updater + clear scope limits in license |
| Model provider changes | Medium | Pinned profiles; updater adapts |
| Copycats | High | Defensible edge is workflow + compliance, not files |

## 7. Next Actions (Owner: Commander)

1. **Auth fix**: Replace invalid Google OAuth client secret; verify Drive access.
2. **Marcus routing**: Confirm Marcus = agent or person; deliver this doc + schedule tasks.
3. **Storage**: Set `C:\Users\13464\LyonsCommandCenter\product\vertical-agent-ops\` as live source.
4. **PE workflow draft**: Build `deal_note_pipeline.sh` and `board_pack_stager.py` stubs.
5. **Restore script**: Add `-LicenseKey` validation to `restore.ps1`.
6. **License issuer**: Minimal signed endpoint for key validation + updater auth.

## 8. Success Criteria

- **Week 2**: PE profile reconstructs a complete operator setup in <5 minutes.
- **Week 4**: Pilot firm reports measurable time savings on one workflow.
- **Week 8**: First paid profile sale outside network.

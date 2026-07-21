# Launch Stabilization — Artifact Index

Last updated: 2026-07-21

This directory contains the concrete implementation artifacts for launch stabilization, document production, evidence governance, quality testing, and Quarto rendering.

## Manifest and ownership

- `rails-stabilization-manifest.md` — numbered launch implementation order and acceptance criteria
- `stack-diagram.md` — approved Docling → Hermes Workforce → Promptfoo → Quarto stack diagram
- `hatchet-deploy-spec.md` — Hatchet Railway worker deployment specification
- `acp-local-metering-plan.md` — ACP local metering validation plan
- `persistent-volume-and-postgres-runtime-manifest.md` — Railway volume and Postgres runtime expectations
- `e2e-telegram-runtime-manifest.md` — Telegram inbound/outbound runtime acceptance test

## Document production

- `document_worker_base.py` — stage-one document worker base wiring
- `evidence_ledger.py` — evidence ledger data model with `EvidenceEntry` and `EvidenceLedger`
- `document_workflow.py` — institutional document workflow with outline, assignment, review, ledger, evaluation, and package export
- `offboarding_plan.py` — financial plan scenario and acceptance gate definitions
- `promptfoo.black-gold.yaml` — Promptfoo regression tests for factual, financial, legal, editorial, structural, citation, and confidentiality gates
- `quarto.templates.yaml` — Quarto template manifest for Black Gold branded document
- `templates/quarto/black-gold/business-plan.qmd` — Quarto template stub with evidence-ledger table and confidentiality notice
- `templates/quarto/black-gold/business-plan-stub.qmd` — alternate Quarto LaTeX-styled template stub

## Receiving repos

The following repositories are acknowledged in the launch stack but are **not** copied into this codebase:
- `docling-project/docling`
- `promptfoo/promptfoo`
- `quarto-dev/quarto-cli`

They are linked via the execution plan above and will be installed and validated in-place on Railway or local worker hosts.
